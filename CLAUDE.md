# IO Project Assistant

Python project packaged as a Claude Code plugin. This repo is also its marketplace (`sectigo-io-tools`).

## Structure

- .claude-plugin/marketplace.json - marketplace listing
- plugins/ioproject-assistant/ - the plugin (what users install)
  - .claude-plugin/plugin.json - manifest; bump `version` on every release
  - agents/ - subagents (launched as `ioproject-assistant:<name>`)
  - skills/ - skills (`ioproject-assistant:<name>`); `run-report` and `setup` are the user entry points
  - src/ioassistant/ - application code (standard library only)
  - config/ - pricing.json, defaults.env (non-secret settings)
- tests/ - pytest tests (conftest.py puts the plugin's src/ on the path)
- docs/PLUGIN_GUIDE.md - sharing and end-user guide
- output/ - local report runs (not part of the plugin)

In agent and skill text, refer to plugin files as `${CLAUDE_PLUGIN_ROOT}/...` and run Python as `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python -m ioassistant.cli ...`. Do not add a top-level `bin/` to the plugin: claude.ai organization sync rejects it.

## Setup

```bash
pip install -r requirements.txt
python -m pytest
claude plugin validate plugins/ioproject-assistant --strict
claude --plugin-dir plugins/ioproject-assistant   # try local changes
```

Tokens live outside the repo in ~/.ioassistant/secrets.env. A .env in the working folder overrides plugins/ioproject-assistant/config/defaults.env.
