"""Export StateMachine JSON Schema.

Usage:
    python scripts/export_state_machine_schema.py [output_path]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from irms.models.state_machine import state_machine_json_schema


def main() -> None:
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("schemas/state_machine.schema.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(state_machine_json_schema(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(output)


if __name__ == "__main__":
    main()
