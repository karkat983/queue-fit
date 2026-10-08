from src.config import ROOT, load_config, resolve


def test_config_has_service_and_sweep_sections():
    cfg = load_config()
    assert cfg["service"]["workers"] >= 1
    assert cfg["sweep"]["utilisations"] == sorted(cfg["sweep"]["utilisations"])


def test_resolve_is_relative_to_repo_root():
    assert resolve("results/raw") == ROOT / "results" / "raw"
