CATEGORY_LABELS = {
    1: "Structure Utilities",
    2: "Calculation Workflows",
    3: "Post-Processing & Analysis",
    4: "Job Management",
    5: "Utilities",
}

# Categories that require structure files to be present
CATEGORIES_REQUIRING_STRUCTURES = {1, 2}

# Each category has a list of options. Users see simple 1, 2, 3... within each submenu.
CATEGORY_OPTIONS = {
    1: [
        {
            "label": "View Structure Info",
            "handler": "calcflow.handlers.structure:view_structure_info",
            "description": "Display formula, atoms, lattice parameters, and volume.",
        },
        {
            "label": "Convert Structure Format",
            "handler": "calcflow.handlers.structure:convert_format",
            "description": "Convert between POSCAR, CIF, XYZ, etc. (ASE-supported formats).",
        },
    ],
    2: [
        {
            "label": "Geometry Optimization",
            "handler": "calcflow.handlers.workflows:geometry_optimization",
            "description": "Relax atomic positions using conjugate gradient (IBRION=2).",
        },
        {
            "label": "Geometry Optimization (Spin-Polarized)",
            "handler": "calcflow.handlers.workflows:geometry_optimization_spin",
            "description": "Spin-polarized relaxation (ISPIN=2).",
        },
        {
            "label": "Single-Point Calculation",
            "handler": "calcflow.handlers.workflows:single_point",
            "description": "Single SCF energy evaluation (NSW=0).",
        },
        {
            "label": "Frequency Calculation",
            "handler": "calcflow.handlers.workflows:frequency_calculation",
            "description": "Finite differences frequency calculation (IBRION=5).",
        },
        {
            "label": "Bader Charge Setup",
            "handler": "calcflow.handlers.workflows:bader_setup",
            "description": "Single-point with charge density output for Bader analysis.",
        },
        {
            "label": "NEB Path Generation",
            "handler": "calcflow.handlers.workflows:neb_path_generation",
            "description": "Generate intermediate NEB images between reactant and product.",
        },
    ],
    3: [
        {
            "label": "Extract Energies",
            "handler": "calcflow.handlers.postproc:extract_energies",
            "description": "Parse total energies from OSZICAR.",
        },
        {
            "label": "Analyze Frequencies",
            "handler": "calcflow.handlers.postproc:analyze_frequencies",
            "description": "Parse vibrational modes from OUTCAR and save results.",
        },
        {
            "label": "Bader Charge Analysis",
            "handler": "calcflow.handlers.postproc:bader_analysis",
            "description": "Run chgsum + bader and compute per-atom charges.",
        },
        {
            "label": "Extract Forces",
            "handler": "calcflow.handlers.postproc:extract_forces",
            "description": "Parse max and RMS forces from OUTCAR.",
        },
    ],
    4: [
        {
            "label": "Submit Job",
            "handler": "calcflow.handlers.jobs:submit_job_handler",
            "description": "Submit a VASP job to SGE.",
        },
        {
            "label": "Check Job Status",
            "handler": "calcflow.handlers.jobs:check_status",
            "description": "Show running/queued jobs (qstat).",
        },
        {
            "label": "Cancel Job",
            "handler": "calcflow.handlers.jobs:cancel_job_handler",
            "description": "Cancel a running/queued job (qdel).",
        },
    ],
    5: [
        {
            "label": "ENCUT Convergence Test",
            "handler": "calcflow.handlers.utilities:encut_convergence",
            "description": "Run series of single-points at different ENCUT values.",
        },
        {
            "label": "KPOINTS Convergence Test",
            "handler": "calcflow.handlers.utilities:kpoints_convergence",
            "description": "Run series of single-points with different k-point meshes.",
        },
        {
            "label": "View/Edit Presets",
            "handler": "calcflow.handlers.utilities:manage_presets",
            "description": "List, view, or create custom INCAR presets.",
        },
        {
            "label": "Configure CalcFlow",
            "handler": "calcflow.handlers.utilities:configure",
            "description": "Edit cluster defaults (queue, cores, VASP module, etc.).",
        },
    ],
}


def get_available_categories(session):
    """Return category IDs that are available given the current session state."""
    has_structures = bool(session.get("structure_files"))
    available = []
    for cat_id in sorted(CATEGORY_LABELS):
        if cat_id in CATEGORIES_REQUIRING_STRUCTURES and not has_structures:
            continue
        available.append(cat_id)
    return available
