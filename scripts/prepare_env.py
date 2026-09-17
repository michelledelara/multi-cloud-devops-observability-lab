"""Create a local-only Grafana password without overwriting an existing .env."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
path = root / ".env"
if path.exists():
    print(".env already exists; preserved.")
else:
    with path.open("x", encoding="utf-8") as stream:
        stream.write(f"GRAFANA_ADMIN_PASSWORD={secrets.token_urlsafe(32)}\nENABLE_FAULTS=false\n")
    path.chmod(0o600)
    print("Created .env. Grafana user: admin. Read your password locally from .env.")
