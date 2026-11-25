# Backend tests

Contract tests for the API. Each test checks status codes, JSON shape, and error messages through HTTP. Fixtures live in `conftest.py`. One file covers one resource.

The suite uses Postgres database `platform_test`. It does not read or write the development database. Schema check constraints use Postgres `btrim`, so the tests do not run on SQLite.

`platform_test` is created automatically when the suite starts. Postgres must already be running on `localhost:5432`. Credentials come from the environment, or from the project `.env` (`POSTGRES_USER` and `POSTGRES_PASSWORD`).

## Setup

From the repository root, start Postgres:

```bash
docker compose up -d db
```

From `backend/`, install dependencies and run the suite:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest
```

Run one file or one test:

```bash
python -m pytest tests/test_users.py
python -m pytest tests/test_users.py::test_create_user
```

Verbose output:

```bash
python -m pytest -v
```
