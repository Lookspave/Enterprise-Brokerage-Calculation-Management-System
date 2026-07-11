from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ebcms.database import get_db
from ebcms.models import Client, Product
from ebcms.schemas import ClientCreate, ClientRead, ProductCreate, ProductRead

router = APIRouter(tags=["reference data"])


@router.post("/client", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(payload: ClientCreate, db: Session = Depends(get_db)) -> Client:
    if db.get(Client, payload.client_id):
        raise HTTPException(status_code=409, detail="Client already exists.")
    client = Client(**payload.model_dump())
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/client/{client_id}", response_model=ClientRead)
def get_client(client_id: str, db: Session = Depends(get_db)) -> Client:
    client = db.get(Client, client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found.")
    return client


@router.post("/product", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> Product:
    if db.get(Product, payload.product_id):
        raise HTTPException(status_code=409, detail="Product already exists.")
    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get("/product/{product_id}", response_model=ProductRead)
def get_product(product_id: str, db: Session = Depends(get_db)) -> Product:
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found.")
    return product

