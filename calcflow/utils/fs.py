import os
import shutil
import logging


def prepare_output_directory(output_dir, clean=False):
    """Create output directory. Optionally remove existing contents."""
    if os.path.exists(output_dir) and clean:
        logging.warning("Cleaning existing directory: %s", output_dir)
        shutil.rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    logging.info("Output directory ready: %s", output_dir)
