import os
import re
import subprocess
import logging

import numpy as np
from ase import Atoms
from ase.io import read

from calcflow import CalculationError


def build_chgsum(directory):
    """Run chgsum.pl (Henkelman group) to sum AECCAR0 and AECCAR2."""
    try:
        subprocess.run(
            ["chgsum.pl", "AECCAR0", "AECCAR2"],
            cwd=directory, check=True, capture_output=True,
        )
        logging.info("chgsum.pl completed successfully.")
    except subprocess.CalledProcessError as e:
        raise CalculationError(f"chgsum.pl failed: {e.stderr.decode()}") from e


def run_bader(directory):
    """Run bader analysis using CHGCAR and CHGCAR_sum."""
    try:
        subprocess.run(
            ["bader", "CHGCAR", "-ref", "CHGCAR_sum"],
            cwd=directory, check=True, capture_output=True,
        )
        logging.info("Bader analysis completed successfully.")
    except subprocess.CalledProcessError as e:
        raise CalculationError(f"Bader analysis failed: {e.stderr.decode()}") from e


def cut_acf_file(directory, first_wanted_column=7):
    """Parse ACF.dat and write a simplified version with selected columns."""
    fname = os.path.join(directory, "ACF.dat")

    if not os.path.exists(fname):
        raise CalculationError(f"ACF.dat not found in {directory}")

    with open(fname, "r", encoding="utf-8") as f:
        lines = f.readlines()

    filtered = []
    for line in lines:
        if len(line) > 4 and line[4].isdigit():
            filtered.append("\t".join(line.split()[:first_wanted_column]))

    out_path = os.path.join(directory, "ACF_small.dat")
    with open(out_path, "w", encoding="utf-8") as g:
        g.write("\n".join(filtered) + "\n" if filtered else "")

    logging.info("Wrote simplified ACF data to %s", out_path)


def compute_bader_charges(directory):
    """
    Compute per-atom Bader charges from ACF_small.dat, CONTCAR, and POTCAR.

    Returns list of dicts: [{"element": "O", "charge": -1.23}, ...]
    """
    atoms: Atoms = read(os.path.join(directory, "CONTCAR"), index=-1)  # type: ignore[assignment]
    matrix = np.loadtxt(os.path.join(directory, "ACF_small.dat"))
    symbols = atoms.get_chemical_symbols()

    # Derive unique element order from symbols (preserving first-appearance order)
    unique_elements = list(dict.fromkeys(symbols))

    # Extract ZVAL from POTCAR
    potcar_path = os.path.join(directory, "POTCAR")
    zval_pattern = re.compile(r"ZVAL\s*=\s*([\d.]+)")
    zval_values = []
    with open(potcar_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            match = zval_pattern.search(line)
            if match:
                zval_values.append(float(match.group(1)))

    zval_map = {}
    for i, elem in enumerate(unique_elements):
        zval_map[elem] = zval_values[i]

    # Compute charges
    results = []
    for i, elem in enumerate(symbols):
        bader_charge = zval_map[elem] - matrix[i, 4]
        results.append({"element": elem, "charge": bader_charge})

    return results


def run_bader_analysis(calc_dir, last_step_only=False):
    """
    Full Bader analysis workflow.

    Args:
        calc_dir: Directory containing VASP output files
        last_step_only: If True, skip chgsum/bader and just parse existing results

    Returns:
        List of per-atom charge dicts
    """
    if not last_step_only:
        logging.info("Running complete Bader analysis...")
        build_chgsum(calc_dir)
        run_bader(calc_dir)

    cut_acf_file(calc_dir)
    charges = compute_bader_charges(calc_dir)

    # Write results
    out_path = os.path.join(calc_dir, "BaderCharge.dat")
    with open(out_path, "w", encoding="utf-8") as f:
        for entry in charges:
            f.write(f"Atom {entry['element']} Bader charge {entry['charge']}\n")

    logging.info("Bader charges written to %s", out_path)

    # Log summary
    for entry in charges:
        logging.info("  %s: %+.4f", entry['element'], entry['charge'])

    return charges
