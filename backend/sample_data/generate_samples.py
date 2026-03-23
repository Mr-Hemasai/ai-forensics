from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
import random

import pandas as pd


OUTPUT_DIR = Path(__file__).resolve().parent
random.seed(42)

PHONE_NUMBERS = [f"98{random.randint(10000000, 99999999)}" for _ in range(15)]
IPS = [f"10.0.0.{i}" for i in range(2, 18)]
TOWERS = [f"TWR-{100+i}" for i in range(12)]
IMSI_LIST = [f"40410{random.randint(1000000000, 9999999999)}" for _ in range(12)]


def random_time(offset_days: int = 0, bias_night: bool = False) -> datetime:
    base = datetime(2025, 8, 1) + timedelta(days=offset_days)
    hour = random.choice([0, 1, 2, 3, 4, 22, 23]) if bias_night and random.random() > 0.5 else random.randint(6, 21)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return base.replace(hour=hour, minute=minute, second=second)


def build_cdr() -> pd.DataFrame:
    rows = []
    suspect = PHONE_NUMBERS[0]
    for idx in range(60):
        caller = suspect if idx % 4 == 0 else random.choice(PHONE_NUMBERS)
        receiver = PHONE_NUMBERS[1] if idx % 5 == 0 else random.choice(PHONE_NUMBERS)
        rows.append(
            {
                "caller_number": caller,
                "receiver_number": receiver,
                "call_start_time": random_time(idx % 7, bias_night=idx % 3 == 0),
                "duration_seconds": random.randint(15, 900),
                "tower_id": random.choice(TOWERS),
                "imei": f"3569{random.randint(1000000000, 9999999999)}",
            }
        )
    return pd.DataFrame(rows)


def build_tower_dump() -> pd.DataFrame:
    rows = []
    watch_number = PHONE_NUMBERS[0]
    for idx in range(55):
        rows.append(
            {
                "msisdn": watch_number if idx % 6 == 0 else random.choice(PHONE_NUMBERS),
                "imsi": random.choice(IMSI_LIST),
                "tower_id": TOWERS[idx % len(TOWERS)],
                "capture_time": random_time(idx % 5, bias_night=idx % 4 == 0),
                "location_sector": random.choice(["A", "B", "C"]),
            }
        )
    return pd.DataFrame(rows)


def build_ipdr() -> pd.DataFrame:
    rows = []
    suspect = PHONE_NUMBERS[0]
    for idx in range(58):
        rows.append(
            {
                "user_number": suspect if idx % 7 == 0 else random.choice(PHONE_NUMBERS),
                "ip_address": IPS[idx % len(IPS)] if idx % 5 == 0 else random.choice(IPS),
                "session_start": random_time(idx % 6, bias_night=idx % 2 == 0),
                "session_end": random_time(idx % 6, bias_night=idx % 2 == 0) + timedelta(minutes=random.randint(2, 120)),
                "bytes_transferred": random.randint(500, 500000),
                "device_id": f"DEV-{random.randint(1000, 9999)}",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    build_cdr().to_csv(OUTPUT_DIR / "cdr_sample.csv", index=False)
    build_tower_dump().to_csv(OUTPUT_DIR / "tower_dump_sample.csv", index=False)
    build_ipdr().to_csv(OUTPUT_DIR / "ipdr_sample.csv", index=False)
    print("Sample datasets generated in", OUTPUT_DIR)


if __name__ == "__main__":
    main()
