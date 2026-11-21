"""Reading CSV files into flight records and error messages."""
import csv
import os

from validator import to_record, validate_row


def _printable(text: str) -> str:
    """Replace characters that could break a log line (tabs, form feeds, ...)."""
    return "".join(ch if ch.isprintable() else " " for ch in text)


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    """Process the CSV files in the order given.

    Return (records, errors):
      records - valid flight records, in input order
      errors  - one message per invalid row, in input order, formatted as
                "<file name>:<line number>: <ERROR_CODE> | <free text>"
                (base file name only, no timestamp or level, no newline)

    Also performs the DUPLICATE_FLIGHT check across all the files.
    Does not write any files and does not log anything itself.
    """
    records: list[dict] = []
    errors: list[str] = []
    # (flight_id, departure_datetime) of every valid row seen so far, in ALL files
    seen: set[tuple[str, str]] = set()

    for path in paths:
        file_name = os.path.basename(path)

        # Default newline handling turns "\r\n" into "\n", so Windows files work.
        with open(path, encoding="utf-8") as f:
            for line_number, raw_line in enumerate(f, start=1):
                if line_number == 1:
                    continue  # header line: skip without validating

                line = raw_line.rstrip("\r\n")
                if not line.strip():
                    continue  # blank line (only whitespace)
                if line.lstrip().startswith("#"):
                    continue  # comment line

                # Split this one line into fields with the csv module.
                try:
                    fields = next(csv.reader([line]))
                except (csv.Error, StopIteration):
                    fields = []  # cannot be split: reported as WRONG_FIELD_COUNT

                code = validate_row(fields, airports)

                if code is None:
                    record = to_record(fields)
                    key = (record["flight_id"], record["departure_datetime"])
                    if key in seen:
                        code = "DUPLICATE_FLIGHT"
                    else:
                        seen.add(key)
                        records.append(record)

                if code is not None:
                    errors.append(f"{file_name}:{line_number}: {code} | {_printable(line)}")

    return records, errors
