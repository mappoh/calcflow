import os
import sys

from calcflow.core.vasp_runner import run_vasp_calc
from calcflow.core.neb import generate_neb_path
from calcflow.presets.manager import load_preset
from calcflow.handlers.common import pick_structure, pick_structures, after_complete
from calcflow.utils.prompts import ask, ask_choice, ask_yes_no, ask_int, ask_incar_params
from calcflow.utils.fs import prepare_output_directory
from calcflow.handlers.jobs import submit_job_handler


def _setup_params(preset_name):
    """Load preset and let user review/edit parameters."""
    params = load_preset(preset_name)

    print(f"\n  Preset: {preset_name}")
    for key in sorted(params):
        print(f"    {key:12s} = {params[key]}")
    print()

    if ask_yes_no("Edit any parameters?", default=False):
        while True:
            overrides = ask_incar_params()
            params.update(overrides)
            print("\n  Updated parameters:")
            for key in sorted(params):
                print(f"    {key:12s} = {params[key]}")
            print()
            if not ask_yes_no("Edit more?", default=False):
                break

    return params


def _run_single(session, preset_name):
    """Set up a single calculation. Returns (poscar, full_dir, params) or Nones."""
    poscar = pick_structure(session)

    work_dir = session.get("work_dir", os.getcwd())
    work_dir_name = session.get("work_dir_name", os.path.basename(work_dir))

    name = ask("Calculation name")
    use_current = ask_yes_no(f"Save in current directory ({work_dir_name})?")
    if use_current:
        output_dir = work_dir
    else:
        output_dir = ask("Enter directory path")
        output_dir = os.path.expanduser(output_dir)

    # Check for existing folder and let user decide
    full_dir = os.path.join(output_dir, name)
    while os.path.exists(full_dir):
        n = 2
        while os.path.exists(os.path.join(output_dir, f"{name}_{n}")):
            n += 1
        suggested = f"{name}_{n}"
        print(f"\n  '{name}/' already exists.")
        rename = ask_choice("What would you like to do?",
                            [f"use '{suggested}'",
                                "enter a different name", "overwrite"],
                            default=f"use '{suggested}'")
        if rename == f"use '{suggested}'":
            name = suggested
        elif rename == "enter a different name":
            name = ask("New calculation name")
        else:
            break
        full_dir = os.path.join(output_dir, name)

    params = _setup_params(preset_name)

    prepare_output_directory(full_dir)
    session["last_calc_dir"] = full_dir
    session["last_calc_name"] = name

    return poscar, full_dir, params


def _run_batch(session, preset_name):
    """Set up batch calculations for multiple structures."""
    poscars = pick_structures(session)

    work_dir = session.get("work_dir", os.getcwd())
    work_dir_name = session.get("work_dir_name", os.path.basename(work_dir))

    use_current = ask_yes_no(f"Save in current directory ({work_dir_name})?")
    if use_current:
        output_dir = work_dir
    else:
        output_dir = ask("Enter directory path")
        output_dir = os.path.expanduser(output_dir)

    # Naming scheme for batch subdirectories
    prefix = None
    use_prefix = ask_yes_no("Use a common prefix for folder names (e.g. geo_opt_1/, geo_opt_2/)?",
                            default=False)
    if use_prefix:
        prefix = ask("Prefix")

    params = _setup_params(preset_name)

    # Build folder names — auto-detect existing folders
    dir_names = []
    if prefix:
        start = 1
        try:
            for entry in os.scandir(output_dir):
                if entry.is_dir() and entry.name.startswith(prefix + "_"):
                    suffix = entry.name[len(prefix) + 1:]
                    try:
                        start = max(start, int(suffix) + 1)
                    except ValueError:
                        pass
        except (OSError, PermissionError):
            pass
        for i in range(len(poscars)):
            dir_names.append(f"{prefix}_{start + i}")
    else:
        used_names = set()
        for poscar in poscars:
            base = os.path.splitext(os.path.basename(poscar))[0]
            folder = base
            if os.path.exists(os.path.join(output_dir, folder)) or folder in used_names:
                n = 2
                while (os.path.exists(os.path.join(output_dir, f"{folder}_{n}"))
                       or f"{folder}_{n}" in used_names):
                    n += 1
                folder = f"{folder}_{n}"
            used_names.add(folder)
            dir_names.append(folder)

    # Show preview
    print(f"\n  Batch preview ({len(poscars)} calculations):")
    for poscar, folder in zip(poscars, dir_names):
        print(f"    {os.path.basename(poscar):20s} -> {folder}/")
    print()

    if not ask_yes_no("Proceed?"):
        return []

    results = []
    for poscar, folder in zip(poscars, dir_names):
        full_dir = os.path.join(output_dir, folder)
        prepare_output_directory(full_dir)
        run_vasp_calc(poscar, full_dir, params)
        results.append((poscar, full_dir))
        print(f"    Done: {os.path.basename(poscar)} -> {folder}/")

    session["last_calc_dir"] = output_dir
    return results


