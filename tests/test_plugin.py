"""Plugin packaging: manifests, layout and references that only work inside the plugin."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "ioproject-assistant"
MARKDOWN = sorted(PLUGIN.glob("agents/*.md")) + sorted(PLUGIN.glob("skills/*/SKILL.md"))


def test_manifests_point_at_the_plugin():
    manifest = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    assert manifest["name"] == "ioproject-assistant"
    entry = next(p for p in market["plugins"] if p["name"] == manifest["name"])
    assert (ROOT / entry["source"]).resolve() == PLUGIN.resolve()


def test_skill_front_matter_is_valid():
    for skill in PLUGIN.glob("skills/*/SKILL.md"):
        text = skill.read_text(encoding="utf-8")
        assert f"\nname: {skill.parent.name}\n" in text, skill
        desc = re.search(r"^description: (.*)$", text, re.M).group(1)
        quoted = desc[:1] in ("'", '"') and desc[-1:] == desc[:1]
        # an unquoted ': ' breaks the YAML and the skill loads with no metadata
        assert quoted or ": " not in desc, f"{skill}: quote the description"


def test_no_bin_folder():
    # claude.ai organization plugin sync rejects plugins with a top-level bin/
    assert not (PLUGIN / "bin").exists()


def test_no_repo_relative_paths_left():
    for path in MARKDOWN:
        text = path.read_text(encoding="utf-8")
        assert "PYTHONPATH=src" not in text, path
        assert ".claude/skills" not in text and ".claude/agents" not in text, path
        assert not re.search(r"(?<![/{])python -m ioassistant", text.replace('PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python', "")), path


def test_orchestrator_launches_namespaced_agents():
    text = (PLUGIN / "agents" / "orchestrator.md").read_text(encoding="utf-8")
    assert 'subagent_type: "ioproject-assistant:<name>"' in text
    agents = {p.stem for p in PLUGIN.glob("agents/*.md")} - {"orchestrator"}
    for name in agents:
        assert f"`{name}`" in text, f"orchestrator never launches {name}"
