"""Keep the browser sandbox's loopback origin aligned with the platform port."""

import os
import sys
from pathlib import Path

import uvicorn

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
port = int(os.environ.get("PORT", "8000"))
os.environ["JOB_AGENTS_BASE_URL"] = f"http://127.0.0.1:{port}"
uvicorn.run("job_agents.api:app", host="0.0.0.0", port=port, workers=1)
