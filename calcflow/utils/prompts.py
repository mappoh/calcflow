import os


def ask(prompt, default=None, display_default=None):
    """Ask for string input with optional default."""
    shown = display_default if display_default is not None else default
    suffix = f" [{shown}]" if shown else ""
    while True:
        value = input(f"  {prompt}{suffix}: ").strip()
        if value:
            return value
        if default is not None:
            return default
        print("  Input required.")


def ask_int(prompt, default=None, min_val=None, max_val=None):
    """Ask for integer input with optional bounds."""
    suffix = f" [{default}]" if default is not None else ""
    while True:
        value = input(f"  {prompt}{suffix}: ").strip()
        if not value and default is not None:
            return default
        try:
            n = int(value)
        except ValueError:
            print("  Please enter a valid integer.")
            continue
        if min_val is not None and n < min_val:
            print(f"  Must be >= {min_val}.")
            continue
        if max_val is not None and n > max_val:
            print(f"  Must be <= {max_val}.")
            continue
        return n


def ask_float(prompt, default=None):
    """Ask for float input."""
    suffix = f" [{default}]" if default is not None else ""
    while True:
        value = input(f"  {prompt}{suffix}: ").strip()
        if not value and default is not None:
            return default
        try:
            return float(value)
        except ValueError:
            print("  Please enter a valid number.")


def ask_choice(prompt, choices, default=None):
    """Ask user to pick from a list of choices."""
    print(f"  {prompt}")
    for i, c in enumerate(choices, 1):
        marker = " *" if c == default else ""
        print(f"    {i}) {c}{marker}")
    suffix = f" [{default}]" if default else ""
    while True:
        value = input(f"  Choice{suffix}: ").strip()
        if not value and default:
            return default
        try:
            idx = int(value)
            if 1 <= idx <= len(choices):
                return choices[idx - 1]
        except ValueError:
            if value in choices:
                return value
        print(f"  Please enter 1-{len(choices)}.")


def ask_path(prompt, must_exist=True, default=None):
    """Ask for a file/directory path."""
    display = os.path.basename(default) if default else None
    suffix = f" [{display}]" if display else ""
    while True:
        value = input(f"  {prompt}{suffix}: ").strip()
        if not value and default:
            value = default
        if not value:
            print("  Path required.")
            continue
        value = os.path.expanduser(value)
        if must_exist and not os.path.exists(value):
            print(f"  Path not found: {value}")
            continue
        return value


def ask_yes_no(prompt, default=True):
    """Ask a yes/no question."""
    hint = "Y/n" if default else "y/N"
    while True:
        value = input(f"  {prompt} [{hint}]: ").strip().lower()
        if not value:
            return default
        if value in ("y", "yes"):
            return True
        if value in ("n", "no"):
            return False
        print("  Please enter y or n.")


def ask_incar_params():
    """Interactively collect VASP INCAR key=value pairs.

    Coerces values: .true./.false. -> bool, numbers with '.' or 'e' -> float,
    plain integers -> int, everything else -> str.
    """
    params = {}
    print("  Enter INCAR parameters one per line (e.g. ENCUT=520)")
    print("  Press Enter on an empty line when done.")
    while True:
        line = input("    > ").strip()
        if not line:
            break
        if "=" not in line:
            print("    Format: KEY=VALUE (e.g., ENCUT=520)")
            continue
        key, val = line.split("=", 1)
        key = key.strip().upper()
        val = val.strip()
        try:
            if val.lower() in ("true", ".true."):
                params[key] = True
            elif val.lower() in ("false", ".false."):
                params[key] = False
            elif "." in val or "e" in val.lower():
                params[key] = float(val)
            else:
                params[key] = int(val)
        except ValueError:
            params[key] = val
    return params
