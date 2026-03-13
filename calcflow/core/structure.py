import logging

from ase import Atoms
from ase.io import read, write

from calcflow import CalcFlowError


def get_structure_info(filepath):
    """
    Read a structure file and return a summary dict.

    Returns dict with: formula, n_atoms, symbols, cell_params, volume, pbc
    """
    try:
        atoms: Atoms = read(filepath, index=-1)  # type: ignore[assignment]
    except Exception as e:
        raise CalcFlowError(f"Failed to read structure from '{filepath}': {e}") from e

    cell = atoms.get_cell()
    lengths = cell.lengths()
    angles = cell.angles()

    return {
        "formula": atoms.get_chemical_formula(),
        "n_atoms": len(atoms),
        "symbols": list(set(atoms.get_chemical_symbols())),
        "cell_lengths": [round(x, 4) for x in lengths],
        "cell_angles": [round(x, 2) for x in angles],
        "volume": round(atoms.get_volume(), 4),
        "pbc": atoms.pbc.tolist(),
    }


def convert_structure(input_path, output_path):
    """Convert between structure formats. ASE infers format from extension."""
    try:
        atoms: Atoms = read(input_path, index=-1)  # type: ignore[assignment]
        write(output_path, atoms)
        logging.info("Converted %s -> %s", input_path, output_path)
    except Exception as e:
        raise CalcFlowError(f"Conversion failed: {e}") from e


def build_supercell(input_path, output_path, repeats):
    """
    Build a supercell from a structure file.

    Args:
        repeats: tuple of (nx, ny, nz) repetitions
    """
    try:
        atoms: Atoms = read(input_path, index=-1)  # type: ignore[assignment]
        supercell = atoms.repeat(repeats)
        write(output_path, supercell)
        logging.info(
            "Built %dx%dx%d supercell (%d atoms) -> %s",
            repeats[0], repeats[1], repeats[2], len(supercell), output_path
        )
    except Exception as e:
        raise CalcFlowError(f"Supercell build failed: {e}") from e
