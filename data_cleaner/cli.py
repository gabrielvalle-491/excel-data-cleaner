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
    """Run the cleaner from the command line. Returns the process exit code (0 = ok, 1 = file not found)."""
    parser = argparse.ArgumentParser(prog="python -m data_cleaner",
                                     description="Clean, validate and standardize a spreadsheet")
    parser.add_argument("input", type=Path, help="CSV or Excel file")
    parser.add_argument("-o", "--output", type=Path, default=Path("output/clean_report.xlsx"),
                        help="Excel report to write (default: output/clean_report.xlsx)")
    parser.add_argument("-c", "--config", type=Path, default=Path("config.yaml"),
                        help="YAML file with column rules and aliases (default: config.yaml)")
    args = parser.parse_args(argv)

    for path in (args.input, args.config):
        if not path.exists():
            print(f"File not found: {path}", file=sys.stderr)
            return 1

    result = clean_dataframe(read_table(args.input), load_config(args.config))
    path = write_report(result, args.output)
    s = result.stats
    print(f"Rows in: {s['rows_in']} | rows out: {s['rows_out']} | duplicates removed: {s['duplicates_removed']}")
    print(f"Issues logged: {s['issues']} (in {s['rows_with_issues']} rows) -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
