"""Make the plugin's Python package importable without installing it."""
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1] / "plugins" / "ioproject-assistant"
sys.path.insert(0, str(PLUGIN / "src"))
