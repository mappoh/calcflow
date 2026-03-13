import os
import logging

import numpy as np
from ase import Atoms
from ase.io import read
from ase.mep import NEB

from calcflow import CalculationError


def generate_neb_path(reactant_path, product_path, n_images, output_dir, method="idpp"):
    """
    Generate NEB intermediate images between reactant and product structures.

    Handles periodic boundary wrapping automatically.

    Args:
        reactant_path: Path to reactant structure file
        product_path: Path to product structure file
        n_images: Number of intermediate images
        output_dir: Directory to write image subdirectories
        method: Interpolation method ('idpp' or 'linear')

    Returns:
        List of ASE Atoms objects (reactant + intermediates + product)
    """
    try:
        reactant: Atoms = read(reactant_path, index=-1)  # type: ignore[assignment]
        product: Atoms = read(product_path, index=-1)  # type: ignore[assignment]
    except Exception as e:
        raise CalculationError(f"Failed to read structures: {e}") from e

    # Get positions and cell
    pr = reactant.get_positions()
    pp = product.get_positions()
    cell = reactant.get_cell()

    # Wrap/unwrap atoms crossing periodic boundaries
    cell_norms = [np.linalg.norm(cell[j]) for j in range(3)]
    half_norms = [n / 2 for n in cell_norms]

    diff = pr - pp
    for i, d in enumerate(diff):
        d = abs(d)
        index = np.argsort(d)[::-1]
        for j in index:
            if abs(d[j]) > half_norms[j]:
                if pr[i][j] < half_norms[j]:
                    pr[i] += cell[j]
                elif pr[i][j] > half_norms[j]:
                    pr[i] -= cell[j]
                d = abs(pr[i] - pp[i])
                diff = pr - pp

    # Verify wrapping
    diff2 = pr - pp
    for i, d in enumerate(diff2):
        for dim in range(3):
            if abs(d[dim]) > half_norms[dim]:
                logging.warning(
                    "Atom %d may not be properly wrapped in dimension %d: "
                    "displacement = %.4f", i, dim, d[dim]
                )

    reactant.set_positions(pr)

    # Build image list
    images = [reactant]
    images += [reactant.copy() for _ in range(n_images)]
    images += [product]

    # Interpolate
    neb = NEB(images)
    neb.interpolate(method)
    logging.info("Generated %d intermediate images using %s interpolation.", n_images, method)

    # Write to directories
    os.makedirs(output_dir, exist_ok=True)
    for i, img in enumerate(images):
        img_dir = os.path.join(output_dir, f"{i:02d}")
        os.makedirs(img_dir, exist_ok=True)
        img.write(os.path.join(img_dir, "POSCAR"))

    logging.info("NEB images written to %s/00 through %s/%02d", output_dir, output_dir, len(images)-1)

    return images