def _workflow_handler(session, preset_name, after_msg=None):
    """Generic workflow handler supporting single and batch modes."""
    structures = session.get("structure_files", [])

    # Only offer batch when multiple structures exist
    if len(structures) > 1:
        batch = ask_yes_no(
            "Multiple structures found. Run as batch?", default=False)
    else:
        batch = False

    if batch:
        results = _run_batch(session, preset_name)
        if not results:
            return
        print(f"\n  {len(results)} calculations set up.")
        print("\n  Submitting jobs to cluster...")
        for _, full_dir in results:
            session["last_calc_dir"] = full_dir
            submit_job_handler(session, standalone=False)
        print(f"\n  All {len(results)} jobs submitted.")
        if after_msg:
            print(f"  {after_msg}")
        sys.stdout.flush()
        after_complete()
    else:
        poscar, full_dir, params = _run_single(session, preset_name)
        if poscar is None:
            return
        run_vasp_calc(poscar, full_dir, params)
        session["last_calc_dir"] = full_dir
        submit_job_handler(session, standalone=False)
        print()
        if after_msg:
            print(f"  {after_msg}")
        sys.stdout.flush()
        after_complete()


def geometry_optimization(session):
    """201 - Geometry optimization."""
    _workflow_handler(session, "tight")


def geometry_optimization_spin(session):
    """202 - Spin-polarized geometry optimization."""
    _workflow_handler(session, "sp-tight")


def single_point(session):
    """203 - Single-point calculation."""
    _workflow_handler(session, "single-point")


def frequency_calculation(session):
    """204 - Frequency calculation."""
    _workflow_handler(session, "freq")


def bader_setup(session):
    """205 - Bader charge density setup."""
    _workflow_handler(session, "bader",
                      after_msg="After completion, use Post-Processing > Bader Charge Analysis.")


def neb_path_generation(session):
    """206 - NEB path generation."""
    reactant = pick_structure(session, prompt="Reactant structure")
    product = pick_structure(session, prompt="Product structure")
    n_images = ask_int("Number of intermediate images",
                       default=8, min_val=2, max_val=20)
    work_dir = session.get("work_dir", os.getcwd())
    work_dir_name = session.get("work_dir_name", os.path.basename(work_dir))
    use_current = ask_yes_no(
        f"Save in current directory ({work_dir_name}/neb_images)?")
    if use_current:
        output_dir = os.path.join(work_dir, "neb_images")
    else:
        output_dir = ask("Enter directory path")
        output_dir = os.path.expanduser(output_dir)
    method = ask_choice("Interpolation method", [
                        "idpp", "linear"], default="idpp")

    print("\n  Summary:")
    print(f"    Reactant:       {os.path.basename(reactant)}")
    print(f"    Product:        {os.path.basename(product)}")
    print(f"    Images:         {n_images}")
    print(f"    Method:         {method}")
    print(f"    Output:         {os.path.basename(output_dir)}/")
    print()

    if not ask_yes_no("Proceed?"):
        return

    images = generate_neb_path(reactant, product, n_images, output_dir, method)
    print(
        f"\n  Generated {len(images)} images (including endpoints) in {os.path.basename(output_dir)}/")
    session["last_calc_dir"] = output_dir
    after_complete()


