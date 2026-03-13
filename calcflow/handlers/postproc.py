import os
import re

from calcflow.core.freq_analyzer import run_freq_analysis
from calcflow.core.bader import run_bader_analysis
from calcflow.handlers.common import pick_calc_dir, after_complete
from calcflow.utils.prompts import ask_yes_no


def extract_energies(session):
    """301 - Extract energies from OSZICAR."""
    calc_dir = pick_calc_dir(session)
    calc_name = os.path.basename(calc_dir)

    oszicar = os.path.join(calc_dir, "OSZICAR")
    if not os.path.exists(oszicar):
        print(f"\n  OSZICAR not found in {calc_name}/")
        return

    ionic_pattern = re.compile(r"^\s*(\d+)\s+F=\s*([-+]?\d*\.?\d+E[+-]?\d+)")
    scf_pattern = re.compile(r"E0=\s*([-+]?\d*\.?\d+E[+-]?\d+)")

    energies = []
    scf_energies = []
    with open(oszicar, "r", encoding="utf-8") as f:
        for line in f:
            m = ionic_pattern.search(line)
            if m:
                energies.append((int(m.group(1)), float(m.group(2))))
            elif not energies:
                m = scf_pattern.search(line)
                if m:
                    scf_energies.append((len(scf_energies) + 1, float(m.group(1))))

    if not energies:
        energies = scf_energies

    if not energies:
        print("\n  No energies found in OSZICAR.")
        return

    print(f"\n  Energies from {calc_name}/OSZICAR:")
    print(f"  {'Step':>6}  {'Energy (eV)':>16}")
    print(f"  {'---':>6}  {'---':>16}")
    for step, energy in energies:
        print(f"  {step:>6}  {energy:>16.8f}")

    if len(energies) > 1:
        delta = energies[-1][1] - energies[-2][1]
        print(f"\n  Final energy: {energies[-1][1]:.8f} eV")
        print(f"  Last delta:   {delta:.2e} eV")
    else:
        print(f"\n  Energy: {energies[0][1]:.8f} eV")
    print()
    after_complete()


def analyze_frequencies(session):
    """302 - Analyze frequencies from OUTCAR."""
    calc_dir = pick_calc_dir(session)
    calc_name = os.path.basename(calc_dir)

    outcar = os.path.join(calc_dir, "OUTCAR")
    if not os.path.exists(outcar):
        print(f"\n  OUTCAR not found in {calc_name}/")
        return

    freq_data, _ = run_freq_analysis(calc_dir)

    if not freq_data:
        print("\n  No frequency data found in OUTCAR.")
        return

    print(f"\n  Frequencies from {calc_name}/OUTCAR:")
    print(f"  {'Mode':>6}  {'cm-1':>10}  {'THz':>10}  {'meV':>10}  {'Type':>10}")
    print(f"  {'---':>6}  {'---':>10}  {'---':>10}  {'---':>10}  {'---':>10}")
    for f in freq_data:
        ftype = "IMAGINARY" if f["is_imaginary"] else "real"
        print(f"  {f['mode']:>6}  {f['cm-1']:>10.2f}  {f['thz']:>10.4f}  "
              f"{f['meV']:>10.4f}  {ftype:>10}")
    print()
    after_complete()


def bader_analysis(session):
    """303 - Bader charge analysis."""
    calc_dir = pick_calc_dir(session)
    calc_name = os.path.basename(calc_dir)

    # Check required files
    required = ["CHGCAR", "AECCAR0", "AECCAR2"]
    missing = [f for f in required if not os.path.exists(os.path.join(calc_dir, f))]
    if missing:
        print(f"\n  Missing files in {calc_name}/: {', '.join(missing)}")
        print("  Bader analysis requires CHGCAR, AECCAR0, and AECCAR2.")
        return

    run_full = ask_yes_no("Run full workflow (chgsum + bader + charge analysis)?")

    charges = run_bader_analysis(calc_dir, last_step_only=not run_full)

    print(f"\n  Bader charges for {calc_name}/:")
    print(f"  {'#':>4}  {'Element':>8}  {'Charge':>10}")
    print(f"  {'---':>4}  {'---':>8}  {'---':>10}")
    for i, entry in enumerate(charges, 1):
        print(f"  {i:>4}  {entry['element']:>8}  {entry['charge']:>+10.4f}")
    print()
    after_complete()


def extract_forces(session):
    """304 - Extract forces from OUTCAR."""
    calc_dir = pick_calc_dir(session)
    calc_name = os.path.basename(calc_dir)

    outcar = os.path.join(calc_dir, "OUTCAR")
    if not os.path.exists(outcar):
        print(f"\n  OUTCAR not found in {calc_name}/")
        return

    force_pattern = re.compile(r"RMS\s+([-+]?\d*\.?\d+)\s+MAX\s+([-+]?\d*\.?\d+)")

    max_forces = []
    with open(outcar, "r", encoding="utf-8") as f:
        for line in f:
            match = force_pattern.search(line)
            if match:
                rms = float(match.group(1))
                max_f = float(match.group(2))
                max_forces.append((rms, max_f))

    if not max_forces:
        print("\n  No force data found in OUTCAR.")
        return

    print(f"\n  Forces from {calc_name}/OUTCAR:")
    print(f"  {'Step':>6}  {'RMS Force':>12}  {'Max Force':>12}")
    print(f"  {'---':>6}  {'---':>12}  {'---':>12}")
    for i, (rms, max_f) in enumerate(max_forces, 1):
        print(f"  {i:>6}  {rms:>12.6f}  {max_f:>12.6f}")

    print(f"\n  Final: RMS={max_forces[-1][0]:.6f}, Max={max_forces[-1][1]:.6f}")
    print()
    after_complete()
