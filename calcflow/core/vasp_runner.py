import os
import logging

from ase import Atoms
from ase.io import read
from ase.calculators.vasp import Vasp

from calcflow import CalculationError


def run_vasp_calc(poscar_path, output_dir, params):
    """
    Run a VASP calculation using ASE.

    ASE automatically generates INCAR, KPOINTS, and POTCAR from the
    params dict and the atoms object.

    Args:
        poscar_path: Path to the input structure file (POSCAR, CIF, XYZ, etc.)
        output_dir: Directory where VASP files will be written
        params: Dict of VASP parameters (from a preset or merged)
    """
    try:
        atoms: Atoms = read(poscar_path, index=-1)  # type: ignore[assignment]
    except Exception as e:
        raise CalculationError(f"Failed to read structure from '{poscar_path}': {e}") from e

    os.environ["VASP_JOB_NAME"] = os.path.basename(output_dir)

    params = dict(params)  # avoid mutating caller's dict

    # Determine pseudopotentials from GGA parameter
    gga = params.get("GGA", "").strip().upper()
    if gga == "PE":
        params["pp"] = "PBE"
    else:
        raise CalculationError(
            f"Unknown or missing 'GGA' parameter '{gga}'. Only 'PE' (PBE) is currently supported."
        )

    try:
        calc = Vasp(directory=output_dir, **params)
        atoms.calc = calc
        calc.write_input(atoms)
        logging.info("VASP input files written to %s", output_dir)
    except Exception as e:
        raise CalculationError(f"Failed to write VASP input files: {e}") from e
