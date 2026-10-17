"""Agent definitions must have a valid front matter: a bad one makes the agent vanish from the session."""
from pathlib import Path

AGENTS = sorted((Path(__file__).resolve().parents[1] / ".claude" / "agents").glob("*.md"))


def _front_matter(path: Path) -> dict:
    parts = path.read_text(encoding="utf-8").split("---")
    assert len(parts) >= 3, f"{path.name}: missing --- front matter"
    fields = {}
    for line in parts[1].strip().splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()
    return fields


def test_agent_front_matter_is_valid():
    assert AGENTS, "no agent files found"
    for path in AGENTS:
        fm = _front_matter(path)
        for required in ("name", "description", "tools", "model"):
            assert fm.get(required), f"{path.name}: missing {required}"
        assert fm["name"] == path.stem, f"{path.name}: name must match the file name"
        desc = fm["description"]
        quoted = desc[:1] in ("'", '"') and desc[-1:] == desc[:1]
        # an unquoted YAML value must not contain ': ' (this broke jira-collector)
        assert quoted or ": " not in desc, f"{path.name}: quote the description (contains ': ')"
