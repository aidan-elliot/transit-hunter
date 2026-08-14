"""Convenience wrapper for freezing the live NASA TOI catalogue.

Run from the repository root with:
    python scripts/freeze_catalog.py --retrieved-on YYYY-MM-DD
"""

from transit_hunter.catalog import main

if __name__ == "__main__":
    main()
