"""The contract the README makes about the notebooks, enforced.

"The notebooks are committed unexecuted, with no saved outputs." That was true by
habit and by nothing else. It is a test now, so the first commit that breaks it says so.
"""

from pathlib import Path

import nbformat
import pytest

ROOT = Path(__file__).resolve().parent.parent
NOTEBOOKS = sorted(ROOT.glob("lab_*/*.ipynb"))


def test_every_lab_has_its_notebooks():
    assert len(NOTEBOOKS) == 8, [path.name for path in NOTEBOOKS]


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.stem)
def test_notebook_is_valid_and_unexecuted(path):
    notebook = nbformat.read(path, as_version=4)
    nbformat.validate(notebook)
    for number, cell in enumerate(notebook.cells):
        if cell.cell_type != "code":
            continue
        assert not cell.get("outputs"), f"cell {number} has saved output"
        assert cell.get("execution_count") is None, f"cell {number} has an execution count"
