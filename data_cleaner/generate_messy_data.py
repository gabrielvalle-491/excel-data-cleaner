"""Create a deliberately messy customer spreadsheet (like a real CRM export).

    python -m data_cleaner.generate_messy_data samples/customers_messy.xlsx --rows 500
"""

from __future__ import annotations

import argparse
import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

FIRST = ["juan", "MARÍA", "  lucía", "Carlos", "ana", "josé luis", "Sofía", "martín", "valentina", "diego"]
LAST = ["pérez", "GÓMEZ", "rodríguez ", "de la fuente", "Fernández", "lópez", "díaz", "MARTÍNEZ", "sosa"]
DOMAINS = ["gmail.com", "hotmail.com", "yahoo.com", "empresa.com.ar", "gmial.com", "hotmail.con"]
COUNTRIES = ["Argentina", "ARG", "argentina ", "México", "mx", "Chile", "España", "USA", "colombia", "Atlantis"]
DATE_STYLES = ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%b %d, %Y", "%d.%m.%Y"]


def messy_phone(rng: random.Random) -> str:
    area, number = rng.choice(["2657", "11", "351", "261"]), str(rng.randint(100000, 9999999)).zfill(7)
    number = number[: 10 - len(area)].rjust(10 - len(area), "4")
    return rng.choice([
        f"+54 9 {area} {number}",
        f"0{area}-15-{number}",
        f"({area}) {number}",
        f"54{area}{number}",
        f"{area}{number}",
    ])


def generate(path: Path, rows: int = 500, seed: int = 42) -> Path:
    rng = random.Random(seed)
    records = []
    for _ in range(rows):
        first, last = rng.choice(FIRST), rng.choice(LAST)
        user = f"{first.strip().split()[0].lower()}.{last.strip().split()[-1].lower()}{rng.randint(1, 99)}"
        user = user.replace("í", "i").replace("é", "e").replace("á", "a").replace("ó", "o").replace("ú", "u")
        signup = date(2024, 1, 1) + timedelta(days=rng.randint(0, 900))
        amount = round(rng.uniform(1500, 250000), 2)
        records.append({
            " Nombre ": f"{first} {last}",
            "E-mail": rng.choices([f"{user}@{rng.choice(DOMAINS)}", f" {user.upper()}@GMAIL.COM ", "", "sin dato"],
                                  weights=[70, 20, 5, 5])[0],
            "Telefono": messy_phone(rng),
            "País": rng.choice(COUNTRIES[:3]) if rng.random() < 0.8 else rng.choice(COUNTRIES),
            "Fecha alta": signup.strftime(rng.choice(DATE_STYLES)) if rng.random() > 0.03 else "31/02/2025",
            "Monto compra": rng.choice([f"$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                                        f"{amount:,.2f}", f"USD {amount}", "n/a"]),
            "Ciudad": rng.choice(["villa mercedes", "  San Luis", "CÓRDOBA", "Buenos   Aires", "-"]),
        })
    # Re-insert ~8% of rows as duplicates with small formatting differences.
    for record in rng.sample(records, k=rows // 12):
        dup = dict(record)
        dup[" Nombre "] = dup[" Nombre "].upper()
        records.insert(rng.randint(0, len(records)), dup)
    records.insert(rng.randint(0, len(records)), {k: None for k in records[0]})  # blank row

    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(records).to_excel(path, index=False)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a messy customer spreadsheet")
    parser.add_argument("output", type=Path, nargs="?", default=Path("samples/customers_messy.xlsx"))
    parser.add_argument("--rows", type=int, default=500)
    args = parser.parse_args()
    print(f"Created {generate(args.output, args.rows)}")


if __name__ == "__main__":
    main()
