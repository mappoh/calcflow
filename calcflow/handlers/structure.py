import os

from calcflow.core.structure import get_structure_info, convert_structure, build_supercell
from calcflow.handlers.common import pick_structure, after_complete
from calcflow.utils.prompts import ask_int, ask, ask_yes_no


def view_structure_info(session):
    """101 - Display structure information."""
    path = pick_structure(session, prompt="Structure file")

    info = get_structure_info(path)

    print()
    print(f"  File:         {os.path.basename(path)}")
    print(f"  Formula:      {info['formula']}")
    print(f"  Atoms:        {info['n_atoms']}")
    print(f"  Elements:     {', '.join(info['symbols'])}")
    print(
        f"  Cell (A):     a={info['cell_lengths'][0]:.4f}, b={info['cell_lengths'][1]:.4f}, c={info['cell_lengths'][2]:.4f}")
    print(
        f"  Angles (deg): alpha={info['cell_angles'][0]:.2f}, beta={info['cell_angles'][1]:.2f}, gamma={info['cell_angles'][2]:.2f}")
    print(f"  Volume (A^3): {info['volume']:.4f}")
    print(f"  PBC:          {info['pbc']}")
    print()
    after_complete()


def convert_format(session):
    """102 - Convert between structure formats."""
    input_path = pick_structure(session, prompt="Input structure")
    output_path = ask("Output file (e.g. structure.cif, output.xyz)")

    if os.path.exists(output_path):
        if not ask_yes_no(f"'{output_path}' already exists. Overwrite?", default=False):
            return

    convert_structure(input_path, output_path)
    print(f"\n  Converted: {os.path.basename(input_path)} -> {output_path}")
    after_complete()


def build_supercell_handler(session):
    """103 - Build a supercell."""
    input_path = pick_structure(session, prompt="Structure file")
    nx = ask_int("Repeat in x", default=1, min_val=1)
    ny = ask_int("Repeat in y", default=1, min_val=1)
    nz = ask_int("Repeat in z", default=1, min_val=1)
    output_path = ask("Output file", default="POSCAR_supercell")

    if os.path.exists(output_path):
        if not ask_yes_no(f"'{output_path}' already exists. Overwrite?", default=False):
            return

    print("\n  Summary:")
    print(f"    Input:      {os.path.basename(input_path)}")
    print(f"    Supercell:  {nx}x{ny}x{nz}")
    print(f"    Output:     {output_path}")
    print()

    if not ask_yes_no("Proceed?"):
        return

    build_supercell(input_path, output_path, (nx, ny, nz))
    print(f"\n  Supercell written to {output_path}")
    after_complete()
