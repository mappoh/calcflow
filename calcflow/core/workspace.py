import os

# Suffixes ASE can read that are relevant for VASP workflows
_STRUCTURE_SUFFIXES = (".vasp", ".cif", ".xyz", ".xsd", ".gen")

# Exact names and prefix patterns for VASP structure files
_STRUCTURE_PREFIXES = ("POSCAR", "CONTCAR")

# VASP output files that indicate a completed/running calculation
VASP_OUTPUT_FILES = ("OUTCAR", "OSZICAR", "CHGCAR", "WAVECAR", "vasprun.xml")


def _is_structure_file(name):
    """Check if a filename matches known structure file patterns."""
    if any(name.endswith(s) for s in _STRUCTURE_SUFFIXES):
        return True
    for prefix in _STRUCTURE_PREFIXES:
        if name.startswith(prefix):
            return True
    return False


def scan_structures(directory):
    """
    Scan a directory for structure files.
    Returns a sorted list of absolute file paths.
    """
    try:
        entries = os.scandir(directory)
    except (OSError, PermissionError):
        return []

    found = []
    for entry in entries:
        if entry.is_file() and _is_structure_file(entry.name):
            found.append(entry.path)

    return sorted(found)


def scan_vasp_outputs(directory):
    """Check which VASP output files exist in a directory."""
    return [f for f in VASP_OUTPUT_FILES if os.path.exists(os.path.join(directory, f))]


def scan_subdirectories(directory):
    """
    Scan for subdirectories that contain structure files.
    Useful when user has multiple calculations in one parent directory.
    """
    subdirs = []
    try:
        entries = sorted(os.scandir(directory), key=lambda e: e.name)
    except (OSError, PermissionError):
        return subdirs
    for entry in entries:
        if entry.is_dir():
            structures = scan_structures(entry.path)
            outputs = scan_vasp_outputs(entry.path)
            if structures or outputs:
                subdirs.append({
                    "name": entry.name,
                    "path": entry.path,
                    "structures": len(structures),
                    "outputs": outputs,
                })
    return subdirs
