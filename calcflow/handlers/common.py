import os

from calcflow.utils.prompts import ask_path, ask_yes_no


def pick_structure(session, prompt="Structure file"):
    """Pick a single structure file from detected files or ask for path."""
    structures = session.get("structure_files", [])
    default = session.get("last_poscar")

    if len(structures) == 1:
        chosen = structures[0]
        print(f"\n  {prompt}: {os.path.basename(chosen)}")
        session["last_poscar"] = chosen
        return chosen

    if len(structures) > 1:
        print(f"\n  {prompt} — select from available files:")
        for i, path in enumerate(structures, 1):
            marker = " *" if path == default else ""
            print(f"    {i}) {os.path.basename(path)}{marker}")
        print()
        while True:
            raw = input("  Enter #: ").strip()
            if not raw and default:
                return default
            try:
                idx = int(raw)
                if 1 <= idx <= len(structures):
                    session["last_poscar"] = structures[idx - 1]
                    return structures[idx - 1]
            except ValueError:
                pass
            expanded = os.path.expanduser(raw)
            if os.path.exists(expanded):
                session["last_poscar"] = expanded
                return expanded
            print("  Invalid selection.")
    else:
        path = ask_path(prompt, default=default)
        session["last_poscar"] = path
        return path


def pick_structures(session):
    """Pick one or more structure files. Returns a list of paths."""
    structures = session.get("structure_files", [])

    if len(structures) <= 1:
        return [pick_structure(session)]

    # Multiple structures found — offer batch option
    print(f"\n  Found {len(structures)} structure files:")
    for i, path in enumerate(structures, 1):
        print(f"    {i}) {os.path.basename(path)}")
    print()

    if ask_yes_no("Run on all structure files (batch mode)?", default=False):
        return structures

    # Let user pick specific files
    print("  Enter file numbers separated by commas (e.g. 1,3,5) or a single number:")
    while True:
        raw = input("  Selection: ").strip()
        if not raw:
            continue
        try:
            indices = [int(x.strip()) for x in raw.split(",")]
            selected = []
            valid = True
            for idx in indices:
                if 1 <= idx <= len(structures):
                    selected.append(structures[idx - 1])
                else:
                    print(f"  {idx} is out of range.")
                    valid = False
                    break
            if valid and selected:
                if len(selected) == 1:
                    session["last_poscar"] = selected[0]
                return selected
        except ValueError:
            pass
        print(f"  Please enter numbers between 1 and {len(structures)}.")


def pick_calc_dir(session, prompt="Calculation directory"):
    """Pick a calculation directory, defaulting to work_dir."""
    default = session.get("last_calc_dir", session.get("work_dir", os.getcwd()))
    calc_dir = ask_path(prompt, default=default)
    session["last_calc_dir"] = calc_dir
    return calc_dir
