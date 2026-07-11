import argparse
from decimal import Decimal

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F

REQUIRED_TRADE_COLUMNS = {
    "trade_id",
    "client_id",
    "product_code",
    "client_type",
    "quantity",
    "price",
    "currency",
    "exchange",
    "trade_side",
    "trade_date",
}


def main() -> None:
    args = parse_args()
    spark = (
        SparkSession.builder.appName("ebcms-batch-brokerage")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )

    trades = spark.read.option("header", True).csv(args.trades_csv)
    rules = spark.read.option("header", True).csv(args.rules_csv)
    validated = validate_columns(trades, REQUIRED_TRADE_COLUMNS)
    calculated = calculate_brokerage(validated, rules)

    calculated.write.mode("overwrite").parquet(args.output_path)
    spark.stop()


def validate_columns(df: DataFrame, required_columns: set[str]) -> DataFrame:
    missing = required_columns.difference(set(df.columns))
    if missing:
        raise ValueError(f"Missing required trade columns: {sorted(missing)}")

    return (
        df.withColumn("quantity", F.col("quantity").cast("decimal(20,4)"))
        .withColumn("price", F.col("price").cast("decimal(20,6)"))
        .withColumn("trade_date", F.to_date("trade_date"))
        .withColumn(
            "validation_error",
            F.when(F.col("quantity") <= 0, F.lit("Invalid quantity"))
            .when(F.col("price") <= 0, F.lit("Invalid price"))
            .otherwise(F.lit(None)),
        )
    )


def calculate_brokerage(trades: DataFrame, rules: DataFrame) -> DataFrame:
    normalized_rules = (
        rules.withColumn("brokerage_value", F.col("brokerage_value").cast("decimal(20,6)"))
        .withColumn("effective_date", F.to_date("effective_date"))
        .withColumn("expiry_date", F.to_date("expiry_date"))
    )

    joined = trades.join(
        normalized_rules,
        on=[
            trades.product_code == normalized_rules.product_code,
            trades.client_type == normalized_rules.client_type,
            trades.exchange == normalized_rules.exchange,
            trades.currency == normalized_rules.currency,
            trades.trade_date >= normalized_rules.effective_date,
            (
                normalized_rules.expiry_date.isNull()
                | (trades.trade_date <= normalized_rules.expiry_date)
            ),
        ],
        how="left",
    )

    trade_value = F.col("quantity") * F.col("price")
    brokerage = F.when(
        F.upper(F.col("brokerage_type")) == F.lit("PERCENTAGE"),
        trade_value * (F.col("brokerage_value") / Decimal("100")),
    ).when(
        F.upper(F.col("brokerage_type")) == F.lit("FLAT"),
        F.col("brokerage_value"),
    )

    return (
        joined.withColumn("trade_value", F.round(trade_value, 2))
        .withColumn("brokerage", F.round(brokerage, 2))
        .withColumn("gst", F.round(F.col("brokerage") * Decimal("0.18"), 2))
        .withColumn("stt", F.round(F.col("trade_value") * Decimal("0.00025"), 2))
        .withColumn("exchange_txn_charge", F.round(F.col("trade_value") * Decimal("0.0000325"), 2))
        .withColumn("sebi_charge", F.round(F.col("trade_value") * Decimal("0.000001"), 2))
        .withColumn(
            "total_charges",
            F.round(
                F.col("brokerage")
                + F.col("gst")
                + F.col("stt")
                + F.col("exchange_txn_charge")
                + F.col("sebi_charge"),
                2,
            ),
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run EBCMS batch brokerage calculations.")
    parser.add_argument("--trades-csv", required=True)
    parser.add_argument("--rules-csv", required=True)
    parser.add_argument("--output-path", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    main()

