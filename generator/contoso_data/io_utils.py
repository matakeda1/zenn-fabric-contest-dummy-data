"""CSV / JSON writing helpers with consistent conventions (UTF-8 without BOM, LF, ISO dates)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_csv(df: pd.DataFrame, path: Path, float_format: str | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8", lineterminator="\n", float_format=float_format,
              date_format="%Y-%m-%d %H:%M:%S")
    return path


def fmt_dt(s: pd.Series) -> pd.Series:
    """Format datetime64 series as 'YYYY-MM-DD HH:MM:SS' strings (NaT -> empty)."""
    out = pd.to_datetime(s).dt.strftime("%Y-%m-%d %H:%M:%S")
    return out.where(s.notna(), None)


def fmt_d(s: pd.Series) -> pd.Series:
    out = pd.to_datetime(s).dt.strftime("%Y-%m-%d")
    return out.where(s.notna(), None)
