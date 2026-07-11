from decimal import Decimal
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Enterprise Brokerage Calculation & Management System"
    database_url: str = "sqlite:///./ebcms.db"
    allowed_currencies: str = "INR,USD,EUR,GBP"
    default_gst_rate: Decimal = Decimal("0.18")
    default_stt_rate: Decimal = Decimal("0.00025")
    default_exchange_txn_rate: Decimal = Decimal("0.0000325")
    default_sebi_rate: Decimal = Decimal("0.000001")
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_prefix="EBCMS_", env_file=".env", extra="ignore")

    @property
    def currency_set(self) -> set[str]:
        return {currency.strip().upper() for currency in self.allowed_currencies.split(",")}


@lru_cache
def get_settings() -> Settings:
    return Settings()

