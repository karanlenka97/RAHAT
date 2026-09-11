#!/usr/bin/env python3
"""CLI utility to execute database seeders."""
import sys
import os

# Prepend backend to sys.path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.db.session import SessionLocal
from app.db.seed import run_seeds


def main():
    print("Starting database seeding...")
    db = SessionLocal()
    try:
        results = run_seeds(db)
        print(f"Seeding completed successfully: {results}")
    except Exception as e:
        print(f"Seeding failed: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
