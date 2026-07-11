import json

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ebcms.api.dependencies import require_roles
from ebcms.config import get_settings
from ebcms.core.enums import TradeStatus, UserRole
from ebcms.database import get_db
from ebcms.models import AuditLog, BrokerageResult, Client, Product, Trade, TradeImportReject, User
from ebcms.schemas import (
    BatchCalculationFailureRead,
    BatchCalculationRequest,
    BatchCalculationSummary,
    BrokerageRead,
    CalculationRequest,
    TradeCreate,
    TradeImportRejectionRead,
    TradeImportSummary,
    TradeRead,
)
from ebcms.services.calculation import (
    CalculationError,
    calculate_trade_brokerage,
    calculate_validated_trades,
    select_validated_trades_for_batch,
)
from ebcms.services.validation import validate_trade_record
from ebcms.services.trade_import import TradeImportError, import_trade_file

router = APIRouter(tags=["trades and calculations"])

TRADE_READ_ROLES = {
    UserRole.ADMIN.value,
    UserRole.OPERATIONS.value,
    UserRole.BROKERAGE_MANAGER.value,
    UserRole.FINANCE.value,
    UserRole.RISK.value,
    UserRole.COMPLIANCE.value,
    UserRole.RELATIONSHIP_MANAGER.value,
}

TRADE_WRITE_ROLES = {
    UserRole.ADMIN.value,
    UserRole.OPERATIONS.value,
}

CALCULATION_ROLES = {
    UserRole.ADMIN.value,
    UserRole.OPERATIONS.value,
    UserRole.BROKERAGE_MANAGER.value,
}


@router.post("/trade", response_model=TradeRead, status_code=status.HTTP_201_CREATED)
def create_trade(
    payload: TradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*TRADE_WRITE_ROLES)),
) -> Trade:
    if db.get(Trade, payload.trade_id):
        raise HTTPException(status_code=409, detail="Duplicate trade ID.")

    client = db.get(Client, payload.client_id)
    product = db.get(Product, payload.product_id)
    settings = get_settings()
    validation = validate_trade_record(
        trade_id=payload.trade_id,
        client_exists=bool(client and client.is_active),
        product_exists=bool(product and product.is_active),
        duplicate_trade_id=False,
        quantity=payload.quantity,
        price=payload.price,
        currency=payload.currency,
        trade_side=str(payload.trade_side),
        trade_date=payload.trade_date,
        allowed_currencies=settings.currency_set,
    )

    trade = Trade(
        **payload.model_dump(exclude={"trade_side", "currency", "exchange"}),
        trade_side=str(payload.trade_side).upper(),
        currency=payload.currency.upper(),
        exchange=payload.exchange.upper(),
        status=TradeStatus.VALIDATED.value if validation.is_valid else TradeStatus.REJECTED.value,
        rejection_reason="; ".join(validation.issues) if validation.issues else None,
    )
    db.add(trade)
    db.add(
        AuditLog(
            entity_type="TRADE",
            entity_id=trade.trade_id,
            action="CREATE",
            new_value=f"status={trade.status}",
            user_id=current_user.username,
            change_reason=trade.rejection_reason,
        )
    )
    db.commit()
    db.refresh(trade)
    return trade


@router.get("/trade/{trade_id}", response_model=TradeRead)
def get_trade(
    trade_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*TRADE_READ_ROLES)),
) -> Trade:
    trade = db.get(Trade, trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found.")
    return trade


@router.post("/trades/import", response_model=TradeImportSummary, status_code=status.HTTP_201_CREATED)
async def import_trades(
    file: UploadFile = File(...),
    imported_by: str | None = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*TRADE_WRITE_ROLES)),
) -> TradeImportSummary:
    filename = file.filename or "uploaded-trades"
    try:
        content = await file.read()
        return import_trade_file(
            filename=filename,
            content=content,
            imported_by=imported_by or current_user.username,
            db=db,
        )
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV file must be UTF-8 encoded.") from exc
    except TradeImportError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/trades/imports/{import_id}/rejections", response_model=list[TradeImportRejectionRead])
def get_trade_import_rejections(
    import_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN.value, UserRole.OPERATIONS.value)),
) -> list[TradeImportRejectionRead]:
    rejections = list(
        db.scalars(
            select(TradeImportReject)
            .where(TradeImportReject.import_id == import_id)
            .order_by(TradeImportReject.row_number, TradeImportReject.rejection_id)
        )
    )
    return [
        TradeImportRejectionRead(
            rejection_id=rejection.rejection_id,
            import_id=rejection.import_id,
            row_number=rejection.row_number,
            trade_id=rejection.trade_id,
            reason=rejection.reason,
            raw_payload=json.loads(rejection.raw_payload),
            created_at=rejection.created_at,
        )
        for rejection in rejections
    ]


@router.post("/calculate", response_model=BrokerageRead)
def calculate_trade(
    payload: CalculationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CALCULATION_ROLES)),
) -> BrokerageResult:
    trade = db.get(Trade, payload.trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found.")

    try:
        return calculate_trade_brokerage(trade=trade, calculated_by=payload.calculated_by, db=db)
    except CalculationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc



@router.post("/calculations/batch", response_model=BatchCalculationSummary)
def calculate_batch(
    payload: BatchCalculationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*CALCULATION_ROLES)),
) -> BatchCalculationSummary:
    if payload.date_from and payload.date_to and payload.date_from > payload.date_to:
        raise HTTPException(status_code=400, detail="date_from cannot be after date_to.")
    if (
        payload.import_id is None
        and payload.date_from is None
        and payload.date_to is None
        and not payload.calculate_all_validated
    ):
        raise HTTPException(
            status_code=400,
            detail="Provide import_id, a date range, or calculate_all_validated=true.",
        )

    trades = select_validated_trades_for_batch(
        db=db,
        import_id=payload.import_id,
        date_from=payload.date_from,
        date_to=payload.date_to,
        calculate_all_validated=payload.calculate_all_validated,
    )
    result = calculate_validated_trades(
        trades=trades,
        calculated_by=payload.calculated_by,
        db=db,
    )
    return BatchCalculationSummary(
        total_trades=result.total_trades,
        calculated_count=len(result.calculated_trade_ids),
        failed_count=len(result.failures),
        total_brokerage=result.total_brokerage,
        total_charges=result.total_charges,
        calculated_trade_ids=result.calculated_trade_ids,
        failures=[
            BatchCalculationFailureRead(trade_id=failure.trade_id, reason=failure.reason)
            for failure in result.failures
        ],
    )


@router.get("/brokerage/{trade_id}", response_model=BrokerageRead)
def get_latest_brokerage(
    trade_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*TRADE_READ_ROLES)),
) -> BrokerageResult:
    result = db.scalar(
        select(BrokerageResult)
        .where(BrokerageResult.trade_id == trade_id)
        .order_by(desc(BrokerageResult.calculated_at), desc(BrokerageResult.result_id))
    )
    if not result:
        raise HTTPException(status_code=404, detail="Brokerage result not found.")
    return result
