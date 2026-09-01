"""Public deployment entry point for the Streamlit app.

Streamlit reruns this file after every widget interaction.  Execute the real
app script on every rerun instead of importing it, because Python's module
cache would otherwise make every rerun after the first render a blank page.
"""

import importlib
import sys
from pathlib import Path
from runpy import run_path


# Streamlit Cloud may rerun the entry script inside an existing Python process
# after a deployment. Drop local app modules so main.py and product_logic.py
# always come from the same deployed revision.
importlib.invalidate_caches()
for module_name in ("app.main", "app.product_logic", "app.coze_client"):
    sys.modules.pop(module_name, None)

run_path(str(Path(__file__).parent / "app" / "main.py"), run_name="__main__")
