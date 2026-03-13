import importlib

from calcflow.cli.registry import (
    CATEGORY_LABELS, CATEGORY_OPTIONS, CATEGORIES_REQUIRING_STRUCTURES,
    get_available_categories,
)


def test_all_handlers_importable():
    """Verify every handler string in the registry resolves to a callable."""
    for cat_id, options in CATEGORY_OPTIONS.items():
        for opt in options:
            module_path, func_name = opt["handler"].rsplit(":", 1)
            module = importlib.import_module(module_path)
            handler = getattr(module, func_name)
            assert callable(handler), (
                f"Handler not callable: {opt['handler']} in category {cat_id}"
            )


def test_all_categories_have_options():
    """Every category in CATEGORY_LABELS has at least one option."""
    for cat_id in CATEGORY_LABELS:
        options = CATEGORY_OPTIONS.get(cat_id, [])
        assert len(options) > 0, f"Category {cat_id} has no options"


def test_available_categories_with_structures():
    """All categories available when structures exist."""
    session = {"structure_files": ["POSCAR"]}
    available = get_available_categories(session)
    for cat_id in CATEGORY_LABELS:
        assert cat_id in available


def test_available_categories_without_structures():
    """Structure-requiring categories hidden when no structures."""
    session = {"structure_files": []}
    available = get_available_categories(session)
    for cat_id in CATEGORIES_REQUIRING_STRUCTURES:
        assert cat_id not in available
    # Non-structure categories should still be available
    for cat_id in CATEGORY_LABELS:
        if cat_id not in CATEGORIES_REQUIRING_STRUCTURES:
            assert cat_id in available
