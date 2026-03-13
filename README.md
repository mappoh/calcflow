# CalcFlow

Interactive menu-driven CLI for VASP computational chemistry workflows. CalcFlow provides a guided interface for setting up calculations, managing jobs, and post-processing results.

## Installation

Clone and install:

```bash
git clone https://github.com/mappoh/calcflow.git
cd calcflow
pip install .            # or: uv pip install .
```

Or install directly without cloning:

```bash
pip install git+https://github.com/mappoh/calcflow.git
```

For development:

```bash
git clone https://github.com/mappoh/calcflow.git
cd calcflow
pip install -e ".[dev]"  # or: uv pip install -e ".[dev]"
```

## Quick Start

Navigate to a directory containing your structure files (POSCAR, CONTCAR, CIF, XYZ, etc.) and run:

```bash
calcflow
```

CalcFlow will detect your structure files and present the interactive menu:

```
 =============================================
         CalcFlow  v0.1.0
   Interactive VASP Workflow Manager
 =============================================
 ---------------------------------------------
  Working directory: my_project

  Structure files found (2):
    1. POSCAR
    2. POSCAR_relaxed
 ---------------------------------------------

 ---------------------------------------------
  0)  Summary of All Options

  1)  Structure Utilities
  2)  Calculation Workflows
  3)  Post-Processing & Analysis
  4)  Job Management
  5)  Utilities

  q)  Quit
 ---------------------------------------------
  >>>
```

## Features

### 1) Structure Utilities
- **View Structure Info** — formula, atoms, lattice parameters, volume
- **Convert Structure Format** — between POSCAR, CIF, XYZ, and other ASE-supported formats

### 2) Calculation Workflows
- **Geometry Optimization** — conjugate gradient relaxation (IBRION=2)
- **Geometry Optimization (Spin-Polarized)** — spin-polarized relaxation (ISPIN=2)
- **Single-Point Calculation** — single SCF energy evaluation
- **Frequency Calculation** — finite differences (IBRION=5)
- **Bader Charge Setup** — charge density output for Bader analysis
- **NEB Path Generation** — interpolate intermediate images between reactant and product

All calculation workflows support **batch mode** when multiple structures are detected — run the same calculation type across all structures with automatic folder naming.

### 3) Post-Processing & Analysis
- **Extract Energies** — parse ionic/SCF energies from OSZICAR
- **Analyze Frequencies** — parse vibrational modes from OUTCAR
- **Bader Charge Analysis** — run chgsum + bader and compute per-atom charges
- **Extract Forces** — parse max and RMS forces from OUTCAR

### 4) Job Management
- **Submit Job** — submit to SGE with configurable queue, cores, and VASP executable
- **Check Job Status** — view running/queued jobs (qstat)
- **Cancel Job** — cancel a job by ID (qdel)

### 5) Utilities
- **ENCUT Convergence Test** — sweep ENCUT values with single-point calculations
- **KPOINTS Convergence Test** — sweep k-point meshes
- **View/Edit Presets** — list, view, or create custom INCAR parameter sets
- **Configure CalcFlow** — edit cluster defaults (queue, cores, VASP module)

## Built-in Presets

| Preset | Type | Key Settings |
|--------|------|-------------|
| `tight` | Geometry optimization | IBRION=2, NSW=500, ISPIN=1 |
| `sp-tight` | Spin-polarized geometry optimization | IBRION=2, NSW=500, ISPIN=2 |
| `freq` | Frequency calculation | IBRION=5, NFREE=2 |
| `bader` | Bader charge density | NSW=0, LAECHG=True |
| `single-point` | Single SCF | NSW=0 |

Custom presets can be created via the menu and are saved to `~/.calcflow/presets/`.

## Configuration

On first run, CalcFlow creates `~/.calcflow/config.json` with cluster defaults:

- Scheduler (SGE)
- Default queue, cores, parallel environment
- VASP module and executable

Edit via **Utilities > Configure CalcFlow** or directly in the config file.

## Requirements

- Python >= 3.9
- [ASE](https://wiki.fysik.dtu.dk/ase/) >= 3.22
- NumPy >= 1.24
- Jinja2 >= 3.1

For Bader analysis, [bader](http://theory.cm.utexas.edu/henkelman/code/bader/) and `chgsum.pl` must be available in your PATH.

## License

MIT
