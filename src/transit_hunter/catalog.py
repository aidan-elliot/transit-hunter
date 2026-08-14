"""Freeze and audit the NASA Exoplanet Archive TESS Objects of Interest catalogue."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

TAP_ENDPOINT = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
REQUIRED_COLUMNS = (
    "toi", "tid", "tfopwg_disp", "pl_orbper", "pl_tranmid", "toi_created",
    "rowupdate", "ra", "dec", "st_tmag", "st_teff", "st_rad",
)
CATALOG_QUERY = """SELECT toi, tid, tfopwg_disp, pl_orbper, pl_tranmid, toi_created,
       rowupdate, ra, dec, st_tmag, st_teff, st_rad
FROM toi"""
POSITIVE_DISPOSITIONS = {"CP"}
NEGATIVE_DISPOSITIONS = {"FP", "FA"}
UNRESOLVED_DISPOSITIONS = {"PC", "APC"}
KNOWN_PLANET_DISPOSITION = "KP"


def tap_url(query: str = CATALOG_QUERY, endpoint: str = TAP_ENDPOINT) -> str:
    """Build a synchronous TAP CSV URL from ADQL without hiding query parameters."""
    return f"{endpoint}?{urlencode({'query': query, 'format': 'csv'})}"


def download_catalogue(query: str = CATALOG_QUERY, timeout_seconds: int = 120) -> bytes:
    """Return the raw CSV response for the project's fixed TOI query."""
    with urlopen(tap_url(query), timeout=timeout_seconds) as response:
        return response.read()


def read_catalogue(raw_csv: bytes) -> pd.DataFrame:
    """Parse and minimally validate a raw TAP response."""
    catalogue = pd.read_csv(io.BytesIO(raw_csv))
    missing = set(REQUIRED_COLUMNS).difference(catalogue.columns)
    if missing:
        raise ValueError(f"TAP response is missing required columns: {sorted(missing)}")
    if catalogue["toi"].isna().any() or catalogue["tid"].isna().any():
        raise ValueError("TOI and TIC identifiers must be present for every row.")
    if catalogue["toi"].duplicated().any():
        raise ValueError("TOI identifiers must be unique in a frozen snapshot.")
    return catalogue


def prepare_supervised_catalogue(catalogue: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return labelled CP/FP/FA rows and KP rows, retaining every required column.

    A TIC can have several TOIs, so TIC uniqueness is *not* an invariant. Instead,
    the audit confirms that each TOI maps to exactly one TIC and reports multi-TOI TICs.
    """
    required = set(REQUIRED_COLUMNS)
    missing = required.difference(catalogue.columns)
    if missing:
        raise ValueError(f"Catalogue is missing required columns: {sorted(missing)}")

    frame = catalogue.loc[:, list(REQUIRED_COLUMNS)].copy()
    frame["tfopwg_disp"] = frame["tfopwg_disp"].fillna("").astype(str).str.upper().str.strip()
    if frame["toi"].duplicated().any():
        raise ValueError("TOI identifiers must be unique before labels are assigned.")

    supervised = frame.loc[frame.tfopwg_disp.isin(POSITIVE_DISPOSITIONS | NEGATIVE_DISPOSITIONS)].copy()
    supervised["label"] = supervised["tfopwg_disp"].map(
        lambda disposition: 1 if disposition in POSITIVE_DISPOSITIONS else 0
    ).astype("int8")
    supervised = supervised.sort_values(["toi"], kind="stable").reset_index(drop=True)
    known_planets = frame.loc[frame.tfopwg_disp.eq(KNOWN_PLANET_DISPOSITION)].copy()
    known_planets = known_planets.sort_values(["toi"], kind="stable").reset_index(drop=True)
    return supervised, known_planets


def audit_catalogue(catalogue: pd.DataFrame, supervised: pd.DataFrame) -> dict[str, object]:
    """Produce auditable counts without incorrectly requiring TIC IDs to be unique."""
    dispositions = catalogue["tfopwg_disp"].fillna("").astype(str).str.upper().str.strip()
    dispositions = dispositions.replace("", "MISSING")
    tic_multiplicity = catalogue.groupby("tid", dropna=False)["toi"].nunique()
    return {
        "source_rows": len(catalogue),
        "source_toi_unique": bool(catalogue["toi"].is_unique),
        "source_unique_tics": int(catalogue["tid"].nunique()),
        "source_tics_with_multiple_tois": int((tic_multiplicity > 1).sum()),
        "disposition_counts": {str(k): int(v) for k, v in dispositions.value_counts().sort_index().items()},
        "supervised_rows": len(supervised),
        "positive_rows": int((supervised["label"] == 1).sum()),
        "negative_rows": int((supervised["label"] == 0).sum()),
        "supervised_toi_unique": bool(supervised["toi"].is_unique),
        "supervised_unique_tics": int(supervised["tid"].nunique()),
    }


def freeze_catalogue(output_dir: Path, retrieved_on: date | None = None) -> dict[str, object]:
    """Download, audit, and write raw/labelled CSV files plus a provenance manifest."""
    raw_csv = download_catalogue()
    return freeze_raw_catalogue(raw_csv, output_dir, retrieved_on)


def freeze_raw_catalogue(
    raw_csv: bytes, output_dir: Path, retrieved_on: date | None = None
) -> dict[str, object]:
    """Freeze an already-downloaded response; useful for reproducible offline audits."""
    output_dir.mkdir(parents=True, exist_ok=True)
    retrieved_on = retrieved_on or datetime.now(UTC).date()
    catalogue = read_catalogue(raw_csv)
    supervised, known_planets = prepare_supervised_catalogue(catalogue)
    stamp = retrieved_on.isoformat()
    raw_path = output_dir / f"toi_catalogue_raw_{stamp}.csv"
    labels_path = output_dir / "labels_snapshot.csv"
    kp_path = output_dir / "known_planets_kp.csv"
    manifest_path = output_dir / "catalogue_manifest.json"
    raw_path.write_bytes(raw_csv)
    supervised.to_csv(labels_path, index=False)
    known_planets.to_csv(kp_path, index=False)
    manifest = {
        "retrieved_on": stamp,
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "source": "NASA Exoplanet Archive TAP toi table",
        "tap_endpoint": TAP_ENDPOINT,
        "format": "csv",
        "query_file": "toi_query.sql",
        "query": CATALOG_QUERY,
        "query_url": tap_url(),
        "raw_csv": raw_path.name,
        "raw_csv_sha256": hashlib.sha256(raw_csv).hexdigest(),
        "labels_snapshot": labels_path.name,
        "known_planets_snapshot": kp_path.name,
        "label_rule": "CP = 1; FP and FA = 0; PC/APC/KP excluded from supervised snapshot",
        "audit": audit_catalogue(catalogue, supervised),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Freeze the current NASA TOI catalogue.")
    parser.add_argument("--output-dir", type=Path, default=Path("data/metadata"))
    parser.add_argument("--retrieved-on", type=date.fromisoformat, default=None)
    parser.add_argument("--raw-csv", type=Path, default=None, help="Reuse an existing raw TAP CSV.")
    args = parser.parse_args()
    raw_csv = args.raw_csv.read_bytes() if args.raw_csv else download_catalogue()
    manifest = freeze_raw_catalogue(raw_csv, args.output_dir, args.retrieved_on)
    print(json.dumps(manifest["audit"], indent=2))


if __name__ == "__main__":
    main()
