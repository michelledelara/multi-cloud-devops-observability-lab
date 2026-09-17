"""Parse repository configuration and check cross-file references."""
import json
from pathlib import Path
import hcl2
import yaml

class ConfigLoader(yaml.SafeLoader):
    pass


ConfigLoader.add_constructor("!override", lambda loader, node: loader.construct_sequence(node))

root = Path(__file__).resolve().parents[1]
files = [p for p in root.rglob("*") if p.is_file() and not any(
    part in {".venv", ".terraform", ".git", ".lab-managed"} for part in p.parts)]
counts = {"yaml": 0, "json": 0, "hcl": 0}
for path in files:
    if path.suffix in {".yaml", ".yml"}:
        list(yaml.load_all(path.read_text(), Loader=ConfigLoader))
        counts["yaml"] += 1
    elif path.suffix == ".json":
        json.loads(path.read_text())
        counts["json"] += 1
    elif path.suffix == ".tf":
        with path.open() as stream:
            hcl2.load(stream)
        counts["hcl"] += 1
kustomize = yaml.safe_load((root / "kustomization.yaml").read_text())
for source in kustomize["resources"]:
    assert (root / source).is_file(), source
for config in kustomize["configMapGenerator"]:
    for source in config.get("files", []):
        assert (root / source.split("=", 1)[-1]).is_file(), source
compose = yaml.safe_load((root / "compose.yaml").read_text())
for service in compose["services"].values():
    for volume in service.get("volumes", []):
        source = volume.split(":", 1)[0]
        if source.startswith("./"):
            assert (root / source).exists(), source
print("Configuration parsing and references:", counts)
