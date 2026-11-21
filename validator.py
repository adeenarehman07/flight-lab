"""Row validation: airport list loading, single-row checks, record building."""
import math
import re
from datetime import datetime

# Regular expressions. We use [0-9] and [A-Z] on purpose instead of \d or
# str.isalnum()/isupper(): those also accept non-ASCII characters such as
# "Ā" or Arabic digits, which the assignment says must be rejected.
# re.fullmatch() must match the WHOLE string (no stray newline at the end).
FLIGHT_ID_RE = re.compile(r"[A-Za-z0-9]{2,8}")
AIRPORT_CODE_RE = re.compile(r"[A-Z]{3}")
DATETIME_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}")


def load_airports(path: str) -> set[str]:
    """Read an airport list file and return the set of codes.

    One code per line. Strip whitespace; skip blank lines and lines
    starting with '#'.
    """
    airports = set()
    # utf-8-sig also copes with a hidden "BOM" mark at the start of the file.
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            code = line.strip()
            if not code or code.startswith("#"):
                continue
            airports.add(code)
    return airports


def parse_datetime(text: str) -> datetime | None:
    """Return a datetime for text written EXACTLY as 'YYYY-MM-DD HH:MM'.

    Returns None if the shape is wrong (not zero-padded, 'T' instead of a
    space, ...) or the date/time does not exist (2025-02-30, hour 24, ...).
    The regex checks the shape; datetime() checks that the values are real.
    """
    if not DATETIME_RE.fullmatch(text):
        return None
    try:
        # The regex guarantees the digits sit at fixed positions, so we can
        # slice them out. datetime() raises ValueError for impossible values
        # (month 13, 30 February, hour 24, year 0, ...). This is much faster
        # than datetime.strptime() on large files.
        return datetime(int(text[0:4]), int(text[5:7]), int(text[8:10]),
                        int(text[11:13]), int(text[14:16]))
    except ValueError:
        return None


def validate_row(fields: list[str], airports: set[str]) -> str | None:
    """Check one CSV row (fields as returned by csv.reader, not yet stripped).

    Return None if the row is valid, otherwise the error code of the
    FIRST failing check (checks 1-11 in the specification, in order).
    Does not check for duplicates.
    """
    # 1. exactly 6 fields
    if len(fields) != 6:
        return "WRONG_FIELD_COUNT"

    flight_id, origin, destination, departure, arrival, price = (f.strip() for f in fields)

    # 2. no empty field (after stripping)
    if not all((flight_id, origin, destination, departure, arrival, price)):
        return "MISSING_FIELD"

    # 3. flight id: 2-8 ASCII letters or digits
    if not FLIGHT_ID_RE.fullmatch(flight_id):
        return "INVALID_FLIGHT_ID"

    # 4-5. origin / destination: 3 uppercase ASCII letters AND in the airport list
    if not AIRPORT_CODE_RE.fullmatch(origin) or origin not in airports:
        return "INVALID_ORIGIN"
    if not AIRPORT_CODE_RE.fullmatch(destination) or destination not in airports:
        return "INVALID_DESTINATION"

    # 6. origin and destination must differ
    if origin == destination:
        return "SAME_ORIGIN_DESTINATION"

    # 7-8. both date-times must be real and in the exact format
    departure_dt = parse_datetime(departure)
    if departure_dt is None:
        return "INVALID_DEPARTURE"
    arrival_dt = parse_datetime(arrival)
    if arrival_dt is None:
        return "INVALID_ARRIVAL"

    # 9. arrival strictly after departure
    if arrival_dt <= departure_dt:
        return "ARRIVAL_NOT_AFTER_DEPARTURE"

    # 10. price must be convertible by float() and finite (no nan / inf)
    try:
        price_value = float(price)
    except ValueError:
        return "INVALID_PRICE"
    if not math.isfinite(price_value):
        return "INVALID_PRICE"

    # 11. price must be positive
    if price_value <= 0:
        return "NON_POSITIVE_PRICE"

    return None


def to_record(fields: list[str]) -> dict:
    """Turn a valid row into a flight record dictionary.

    Keys: flight_id, origin, destination, departure_datetime,
    arrival_datetime (stripped strings) and price (float).
    """
    flight_id, origin, destination, departure, arrival, price = (f.strip() for f in fields)
    return {
        "flight_id": flight_id,
        "origin": origin,
        "destination": destination,
        "departure_datetime": departure,
        "arrival_datetime": arrival,
        "price": float(price),
    }
