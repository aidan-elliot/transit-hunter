"""Create machine-readable records for every reproducible project run."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import subprocess
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path

TRACKED_PACKAGES = ("numpy", "pandas", "scikit-learn", "torch", "lightkurve", "astropy")


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a file without loading it all into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def package_versions(packages: Iterable[str] = TRACKED_PACKAGES) -> dict[str, str | None]:
    """Record installed versions while allowing optional dependencies to be absent."""
    versions: dict[str, str | None] = {}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    return versions


def git_revision(repository_root: Path) -> str | None:
    """Return the current commit when Git metadata is available, otherwise ``None``."""
    result = subprocess.run(
        ["git", "-C", str(repository_root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def write_run_manifest(
    output_dir: Path,
    *,
    command: str,
    config_paths: Iterable[Path],
    input_paths: Iterable[Path],
    seed: int,
    repository_root: Path | None = None,
) -> Path:
    """Write a provenance manifest alongside a generated run's outputs."""
    output_dir.mkdir(parents=True, exist_ok=True)
    repository_root = (repository_root or Path.cwd()).resolve()
    config_paths = [Path(path).resolve() for path in config_paths]
    input_paths = [Path(path).resolve() for path in input_paths]
    missing = [str(path) for path in [*config_paths, *input_paths] if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Cannot create run manifest; missing files: {missing}")

    manifest = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "command": command,
        "seed": seed,
        "git_revision": git_revision(repository_root),
        "config_files": {str(path): sha256_file(path) for path in config_paths},
        "input_files": {str(path): sha256_file(path) for path in input_paths},
        "package_versions": package_versions(),
    }
    destination = output_dir / "run_manifest.json"
    destination.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return destination
