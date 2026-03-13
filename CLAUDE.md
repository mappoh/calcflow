# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development Commands

```bash
pip install -e ".[dev]"       # Install in editable mode with dev dependencies
pytest                        # Run all tests
pytest tests/test_presets.py  # Run a single test file
ruff check calcflow/          # Lint with ruff
pylint calcflow/ --disable=C0114,C0115,C0116,C0301,C0103,R0903,R0913,R0914,R0801,E0401,C0209  # Full pylint
calcflow                      # Run the CLI (from any directory with structure files)
```

## Architecture

CalcFlow is an interactive, menu-driven CLI for setting up VASP computational chemistry calculations. It does **not** run VASP — it writes input files (POSCAR, INCAR, KPOINTS) and submits jobs to SGE.

### Dispatch Flow

```
cli/main.py:run()  →  _choose_workspace()  →  _show_main_page()  →  main loop
                                                                        ↓
                                                              _handle_category()
                                                                        ↓
                                                              _dispatch(cat_id, opt_idx)
                                                                        ↓
                                                         importlib.import_module(handler_string)
                                                                        ↓
                                                              handler(session)
```

- **Registry** (`cli/registry.py`): Maps category IDs to handler strings like `"calcflow.handlers.workflows:geometry_optimization"`. Handlers are loaded dynamically via `importlib`. To add a new handler, add an entry to `CATEGORY_OPTIONS` — no changes needed in main.py.
- **Display** (`cli/display.py`): Renders menus and the workspace summary. Uses sequential numbering (not fixed IDs).
- **Line Counter**: `main.py` patches `sys.stdout.write` and `builtins.input` to count printed lines. `_erase_lines()` uses ANSI escapes to clear exactly what CalcFlow printed, enabling seamless menu refresh without scrolling.

### Session Dictionary

A `dict` passed to all handlers carrying runtime state:

| Key | Description |
|-----|-------------|
| `work_dir` | Absolute path to working directory |
| `work_dir_name` | Display name (basename only) |
| `structure_files` | List of detected structure file paths |
| `vasp_outputs` | List of VASP output filenames found |
| `subdirs` | List of dicts with subdirectory metadata |
| `last_poscar` | Last selected structure path |
| `last_calc_dir` | Last calculation directory |
| `last_calc_name` | Last calculation name |
| `last_job_id` | Last submitted SGE job ID |

### Handler Contract

All handlers: `def handler(session: dict) -> None`

- Use `pick_structure()` / `pick_calc_dir()` from `handlers/common.py` for file selection
- Use prompt helpers from `utils/prompts.py` (`ask`, `ask_int`, `ask_choice`, `ask_yes_no`, etc.)
- Call `after_complete()` at the end of every successful path (offers continue/exit)
- Early returns (user cancels) should NOT call `after_complete()`
- Errors raise `CalcFlowError` subclasses — caught by `_dispatch` and shown with a pause

### Presets & Config

- **Built-in presets**: `calcflow/data/presets/*.json` (shipped with package)
- **User presets**: `~/.calcflow/presets/*.json` (copied from built-ins on first run, editable)
- **Config**: `~/.calcflow/config.json` (cluster defaults: queue, cores, VASP module, scheduler)
- `load_preset(name)` checks user dir first, falls back to built-in

### VASP Input File Generation

`core/vasp_runner.py:run_vasp_calc()` writes POSCAR, INCAR, and KPOINTS directly (no ASE Vasp calculator). POTCAR generation is handled by the cluster/job script, not by CalcFlow.

### Structure Detection

`core/workspace.py` scans for files matching:
- Extensions: `.vasp`, `.cif`, `.xyz`, `.xsd`, `.gen`
- Prefixes: `POSCAR`, `CONTCAR` (matches `POSCAR1`, `POSCAR_relaxed`, etc.)

## Key Conventions

- Never show absolute paths to users — always use `os.path.basename()`
- All `print()` output uses 2-space indent (`"  text"`), nested items use 4-space (`"    item"`)
- All `open()` calls must specify `encoding="utf-8"` (except binary mode)
- All logging uses lazy `%s` formatting, not f-strings
- All `raise` in `except` blocks must use `from e`
- All `ase.io.read()` calls use `index=-1` and type annotation `atoms: Atoms` with `# type: ignore[assignment]`
- `submit_job_handler(session, standalone=False)` when called from workflow handlers (suppresses duplicate `after_complete`)
