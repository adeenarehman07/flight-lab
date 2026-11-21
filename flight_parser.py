"""Flight Schedule Parser and Query Tool - command-line entry point.

Run from the project folder, for example:
    python flight_parser.py -i data/db.csv -a data/airports.txt
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime

from csv_loader import parse_files
from query import run_queries
from validator import load_airports

# TODO: fill in your details: plain ASCII, no spaces or underscores.
STUDENT_ID = "000RDB000"
FIRST_NAME = "Firstname"
LAST_NAME = "Lastname"


class RuntimeProblem(Exception):
    """A problem that must end the run with exit code 1 and an 'Error: ...' line."""


# ---------------------------------------------------------------- arguments

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="flight_parser.py",
        description="Validate flight schedule CSV files, store the valid flights "
                    "as a JSON database and answer queries against it.",
    )
    # Exactly one data source is required. argparse enforces this and exits
    # with code 2 when there is none or more than one.
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("-i", metavar="FILE", help="parse a single CSV file")
    source.add_argument("-d", metavar="FOLDER", help="parse every .csv file in a folder")
    source.add_argument("-j", metavar="FILE", help="load an existing JSON database instead of parsing CSVs")

    parser.add_argument("-a", metavar="FILE", help="airport list file (required with -i and -d)")
    parser.add_argument("-o", metavar="FILE", help="output path for the JSON database (default: db.json)")
    parser.add_argument("-q", metavar="FILE", help="JSON file with queries to run")
    parser.add_argument("-r", metavar="FOLDER", default=".",
                        help="folder for the query response file (default: current folder)")
    return parser


def parse_arguments(argv):
    """Parse the command line. Exits with code 2 (SystemExit) on a usage error."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if args.j is None and args.a is None:
        parser.error("-a is required with -i and -d")
    if args.j is not None and args.o is not None:
        parser.error("-o cannot be used with -j")
    return args


# ---------------------------------------------------------------- helpers

def say(text: str) -> None:
    """print() that can never crash the program (stdout is not graded)."""
    try:
        print(text)
    except (UnicodeEncodeError, OSError):
        pass


def read_json_file(path: str, what: str):
    """Read a JSON file; any problem becomes a RuntimeProblem."""
    try:
        with open(path, encoding="utf-8-sig") as f:
            return json.load(f)
    except FileNotFoundError:
        raise RuntimeProblem(f"{what} file not found: {path}")
    except json.JSONDecodeError as exc:
        raise RuntimeProblem(f"{what} file is not valid JSON: {path} ({exc})")
    except (OSError, UnicodeDecodeError) as exc:
        raise RuntimeProblem(f"cannot read {what} file {path}: {exc}")


def write_json_file(path: str, data) -> None:
    """Write data as JSON; any problem becomes a RuntimeProblem."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
    except OSError as exc:
        raise RuntimeProblem(f"cannot write {path}: {exc}")


def load_database(path: str) -> list[dict]:
    """Load a JSON database (-j). It must be an array of objects."""
    db = read_json_file(path, "database")
    if not isinstance(db, list) or not all(isinstance(record, dict) for record in db):
        raise RuntimeProblem(f"database file must contain a JSON array of objects: {path}")
    return db


def collect_csv_paths(args) -> list[str]:
    """Work out which CSV files to read for -i or -d."""
    if args.i is not None:
        if not os.path.isfile(args.i):
            raise RuntimeProblem(f"CSV file not found: {args.i}")
        return [args.i]

    if not os.path.isdir(args.d):
        raise RuntimeProblem(f"folder not found: {args.d}")
    try:
        names = os.listdir(args.d)
    except OSError as exc:
        raise RuntimeProblem(f"cannot read folder {args.d}: {exc}")
    # only files (not sub-folders) ending in .csv, in sorted filename order
    csv_names = sorted(name for name in names
                       if name.endswith(".csv") and os.path.isfile(os.path.join(args.d, name)))
    if not csv_names:
        raise RuntimeProblem(f"no .csv files found in folder: {args.d}")
    return [os.path.join(args.d, name) for name in csv_names]


def parse_csv_data(args, logger) -> list[dict]:
    """-i / -d: read the CSV files, log the invalid rows, write the database."""
    paths = collect_csv_paths(args)

    try:
        airports = load_airports(args.a)
    except FileNotFoundError:
        raise RuntimeProblem(f"airport file not found: {args.a}")
    except (OSError, UnicodeDecodeError) as exc:
        raise RuntimeProblem(f"cannot read airport file {args.a}: {exc}")

    try:
        records, errors = parse_files(paths, airports)
    except (OSError, UnicodeDecodeError) as exc:
        raise RuntimeProblem(f"cannot read CSV data: {exc}")

    for message in errors:
        logger.warning("%s", message)
    logger.info("Processed %d file(s): %d valid flight(s), %d invalid row(s)",
                len(paths), len(records), len(errors))

    write_json_file(database_path(args), records)
    say(f"{len(records)} valid flight(s), {len(errors)} invalid row(s).")
    say(f"Database written to {database_path(args)}")
    return records


def database_path(args) -> str:
    return args.o if args.o is not None else "db.json"


def run_query_file(args, db: list[dict]) -> None:
    """-q: run the queries and write exactly one response file."""
    queries = read_json_file(args.q, "query")
    if not isinstance(queries, (dict, list)):
        raise RuntimeProblem(f"query file must contain a JSON object or an array: {args.q}")

    results = run_queries(db, queries)

    stamp = datetime.now().strftime("%Y%m%d_%H%M")
    file_name = f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_{stamp}.json"
    response_path = os.path.join(args.r, file_name)
    write_json_file(response_path, results)
    say(f"{len(results)} quer{'y' if len(results) == 1 else 'ies'} answered. Response written to {response_path}")


# ---------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    """Run the whole program and return the exit code (0, 1 or 2).

    argv is the argument list without the program name.
    None means use sys.argv[1:] (argparse does this for you).
    Do not call sys.exit() inside main(); return the code instead.
    """
    # argparse calls sys.exit() for usage errors and for -h; turn that into
    # a returned exit code.
    try:
        args = parse_arguments(argv)
    except SystemExit as exc:
        if isinstance(exc.code, int):
            return exc.code
        return 0 if exc.code is None else 2

    logger = logging.getLogger("flight_parser")
    handler = None
    try:
        if args.j is not None:
            # -j: no database and no errors.log are written
            db = load_database(args.j)
        else:
            # errors.log goes into the same folder as the database file
            log_folder = os.path.dirname(database_path(args)) or "."
            log_path = os.path.join(log_folder, "errors.log")
            try:
                handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
            except OSError as exc:
                raise RuntimeProblem(f"cannot write {log_path}: {exc}")
            logger.setLevel(logging.INFO)
            handler.setFormatter(logging.Formatter(
                "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
            logger.addHandler(handler)

            db = parse_csv_data(args, logger)

        if args.q is not None:
            run_query_file(args, db)
        return 0

    except RuntimeProblem as exc:
        if handler is not None:
            logger.error("%s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # safety net: never show a traceback
        if handler is not None:
            logger.error("unexpected problem: %s", exc)
        print(f"Error: unexpected problem: {exc}", file=sys.stderr)
        return 1
    finally:
        # Always remove and close the handler, so the next call of main()
        # in the same process starts clean.
        if handler is not None:
            logger.removeHandler(handler)
            handler.close()


if __name__ == "__main__":
    sys.exit(main())
