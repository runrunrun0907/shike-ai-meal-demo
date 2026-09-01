"""Public deployment entry point for the Streamlit app.

Streamlit reruns this file after every widget interaction.  Execute the real
app script on every rerun instead of importing it, because Python's module
cache would otherwise make every rerun after the first render a blank page.
"""

from pathlib import Path
from runpy import run_path


run_path(str(Path(__file__).parent / "app" / "main.py"), run_name="__main__")
