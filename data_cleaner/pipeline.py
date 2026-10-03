"""Apply the cleaning rules to a whole table and collect every issue found."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yaml

from data_cleaner.rules import RULES, clean_phone, collapse_spaces


@dataclass
class CleanResult:
    """Output of clean_dataframe: clean rows, one row per issue, removed duplicates and counters."""

    cleaned: pd.DataFrame
    issues: pd.DataFrame
    duplicates: pd.DataFrame
    stats: dict[str, int] = field(default_factory=dict)


def load_config(path: str | Path) -> dict:
    """Read the YAML config (column rules, aliases, required fields, dedupe keys)."""
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def read_table(path: str | Path) -> pd.DataFrame:
    """Read an Excel file, or a CSV with auto-detected separator (UTF-8, then Latin-1), as strings."""
    path = Path(path)
    if path.suffix.lower() in (".xlsx", ".xlsm", ".xls"):
        return pd.read_excel(path, dtype=object)
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            return pd.read_csv(path, dtype=object, encoding=encoding, sep=None, engine="python")
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not decode {path}")


def normalize_headers(df: pd.DataFrame, aliases: dict[str, list[str]]) -> pd.DataFrame:
    """Rename 'E-mail', ' Correo ' or 'EMAIL' to the canonical column name 'email'."""
    lookup = {}
    for canonical, names in aliases.items():
        for name in [canonical, *names]:
            lookup[collapse_spaces(name).lower()] = canonical
    return df.rename(columns={c: lookup.get(collapse_spaces(c).lower(), collapse_spaces(c)) for c in df.columns})


def clean_dataframe(df: pd.DataFrame, config: dict) -> CleanResult:
    """Normalize headers, apply each column's rule, log issues with the source row and drop duplicates."""
    df = normalize_headers(df, config.get("aliases", {}))
    columns: dict[str, str] = config["columns"]
    required = set(config.get("required", []))
    df = df.dropna(how="all").reset_index(drop=True)
    source_rows = df.index + 2  # spreadsheet row number (1 = header)

    cleaned = df.copy()
    issues = []

    # Country first, because phone normalization depends on it.
    ordered = sorted(columns.items(), key=lambda kv: kv[1] != "country")
    for column, rule_name in ordered:
        if column not in df.columns:
            issues.append({"row": "-", "column": column, "value": "", "issue": "Column missing in file"})
            continue
        rule = RULES[rule_name]
        values = []
        for idx, raw in df[column].items():
            if rule_name == "phone":
                value, issue = clean_phone(raw, cleaned.at[idx, "country"] if "country" in cleaned else None)
            else:
                value, issue = rule(raw)
            if issue and (issue.startswith("Missing") and column not in required):
                issue = None
            if issue:
                issues.append({"row": int(source_rows[idx]), "column": column, "value": raw, "issue": issue})
            values.append(value)
        cleaned[column] = values

    # Duplicates: same normalized key = same customer. Keep the first occurrence.
    keys = [k for k in config.get("dedupe_on", []) if k in cleaned.columns]
    dup_mask = pd.Series(False, index=cleaned.index)
    for key in keys:
        present = cleaned[key].notna()
        dup_mask |= present & cleaned.duplicated(subset=[key], keep="first")
    duplicates = cleaned[dup_mask].assign(source_row=source_rows[dup_mask])
    cleaned = cleaned[~dup_mask].reset_index(drop=True)

    issues_df = pd.DataFrame(issues, columns=["row", "column", "value", "issue"])
    stats = {
        "rows_in": len(df),
        "rows_out": len(cleaned),
        "duplicates_removed": int(dup_mask.sum()),
        "issues": len(issues_df),
        "rows_with_issues": issues_df.loc[issues_df["row"] != "-", "row"].nunique(),
    }
    return CleanResult(cleaned=cleaned, issues=issues_df, duplicates=duplicates, stats=stats)
