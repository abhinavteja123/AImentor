# Alembic Migrations

`env.py` is wired to load `app.database.postgres.Base` and all models from
`app.models`, and it reads `DATABASE_URL` from the environment (falling back
to `settings.DATABASE_URL`).

## First time: generate the baseline

Requires a running Postgres matching `DATABASE_URL`.

```bash
# from backend/
alembic revision --autogenerate -m "baseline"
alembic upgrade head
```

Review the generated file in `alembic/versions/` before committing.

## Day-to-day

```bash
alembic revision --autogenerate -m "add foo column"
alembic upgrade head        # apply
alembic downgrade -1        # rollback one
alembic current             # show applied revision
alembic history             # show all revisions
```

## Stop using create_all in production

`app/database/postgres.py::init_db` still calls `Base.metadata.create_all`,
which does NOT apply migrations. Once a baseline migration is committed,
remove that call from `init_db` and run `alembic upgrade head` as part of
deploy instead.
