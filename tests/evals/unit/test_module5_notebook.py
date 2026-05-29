import json
import re
from pathlib import Path

from llm_ops_v1.economics.local_models import LOCAL_MODELS

NOTEBOOK_PATH = Path("notebooks/notebook-llm-ops.ipynb")
LOCAL_MODEL_CALL_PATTERN = re.compile(r'estimate_local_infra_cost\("([^"]+)"')


def _load_notebook() -> dict:
    return json.loads(NOTEBOOK_PATH.read_text())


def _code_sources(notebook: dict) -> list[str]:
    return ["".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "code"]


def test_module5_companion_notebook_exists() -> None:
    assert NOTEBOOK_PATH.exists()


def test_module5_companion_notebook_cells_import_package() -> None:
    notebook = _load_notebook()
    code_sources = _code_sources(notebook)

    assert code_sources
    assert all(
        "from llm_ops_v1" in source or "import llm_ops_v1" in source or "SRC_PATH" in source
        for source in code_sources
    )


def test_module5_companion_notebook_uses_known_local_models() -> None:
    notebook = _load_notebook()
    model_ids = {
        model_id
        for source in _code_sources(notebook)
        for model_id in LOCAL_MODEL_CALL_PATTERN.findall(source)
    }

    assert model_ids
    assert model_ids <= set(LOCAL_MODELS)


def test_module5_companion_notebook_imports_caching_module() -> None:
    notebook = _load_notebook()
    code_sources = "\n".join(_code_sources(notebook))

    assert "from llm_ops_v1.caching import estimate_support_triage_cache_demo" in code_sources
    assert "estimate_support_triage_cache_demo(" in code_sources


def test_module5_companion_notebook_shows_before_after_cache_costs() -> None:
    notebook = _load_notebook()
    code_sources = "\n".join(_code_sources(notebook))

    assert '"uncached_cost_usd"' in code_sources
    assert '"cached_cost_usd"' in code_sources
    assert '"savings_usd"' in code_sources
    assert '"savings_pct"' in code_sources


def test_module5_companion_notebook_explains_streamlit_and_langfuse() -> None:
    notebook = _load_notebook()
    markdown_sources = "\n".join(
        "".join(cell["source"]) for cell in notebook["cells"] if cell["cell_type"] == "markdown"
    )

    assert "dove entra Streamlit" in markdown_sources
    assert "dove entra Langfuse" in markdown_sources
    assert "notebook = walkthrough" in markdown_sources
