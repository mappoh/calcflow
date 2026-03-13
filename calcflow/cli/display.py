import os

from calcflow import __version__
from calcflow.cli.registry import (
    CATEGORY_LABELS, CATEGORY_OPTIONS, get_available_categories,
)

BANNER = f"""
 =============================================
         CalcFlow  v{__version__}
   Interactive VASP Workflow Manager
 =============================================
"""

SEP = " ---------------------------------------------"


def print_banner():
    print(BANNER)


def print_workspace_summary(session):
    """Display the current working directory and detected files."""
    work_dir = session.get("work_dir", os.getcwd())
    structures = session.get("structure_files", [])
    outputs = session.get("vasp_outputs", [])
    subdirs = session.get("subdirs", [])

    dir_name = session.get("work_dir_name", os.path.basename(work_dir) or work_dir)

    print(SEP)
    print(f"  Working directory: {dir_name}")
    print()

    if structures:
        print(f"  Structure files found ({len(structures)}):")
        for i, path in enumerate(structures, 1):
            print(f"    {i}. {os.path.basename(path)}")
    else:
        print("  No structure files found in this directory.")

    if outputs:
        print(f"\n  VASP outputs detected: {', '.join(outputs)}")

    if subdirs:
        print(f"\n  Subdirectories with calculations ({len(subdirs)}):")
        for sd in subdirs:
            out_str = f" [{', '.join(sd['outputs'])}]" if sd['outputs'] else ""
            print(f"    - {sd['name']}/  ({sd['structures']} structures){out_str}")

    print(SEP)
    print()


def get_menu_mapping(session):
    """Build a mapping from display number (1,2,3...) to actual category ID."""
    available = get_available_categories(session)
    return dict(enumerate(available, 1))


def print_top_menu(session):
    """Print the main menu with sequential numbering for available categories."""
    mapping = get_menu_mapping(session)

    print(SEP)
    print("  0)  Summary of All Options")
    print()
    for display_num, cat_id in mapping.items():
        print(f"  {display_num})  {CATEGORY_LABELS[cat_id]}")
    print()
    print("  q)  Quit")
    print(SEP)


def print_category_submenu(category_id, session=None):
    """Print options within a category as simple 1, 2, 3... numbering."""
    label = CATEGORY_LABELS.get(category_id, "Unknown")
    options = CATEGORY_OPTIONS.get(category_id, [])

    if session:
        dir_name = session.get("work_dir_name", "")
        if dir_name:
            print(f"  Working directory: {dir_name}")
    print()
    print(f"  === {label} ===")
    print()
    if not options:
        print("  (No options available yet)")
    else:
        for i, opt in enumerate(options, 1):
            print(f"  {i})  {opt['label']}")
    print()
    print("  0)  Back to main menu")
    print("  q)  Quit")
    print()


def print_full_help(session):
    """Print all categories and their options."""
    mapping = get_menu_mapping(session)

    dir_name = session.get("work_dir_name", "")
    if dir_name:
        print(f"  Working directory: {dir_name}")
    print()
    print("  ========== All Available Options ==========")
    for display_num, cat_id in mapping.items():
        print()
        print(f"  --- {display_num}) {CATEGORY_LABELS[cat_id]} ---")
        options = CATEGORY_OPTIONS.get(cat_id, [])
        for i, opt in enumerate(options, 1):
            print(f"    {i})  {opt['label']}")
            if opt.get("description"):
                print(f"        {opt['description']}")
    print()
