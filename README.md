# Excel Data Cleaner

![CI](https://github.com/gabrielvalle-491/excel-data-cleaner/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Automatically cleans, validates and standardizes large spreadsheets.

Feed it a messy CRM export or a customer list built by hand (Excel or CSV) and get
back a clean table, a list of every problem found (with the original row number),
the duplicates that were removed and a summary — in one Excel report.

## The business problem

A sales team keeps customers in spreadsheets filled by different people over years:
names in random casing, emails with typos (`@gmial.com`), phones written 5 different
ways (`0351-15-1438687`, `+54 9 2657 717867`, `542657277863`), dates in 5 formats,
amounts with `$ 1.234,56` or `USD 1234.5`, the same customer typed twice… Importing
that into a CRM or sending a campaign fails or bounces.

## What it does

| Column type | Cleaning | Validation (goes to the Issues sheet) |
|-------------|----------|----------------------------------------|
| `name` | Fixes spaces and casing, keeps accents, lowercases particles (*de la*) | Missing, contains digits |
| `email` | Lowercases, trims, **auto-fixes common domain typos** | Invalid format, missing |
| `phone` | Normalizes to international **E.164** (`+5492657351236`), removes the legacy `15` mobile prefix, detects country codes | Invalid length, **prefix does not match the country column** |
| `date` | 8 input formats → ISO `YYYY-MM-DD` | Impossible dates (`31/02/2025`), unknown formats |
| `amount` | `$ 1.234,50`, `1,234.50`, `USD 99.9` → `1234.5` | Not a number, negative |
| `country` | Aliases (`ARG`, `mx`, `EEUU`, `España`) → standard name | Unknown country |
| `place` | Title case + spaces (`  buenos   AIRES` → `Buenos Aires`) | – |

It also:

- Recognizes **header variations** (`E-mail`, `Correo`, `Mail` → `email`) via `config.yaml`.
- Drops fully empty rows and **removes duplicates** after normalization (so `ANA@GMAIL.COM ` and `ana@gmail.com` are the same customer).
- Keeps the original spreadsheet row number in every issue, so fixes can be traced.

Everything is driven by `config.yaml` — adapting it to another file is editing a few lines, not code.

## Quick start

```bash
pip install -r requirements.txt

# 1) create a deliberately messy 500-row customer file
python -m data_cleaner.generate_messy_data samples/customers_messy.xlsx --rows 500

# 2) clean it
python -m data_cleaner samples/customers_messy.xlsx -o output/customers_clean_report.xlsx
```

```
Rows in: 541 | rows out: 499 | duplicates removed: 42
Issues logged: 246 (in 219 rows) -> output/customers_clean_report.xlsx
```

## Before → after (real output of the command above)

**Before** (`samples/customers_messy.xlsx`)

| Nombre | E-mail | Telefono | País | Fecha alta | Monto compra | Ciudad |
|---|---|---|---|---|---|---|
| MARÍA pérez | MARIA.PEREZ95@GMAIL.COM | +54 9 2657 717867 | Argentina | 08.10.2024 | $ 62.355,63 | - |
| Carlos sosa | CARLOS.SOSA54@GMAIL.COM | 542657277863 | Argentina | 13-08-2024 | $ 113.128,45 | villa mercedes |
| Carlos GÓMEZ | sin dato | 541141794522 | argentina | 08/11/2025 | USD 58132.72 | CÓRDOBA |
| Carlos Fernández | carlos.fernandez90@gmial.com | 541142841438 | argentina | 30/11/2025 | USD 162536.79 | villa mercedes |

**After** (`Clean data` sheet)

| name | email | phone | country | signup_date | purchase_amount | city |
|---|---|---|---|---|---:|---|
| María Pérez | maria.perez95@gmail.com | +5492657717867 | Argentina | 2024-10-08 | 62,355.63 | |
| Carlos Sosa | carlos.sosa54@gmail.com | +5492657277863 | Argentina | 2024-08-13 | 113,128.45 | Villa Mercedes |
| Carlos Gómez | | +5491141794522 | Argentina | 2025-11-08 | 58,132.72 | Córdoba |
| Carlos Fernández | carlos.fernandez90@gmail.com | +5491142841438 | Argentina | 2025-11-30 | 162,536.79 | Villa Mercedes |

**Issues found** (top of the `Summary` sheet)

| Column | Issue | Count |
|---|---|---:|
| email | Fixed email typo: gmial.com | 67 |
| email | Fixed email typo: hotmail.con | 63 |
| email | Missing email | 49 |
| country | Unknown country | 24 |
| signup_date | Unrecognized date | 13 |
| phone | Phone prefix does not match country (Chile) | 9 |

The report workbook has 4 sheets: **Summary**, **Clean data**, **Issues**, **Duplicates**.

## Project structure

```
data_cleaner/
├── rules.py                # one function per column type: value -> (clean value, issue)
├── pipeline.py             # header aliases, rule application, dedupe, stats
├── report.py               # formatted Excel report
├── generate_messy_data.py  # realistic dirty demo data
└── cli.py
config.yaml                 # column -> rule mapping, aliases, required fields, dedupe keys
tests/                      # 22 pytest tests, run on every push (GitHub Actions)
```

## Tests

```bash
pytest -q
```

## Notes

- Demo data is synthetic (`generate_messy_data.py`). No real customer data.
- Built with Python (pandas, openpyxl) and [Claude Code](https://claude.com/claude-code) as an AI pair programmer.

## Author

**Gabriel Valle** — Data & AI automation (Excel, PDF, workflows) · Villa Mercedes, Argentina · Remote
