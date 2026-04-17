# Job Parser

Worker that scans job boards every 2 hours, stores seen vacancies, and sends new items to Telegram grouped by category.

## Quick Start

1. Set required environment variables: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`
2. Run `python -m job_parser.cli once` for a single scan or `python -m job_parser.cli worker` for continuous polling

## Commands

- `python -m job_parser.cli once` - run a single scan with database and Telegram
- `python -m job_parser.cli worker` - run the 2-hour polling loop

## Environment

- `TELEGRAM_BOT_TOKEN` - required
- `TELEGRAM_CHAT_ID` - required
- `JOB_PARSER_DB_PATH` - optional, defaults to `./data/job_parser.sqlite3`
- `JOB_PARSER_INTERVAL_MINUTES` - optional, defaults to `120`

## Set Environment Variables

### Local shell

Export the variables before running the bot:

```bash
export TELEGRAM_BOT_TOKEN="123456:ABCDEF"
export TELEGRAM_CHAT_ID="-1001234567890"
export JOB_PARSER_DB_PATH="./data/job_parser.sqlite3"
export JOB_PARSER_INTERVAL_MINUTES="120"
```

### `.env` file

You can also keep local values in a `.env` file and load it from your shell or editor:

```env
TELEGRAM_BOT_TOKEN=123456:ABCDEF
TELEGRAM_CHAT_ID=-1001234567890
JOB_PARSER_DB_PATH=./data/job_parser.sqlite3
JOB_PARSER_INTERVAL_MINUTES=120
```

## GitHub Actions Cron + Manual Run

This repository includes a workflow in `.github/workflows/job-parser-cron.yml` that can:

- run on schedule every 2 hours
- run in a UTC window aligned to daytime Kyiv hours
- run manually with `workflow_dispatch` in `once` mode

Required GitHub repository secrets:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Notes:

- SQLite DB is cached between workflow runs via `actions/cache` at `data/job_parser.sqlite3`.
