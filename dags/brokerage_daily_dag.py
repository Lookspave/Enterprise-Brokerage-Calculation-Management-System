from __future__ import annotations

from datetime import datetime

from airflow.decorators import dag, task


@dag(
    dag_id="ebcms_daily_brokerage",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["brokerage", "etl", "finance"],
)
def daily_brokerage() -> None:
    @task
    def load_trades() -> str:
        return "loaded"

    @task
    def run_validation(previous_state: str) -> str:
        return f"{previous_state}:validated"

    @task
    def run_brokerage(previous_state: str) -> str:
        return f"{previous_state}:calculated"

    @task
    def generate_reports(previous_state: str) -> str:
        return f"{previous_state}:reported"

    @task
    def notify_users(previous_state: str) -> None:
        print(f"Daily brokerage pipeline complete: {previous_state}")

    notify_users(generate_reports(run_brokerage(run_validation(load_trades()))))


daily_brokerage()

