# AI Usage Disclosure

## Tools used

- Claude (Anthropic), model Claude Sonnet 5.5, in the claude.ai chat interface

## Conversation links

- Link 1: https://claude.ai/share/62b9e197-5e2e-4154-a087-3ab79e3525de

## What I used them for

I used Claude for guidance about specific Python concepts in the lab, which includes the following.

Validating ASCII flight IDs and exact datetime formats

Tracking duplicate flights across CSV files 

Rejecting Boolean values where query values must be numbers

Understanding argparse argument handling

Understanding why logging handlers must be removed and closed when main() is called repeatedly

## Which parts of the code were AI-generated or substantially AI-assisted

validator.py: Claude guided me on using ASCII-only regular expressions, fullmatch(), and checking the exact datetime format before testing whether the date is real.

csv_loader.py: Claude explained how a set or dictionary can store previously seen flight keys to detect duplicates across multiple files.

query.py: Claude explained that Boolean values are treated as integers in Python and showed how to reject them in _is_number and _is_valid_query.

flight_parser.py: Claude explained mutually exclusive argparse options and why logging handlers must be removed and closed in finally when main() is tested repeatedly.

## Key prompts

how can i validate ASCII flight IDs and exact datetimes without accepting weird formats?

why does Python treat booleans as numbers and how To reject them in query validation?

how argparse argument groups and logging handler cleanup work when main is tested multiple times

## What I changed or verified myself

I used Claude’s examples to help me understand and implement some of the flight ID, datetime, duplicate, query, and logging rules. I used the examples as guidance, made the needed changes for my code, and checked the results myself..
