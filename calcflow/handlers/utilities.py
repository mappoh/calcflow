import os

from calcflow.core.vasp_runner import run_vasp_calc
from calcflow.presets.manager import load_preset, merge_preset, list_presets, save_user_preset
from calcflow.config.settings import get_config, update_config
from calcflow.handlers.common import pick_structure
from calcflow.utils.prompts import ask, ask_int, ask_yes_no, ask_choice, ask_incar_params
from calcflow.utils.fs import prepare_output_directory


def encut_convergence(session):
    """501 - ENCUT convergence test."""
    poscar = pick_structure(session)

    work_dir = session.get("work_dir", os.getcwd())
    work_dir_name = session.get("work_dir_name", os.path.basename(work_dir))
    use_current = ask_yes_no(
        f"Save in current directory ({work_dir_name}/encut_conv)?")
    if use_current:
        output_base = os.path.join(work_dir, "encut_conv")
    else:
        output_base = ask("Enter directory path")
        output_base = os.path.expanduser(output_base)
    start = ask_int("Starting ENCUT (eV)", default=300, min_val=100)
    end = ask_int("Ending ENCUT (eV)", default=600, min_val=start)
    step = ask_int("Step size (eV)", default=50, min_val=10)

    encut_values = list(range(start, end + 1, step))

    print("\n  Summary:")
    print(f"    Structure:    {os.path.basename(poscar)}")
    print(f"    Output:       {os.path.basename(output_base)}/")
    print(f"    ENCUT range:  {start} - {end} eV (step {step})")
    print(f"    Calculations: {len(encut_values)}")
    print(f"    Values:       {encut_values}")
    print()

    if not ask_yes_no("Proceed?"):
        return

    for encut in encut_values:
        calc_dir = os.path.join(output_base, f"encut_{encut}")
        params = merge_preset("single-point", {"ENCUT": encut})
        prepare_output_directory(calc_dir)
        run_vasp_calc(poscar, calc_dir, params)
        print(f"    Done: encut_{encut}/")

    print(
        f"\n  All {len(encut_values)} calculations set up in {os.path.basename(output_base)}/")
    print("  Use Post-Processing > Extract Energies to compare results.")


def kpoints_convergence(session):
    """502 - KPOINTS convergence test."""
    poscar = pick_structure(session)

    work_dir = session.get("work_dir", os.getcwd())
    work_dir_name = session.get("work_dir_name", os.path.basename(work_dir))
    use_current = ask_yes_no(
        f"Save in current directory ({work_dir_name}/kpoints_conv)?")
    if use_current:
        output_base = os.path.join(work_dir, "kpoints_conv")
    else:
        output_base = ask("Enter directory path")
        output_base = os.path.expanduser(output_base)
    start = ask_int("Starting k-mesh (NxNxN, enter N)", default=2, min_val=1)
    end = ask_int("Ending k-mesh N", default=8, min_val=start)
    step = ask_int("Step", default=1, min_val=1)

    k_values = list(range(start, end + 1, step))
    k_labels = [f"{k}x{k}x{k}" for k in k_values]

    print("\n  Summary:")
    print(f"    Structure:    {os.path.basename(poscar)}")
    print(f"    Output:       {os.path.basename(output_base)}/")
    print(f"    K-mesh range: {k_labels[0]} - {k_labels[-1]} (step {step})")
    print(f"    Calculations: {len(k_values)}")
    print(f"    Meshes:       {k_labels}")
    print()

    if not ask_yes_no("Proceed?"):
        return

    for k in k_values:
        calc_dir = os.path.join(output_base, f"kpts_{k}x{k}x{k}")
        params = merge_preset("single-point", {"kpts": (k, k, k)})
        prepare_output_directory(calc_dir)
        run_vasp_calc(poscar, calc_dir, params)
        print(f"    Done: kpts_{k}x{k}x{k}/")

    print(
        f"\n  All {len(k_values)} calculations set up in {os.path.basename(output_base)}/")
    print("  Use Post-Processing > Extract Energies to compare results.")


def manage_presets(session):  # pylint: disable=unused-argument
    """503 - View/edit presets."""
    presets = list_presets()

    print("\n  Available presets:")
    for i, name in enumerate(presets, 1):
        print(f"    {i}) {name}")
    print()

    action = ask_choice("What would you like to do?",
                        ["view a preset", "create new preset", "back"],
                        default="view a preset")

    if action == "back":
        return

    if action == "view a preset":
        name = ask_choice("Select preset", presets)
        params = load_preset(name)
        print(f"\n  Preset: {name}")
        print("  " + "-" * 30)
        for key, val in sorted(params.items()):
            print(f"    {key:12s} = {val}")
        print()

    elif action == "create new preset":
        base = ask_choice("Start from an existing preset?", [
                          "empty"] + presets, default="empty")
        if base == "empty":
            params = {}
        else:
            params = load_preset(base)

        new_name = ask("Preset name")
        overrides = ask_incar_params()
        params.update(overrides)

        print(f"\n  New preset '{new_name}':")
        for key, val in sorted(params.items()):
            print(f"    {key:12s} = {val}")
        print()

        if ask_yes_no("Save this preset?"):
            save_user_preset(new_name, params)
            print(f"  Preset '{new_name}' saved to ~/.calcflow/presets/")
        else:
            print("  Preset not saved.")


def configure(session):  # pylint: disable=unused-argument
    """504 - Edit CalcFlow configuration."""
    config = get_config()
    cluster = config.get("cluster", {})
    vasp = config.get("vasp", {})

    print("\n  Current configuration:")
    print(f"    Scheduler:     {cluster.get('scheduler', 'sge')}")
    print(f"    Default queue: {cluster.get('default_queue', 'long')}")
    print(f"    Default cores: {cluster.get('default_cores', 64)}")
    print(f"    Parallel env:  {cluster.get('parallel_env', 'mpi-*')}")
    print(f"    VASP module:   {cluster.get('vasp_module', 'vasp/6.4.0/')}")
    print(f"    VASP exec:     {vasp.get('default_executable', 'vasp_std')}")
    print()

    if not ask_yes_no("Edit configuration?", default=False):
        return

    queue = ask("Default queue", default=cluster.get("default_queue", "long"))
    cores = ask_int("Default cores", default=cluster.get(
        "default_cores", 64), min_val=1)
    pe = ask("Parallel environment",
             default=cluster.get("parallel_env", "mpi-*"))
    module = ask("VASP module", default=cluster.get(
        "vasp_module", "vasp/6.4.0/"))
    exe = ask_choice("Default VASP executable",
                     ["vasp_std", "vasp_gam", "vasp_neb"],
                     default=vasp.get("default_executable", "vasp_std"))

    print("\n  New configuration:")
    print(f"    Default queue: {queue}")
    print(f"    Default cores: {cores}")
    print(f"    Parallel env:  {pe}")
    print(f"    VASP module:   {module}")
    print(f"    VASP exec:     {exe}")
    print()

    if not ask_yes_no("Save changes?"):
        print("  Changes discarded.")
        return

    updates = {
        "cluster": {
            "default_queue": queue,
            "default_cores": cores,
            "parallel_env": pe,
            "vasp_module": module,
        },
        "vasp": {"default_executable": exe},
    }

    update_config(updates)
    print("\n  Configuration updated.")
