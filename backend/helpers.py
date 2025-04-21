import os
import json
import re
from typing import Any, Dict


def load_config_with_env(path: str) -> Dict[str, Any]:
    """
    Replace any ${VAR_NAME} with the value of the corresponding env var
    For example in servers_config.json: 
     "env": {
        "NPS_API_KEY": "${NPS_API_KEY}"
      }
    """
    with open(path, "r") as f:
        raw = f.read()

    substituted = re.sub(r"\$\{(\w+)\}", lambda m: os.getenv(m.group(1), ""), raw)

    return json.loads(substituted)
