import json
import pathlib
from typing import Dict, Any, Optional

from jinja2 import Template


class SoarEngine:
    """Simple SOAR engine that loads and executes JSON playbooks."""

    def __init__(self, playbook_dir: pathlib.Path) -> None:
        self.playbook_dir = playbook_dir
        self.playbooks: Dict[str, Dict[str, Any]] = {}
        self._load_playbooks()

    def _load_playbooks(self) -> None:
        for path in self.playbook_dir.glob("*.json"):
            with path.open() as fh:
                data = json.load(fh)
            self.playbooks[path.stem] = data

    def execute(self, name: str, **params: Any) -> None:
        """Run the playbook ``name`` with ``params``."""
        playbook = self.playbooks.get(name)
        if not playbook:
            print(f"[SOAR] Playbook '{name}' not found")
            return
        workflow = playbook.get("workflow", {})
        blocks = workflow.get("blocks", {})
        current: Optional[str] = workflow.get("start")
        while current:
            block = blocks.get(current)
            if block is None:
                print(f"[SOAR] Unknown block '{current}' in playbook '{name}'")
                break
            description = block.get("description", "")
            action = block.get("action", {})
            command_tpl = Template(action.get("command", ""))
            command = command_tpl.render(**params)
            print(f"[SOAR] {description}")
            print(f"[SOAR] Executing: {command}")
            next_blocks = block.get("next", [])
            current = next_blocks[0] if next_blocks else None

    # Convenience wrappers for common playbooks
    def response(self, host: str) -> None:
        self.execute("response", host=host)

    def elimination(self, host: str) -> None:
        self.execute("elimination", host=host)

    def recovery(self, host: str) -> None:
        self.execute("recovery", host=host)


__all__ = ["SoarEngine"]
