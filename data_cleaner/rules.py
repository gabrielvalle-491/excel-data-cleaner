"""Column-level cleaning rules.

Every rule takes a raw value and returns `(clean_value, issue)`.
`issue` is None when the value is fine, or a short human-readable message
that ends up in the "Issues" sheet of the report.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Callable

Result = tuple[object, str | None]

EMAIL_RE = re.compile(r"^[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}$")
EMAIL_TYPOS = {"gmial.com": "gmail.com", "gmai.com": "gmail.com", "gmail.con": "gmail.com",
               "hotmial.com": "hotmail.com", "hotmail.con": "hotmail.com", "yahoo.con": "yahoo.com"}
DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%m/%d/%Y", "%Y/%m/%d", "%d %b %Y", "%b %d, %Y")
COUNTRIES = {
    "argentina": "Argentina", "arg": "Argentina", "ar": "Argentina",
    "mexico": "Mexico", "méxico": "Mexico", "mx": "Mexico",
    "chile": "Chile", "cl": "Chile",
    "españa": "Spain", "espana": "Spain", "spain": "Spain", "es": "Spain",
    "usa": "United States", "us": "United States", "eeuu": "United States", "united states": "United States",
    "colombia": "Colombia", "co": "Colombia",
}
COUNTRY_CODES = {"Argentina": "54", "Mexico": "52", "Chile": "56", "Spain": "34", "United States": "1",
                 "Colombia": "57"}
NULL_TOKENS = {"", "-", "--", "n/a", "na", "null", "none", "s/d", "sin dato", "?"}


def is_blank(value: object) -> bool:
    """True for None, NaN and placeholder tokens such as "-", "n/a" or "sin dato"."""
    if value is None:
        return True
    if isinstance(value, float) and value != value:  # NaN
        return True
    return str(value).strip().lower() in NULL_TOKENS


def collapse_spaces(value: object) -> str:
    """Convert to str, collapse runs of whitespace into one space and trim the ends."""
    return re.sub(r"\s+", " ", str(value)).strip()


def clean_text(value: object) -> Result:
    """Generic text: collapse spaces; blanks become None (never an issue)."""
    if is_blank(value):
        return None, None
    return collapse_spaces(value), None


def clean_place(value: object) -> Result:
    """'  buenos   AIRES ' -> 'Buenos Aires'"""
    if is_blank(value):
        return None, None
    return collapse_spaces(value).title(), None


def clean_name(value: object) -> Result:
    """'  juan   PÉREZ ' -> 'Juan Pérez' (keeps accents, fixes casing and spaces)."""
    if is_blank(value):
        return None, "Missing name"
    text = collapse_spaces(value)
    if re.search(r"\d", text):
        return text.title(), "Name contains digits"
    particles = {"de", "del", "la", "y", "da", "van", "von"}
    words = [w.lower() if i and w.lower() in particles else w.capitalize() for i, w in enumerate(text.split(" "))]
    return " ".join(words), None


def clean_email(value: object) -> Result:
    """Lowercase and trim an email, fix common domain typos and flag invalid formats."""
    if is_blank(value):
        return None, "Missing email"
    email = collapse_spaces(value).lower().replace(" ", "").replace(",", ".")
    if "@" in email:
        user, domain = email.rsplit("@", 1)
        if domain in EMAIL_TYPOS:
            fixed = f"{user}@{EMAIL_TYPOS[domain]}"
            return fixed, f"Fixed email typo: {domain}"
    if not EMAIL_RE.match(email):
        return email, "Invalid email"
    return email, None


def clean_phone(value: object, country: str | None = "Argentina") -> Result:
    """Normalize to E.164 (+5492657351236). Argentina mobile numbers get the 9 prefix."""
    if is_blank(value):
        return None, "Missing phone"
    raw = str(value)
    if isinstance(value, float) and value.is_integer():
        raw = str(int(value))
    digits = re.sub(r"\D", "", raw)
    code = COUNTRY_CODES.get(country or "Argentina", "54")
    # "542657..." typed without "+": detect the country code. One-digit codes (US "1") are
    # ambiguous with local area codes, so they are only trusted when written with "+".
    known_prefix = next((c for c in COUNTRY_CODES.values()
                         if len(c) > 1 and digits.startswith(c) and len(digits) > 10), None)
    if raw.strip().startswith("+") or digits.startswith("00"):
        digits = digits.lstrip("0")
    elif known_prefix:
        code = known_prefix  # number already carries its own country code
    else:
        digits = code + digits.lstrip("0")
    if digits.startswith("54"):
        national = digits[2:]
        # Drop the legacy "15" mobile prefix after a 3/4 digit area code: 2657 15 351236
        match = re.match(r"^(9?)(\d{2,4})15(\d{6,8})$", national)
        if match and len(match.group(2) + match.group(3)) == 10:
            national = match.group(2) + match.group(3)
        if not national.startswith("9") and len(national) == 10:
            national = "9" + national
        digits = "54" + national
    if not 10 <= len(digits) <= 15:
        return f"+{digits}", "Phone has an invalid length"
    expected = COUNTRY_CODES.get(country or "")
    if expected and not digits.startswith(expected):
        return f"+{digits}", f"Phone prefix does not match country ({country})"
    return f"+{digits}", None


def clean_date(value: object) -> Result:
    """Parse any of DATE_FORMATS (or a datetime) into ISO YYYY-MM-DD."""
    if is_blank(value):
        return None, "Missing date"
    if isinstance(value, datetime):
        return value.date().isoformat(), None
    text = collapse_spaces(value)
    for fmt in DATE_FORMATS:
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        if parsed.year < 1900 or parsed.year > 2100:
            return text, "Date out of range"
        return parsed.date().isoformat(), None
    return text, "Unrecognized date"


def clean_amount(value: object) -> Result:
    """'$ 1.234,50' / '1,234.50' / 'USD 1234.5' -> 1234.5"""
    if is_blank(value):
        return None, "Missing amount"
    if isinstance(value, (int, float)):
        return round(float(value), 2), None
    text = re.sub(r"[^\d,.\-]", "", str(value))
    if text.rfind(",") > text.rfind("."):
        text = text.replace(".", "").replace(",", ".")
    else:
        text = text.replace(",", "")
    try:
        amount = round(float(text), 2)
    except ValueError:
        return str(value), "Invalid amount"
    return amount, ("Negative amount" if amount < 0 else None)


def clean_country(value: object) -> Result:
    """Map country aliases ('ARG', 'mx', 'EEUU', 'España') to a standard English name."""
    if is_blank(value):
        return None, "Missing country"
    key = collapse_spaces(value).lower()
    plain = unicodedata.normalize("NFKD", key).encode("ascii", "ignore").decode()
    country = COUNTRIES.get(key) or COUNTRIES.get(plain)
    return (country, None) if country else (collapse_spaces(value).title(), "Unknown country")


RULES: dict[str, Callable[..., Result]] = {
    "text": clean_text,
    "place": clean_place,
    "name": clean_name,
    "email": clean_email,
    "phone": clean_phone,
    "date": clean_date,
    "amount": clean_amount,
    "country": clean_country,
}
