"""Create a confirmed, fictional test account without embedding credentials in source."""

import argparse
import getpass
import json
import os
import secrets
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from job_agents.storage import Store  # noqa: E402

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output", type=Path, required=True, help="Private credentials output file")
args = parser.parse_args()
url = os.environ.get("SUPABASE_URL", "").rstrip("/")
database_url = os.environ.get("DATABASE_URL")
if not url.startswith("https://") or not database_url:
    parser.error("Set SUPABASE_URL and DATABASE_URL in your local environment first.")
if args.output.exists():
    parser.error("Output file already exists; choose a new private path.")
key = getpass.getpass("One-time Supabase admin secret/service-role key: ")
password = secrets.token_urlsafe(24)
email = "test@applypilot.example"
response = httpx.post(
    url + "/auth/v1/admin/users",
    timeout=30,
    headers={"apikey": key, "Authorization": "Bearer " + key},
    json={
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {"full_name": "Alex Morgan — Test Account"},
    },
)
if response.status_code not in (200, 201):
    raise SystemExit(
        f"Account creation failed (HTTP {response.status_code}). "
        "Check the admin key or whether this test email already exists."
    )
user_id = response.json()["id"]
profile = json.loads(
    (Path(__file__).resolve().parent.parent / "examples/applicant.json").read_text()
)
profile.update(id="default", email=email)
args.output.parent.mkdir(parents=True, exist_ok=True)
fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, "w") as output:
    json.dump(
        {
            "website": "https://job-application-agents.onrender.com/login",
            "email": email,
            "password": password,
        },
        output,
        indent=2,
    )
try:
    Store(Path("runtime"), database_url).save_profile("user:" + user_id, profile)
except Exception:
    print("The account was created, but its sample profile could not be saved. Use My profile.")
print(f"Confirmed test account created. Credentials saved privately to {args.output}.")
