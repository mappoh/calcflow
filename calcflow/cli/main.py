import os
import sys
import builtins
import importlib
from calcflow import CalcFlowError
from calcflow.cli.display import (
    print_banner, print_top_menu, print_category_submenu,
    print_full_help, print_workspace_summary, get_menu_mapping,
)
from calcflow.cli.registry import CATEGORY_OPTIONS
from calcflow.config.settings import get_config
from calcflow.presets.manager import init_user_presets
from calcflow.core.workspace import scan_structures, scan_vasp_outputs, scan_subdirectories
from calcflow.utils.logging import setup_logging


# Session state carried between menu choices
_session = {}

# Tracks how many lines CalcFlow has printed since last clear
_line_count = 0
_original_write = None


def _install_line_counter():
    """Wrap stdout.write and input to count all lines CalcFlow produces."""
    global _original_write
    if _original_write is not None:
        return  # already installed
    _original_write = sys.stdout.write
    _original_input = builtins.input

    def _counting_write(text):
        global _line_count
        _line_count += text.count("\n")
        return _original_write(text)

    def _counting_input(prompt=""):
        global _line_count
        result = _original_input(prompt)
        _line_count += 1  # terminal echoes a newline when user presses Enter
        return result

    sys.stdout.write = _counting_write
    builtins.input = _counting_input


def _erase_lines():
    """Erase exactly the lines CalcFlow printed, leaving prior terminal content."""
    global _line_count
    if _line_count > 0 and sys.stdout.isatty():
        # Move up and clear each line we printed
        _original_write(f"\033[{_line_count}A\033[J")
        sys.stdout.flush()
    _line_count = 0


def _reset_counter():
    """Reset the line counter without erasing."""
    global _line_count
    _line_count = 0


def _setup_workspace(directory=None):
    """Initialize or change the working directory and scan for files."""
    if directory is None:
        directory = os.getcwd()

    abs_dir = os.path.abspath(directory)
    _session["work_dir"] = abs_dir
    _session["work_dir_name"] = os.path.basename(abs_dir) or abs_dir
    _session["structure_files"] = scan_structures(directory)
    _session["vasp_outputs"] = scan_vasp_outputs(directory)
    _session["subdirs"] = scan_subdirectories(directory)

    # Auto-set last_poscar if exactly one structure file found
    if len(_session["structure_files"]) == 1:
        _session["last_poscar"] = _session["structure_files"][0]
    # Set last_calc_dir to work_dir by default
    _session["last_calc_dir"] = _session["work_dir"]


def _choose_workspace():
    """Show current directory contents and ask user to confirm or exit."""
    cwd = os.getcwd()
    dir_name = os.path.basename(cwd) or cwd

    print(f"  Current working directory: {dir_name}")

    # List directory contents in compact columns
    try:
        entries = sorted(os.scandir(cwd), key=lambda e: e.name)
        if entries:
            names = []
            for entry in entries:
                names.append(f"{entry.name}/" if entry.is_dir() else entry.name)
            # Format into wrapped lines with "Contents:" label
            label = "  Contents: "
            indent = " " * len(label)
            max_width = 72
            lines = []
            current = label
            for name in names:
                addition = name + "  "
                if len(current) + len(addition) > max_width and current.strip():
                    lines.append(current.rstrip())
                    current = indent + addition
                else:
                    current += addition
            if current.strip():
                lines.append(current.rstrip())
            print("\n".join(lines))
        else:
            print("  Contents: (empty directory)")
    except PermissionError:
        print("  Contents: (unable to read directory)")

    print()

    try:
        choice = input("  Proceed with this directory? (y/n): ").strip().lower()
    except (KeyboardInterrupt, EOFError) as exc:
        _erase_lines()
        raise SystemExit(0) from exc

    if choice in ("y", "yes", ""):
        _erase_lines()
        _setup_workspace(cwd)
    else:
        _erase_lines()
        raise SystemExit(0)


def _show_main_page():
    """Display workspace summary and main menu together."""
    _reset_counter()
    print_banner()
    print_workspace_summary(_session)
    print_top_menu(_session)


def _dispatch(category_id, option_index):
    """Resolve and call the handler for a category option."""
    options = CATEGORY_OPTIONS.get(category_id, [])
    if option_index < 0 or option_index >= len(options):
        print("  Invalid option.")
        return

    entry = options[option_index]
    module_path, func_name = entry["handler"].rsplit(":", 1)
    module = importlib.import_module(module_path)
    handler = getattr(module, func_name)

    # Show banner, working directory, and current task before every handler
    _reset_counter()
    print_banner()
    dir_name = _session.get("work_dir_name", "")
    if dir_name:
        print(f"  Working directory: {dir_name}")
    print(f"  Task: {entry['label']}")

    try:
        handler(_session)
    except KeyboardInterrupt:
        print("\n  Interrupted. Returning to menu.")
    except CalcFlowError as e:
        print(f"\n  Error: {e}")


def run():
    """Main entry point for CalcFlow."""
    setup_logging()
    _install_line_counter()

    # Ensure config and user presets exist
    get_config()
    init_user_presets()

    print_banner()

    # Step 1: Choose working directory
    _choose_workspace()

    # Step 2: Show what was found and main menu
    _show_main_page()

    # Step 3: Main menu loop
    while True:
        try:
            raw = input("  >>> ").strip()
        except (KeyboardInterrupt, EOFError):
            _erase_lines()
            break

        if raw.lower() in ("q", "quit", "exit"):
            _erase_lines()
            break

        if raw == "0":
            _erase_lines()
            print_banner()
            print_full_help(_session)
            input("  Press Enter to return...")
            _erase_lines()
            _show_main_page()
            continue

        try:
            code = int(raw)
        except ValueError:
            _erase_lines()
            _show_main_page()
            continue

        mapping = get_menu_mapping(_session)
        if code in mapping:
            cat_id = mapping[code]
            _erase_lines()
            _handle_category(cat_id)
            _erase_lines()
            _show_main_page()
        else:
            _erase_lines()
            _show_main_page()


def _handle_category(category_id):
    """Show submenu for a category and handle selection."""
    options = CATEGORY_OPTIONS.get(category_id, [])

    while True:
        _reset_counter()
        print_banner()
        print_category_submenu(category_id, _session)
        try:
            raw = input("  >>> ").strip()
        except (KeyboardInterrupt, EOFError):
            print()
            break

        if raw.lower() in ("q", "quit", "exit"):
            _erase_lines()
            raise SystemExit(0)

        if raw == "0" or raw.lower() in ("b", "back"):
            break

        try:
            choice = int(raw)
        except ValueError:
            _erase_lines()
            continue

        if 1 <= choice <= len(options):
            _erase_lines()
            _dispatch(category_id, choice - 1)
            _erase_lines()
        else:
            _erase_lines()
