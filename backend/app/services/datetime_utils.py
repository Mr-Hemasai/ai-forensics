from __future__ import annotations

import re

import pandas as pd


_DAYFIRST_CANDIDATE_RE = re.compile(r"^\s*(\d{1,2})[-/](\d{1,2})[-/](\d{2,4})(?:\s|$)")
_ISO_CANDIDATE_RE = re.compile(r"^\s*\d{4}[-/]\d{1,2}[-/]\d{1,2}")


def _guess_dayfirst(values: pd.Series) -> bool | None:
    first_gt_12 = 0
    second_gt_12 = 0
    ambiguous = 0

    for raw in values.head(50).astype(str):
        match = _DAYFIRST_CANDIDATE_RE.match(raw)
        if not match:
            continue
        first = int(match.group(1))
        second = int(match.group(2))
        if first > 12 and second <= 12:
            first_gt_12 += 1
        elif second > 12 and first <= 12:
            second_gt_12 += 1
        else:
            ambiguous += 1

    if first_gt_12 > second_gt_12:
        return True
    if second_gt_12 > first_gt_12:
        return False
    if ambiguous:
        return True
    return None


def coerce_datetime(series: pd.Series) -> pd.Series:
    values = series.dropna()
    if values.empty:
        return pd.to_datetime(series, errors="coerce")

    string_values = values.astype(str).str.strip()
    if string_values.empty:
        return pd.to_datetime(series, errors="coerce")

    has_iso = bool(string_values.head(20).map(lambda item: bool(_ISO_CANDIDATE_RE.match(item))).any())
    dayfirst = None if has_iso else _guess_dayfirst(string_values)

    parsed = pd.to_datetime(series, errors="coerce", format="mixed", dayfirst=bool(dayfirst))
    parsed_ratio = parsed.notna().mean()

    if dayfirst is None:
        return parsed

    alternate = pd.to_datetime(series, errors="coerce", format="mixed", dayfirst=not dayfirst)
    alternate_ratio = alternate.notna().mean()
    return alternate if alternate_ratio > parsed_ratio else parsed
