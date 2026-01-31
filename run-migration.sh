#!/bin/bash

echo "========================================"
echo "Running Resume Table Migration"
echo "========================================"
echo

echo "Executing migration script in Docker container..."
docker compose exec backend python scripts/migrate_resume_table.py

if [ $? -eq 0 ]; then
    echo
    echo "========================================"
    echo "Migration completed successfully!"
    echo "========================================"
else
    echo
    echo "========================================"
    echo "Migration failed! Check logs above."
    echo "========================================"
    exit 1
fi
