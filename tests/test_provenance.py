import json

from transit_hunter.provenance import sha256_file, write_run_manifest


def test_run_manifest_records_input_and_configuration_hashes(tmp_path) -> None:
    config = tmp_path / "config.yaml"
    source = tmp_path / "labels.csv"
    config.write_text("seed: 4000\n", encoding="utf-8")
    source.write_text("toi,label\n1.01,1\n", encoding="utf-8")

    manifest_path = write_run_manifest(
        tmp_path / "run",
        command="pytest smoke",
        config_paths=[config],
        input_paths=[source],
        seed=4000,
        repository_root=tmp_path,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["seed"] == 4000
    assert manifest["config_files"][str(config.resolve())] == sha256_file(config)
    assert manifest["input_files"][str(source.resolve())] == sha256_file(source)
