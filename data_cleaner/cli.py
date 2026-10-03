"""Command line entry point.

    python -m data_cleaner samples/customers_messy.xlsx -o output/customers_clean.xlsx
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from data_cleaner.pipeline import clean_dataframe, load_config, read_table
from data_cleaner.report import write_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clean, validate and standardize a spreadsheet")
    parser.add_argument("input", type=Path, help="CSV or Excel file")
    parser.add_argument("-o", "--output", type=Path, default=Path("output/clean_report.xlsx"))
    parser.add_argument("-c", "--config", type=Path, default=Path("config.yaml"))
    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"File not found: {args.input}", file=sys.stderr)
        return 1

    result = clean_dataframe(read_table(args.input), load_config(args.config))
    path = write_report(result, args.output)
    s = result.stats
    print(f"Rows in: {s['rows_in']} | rows out: {s['rows_out']} | duplicates removed: {s['duplicates_removed']}")
    print(f"Issues logged: {s['issues']} (in {s['rows_with_issues']} rows) -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
