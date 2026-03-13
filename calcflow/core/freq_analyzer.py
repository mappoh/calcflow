import os
import re
import time
import json
import logging

import numpy as np

from calcflow import CalculationError


def wait_for_freq_termination(
    outcar_path, timeout=172800, poll_interval=60,
    termination_marker="Voluntary context switches",
):
    """Wait until OUTCAR contains the termination marker."""
    logging.info("Checking %s every %ds for convergence...", outcar_path, poll_interval)
    elapsed = 0
    marker_bytes = termination_marker.encode()
    while elapsed < timeout:
        if os.path.exists(outcar_path):
            try:
                with open(outcar_path, "rb") as f:
                    f.seek(0, 2)
                    size = f.tell()
                    f.seek(max(0, size - 8192))
                    if marker_bytes in f.read():
                        logging.info("Termination marker found. Calculation complete.")
                        return True
            except Exception as e:
                logging.error("Error reading %s: %s", outcar_path, e)
        time.sleep(poll_interval)
        elapsed += poll_interval
    return False


def extract_frequencies(outcar_path):
    """
    Parse vibrational frequencies from OUTCAR.
    Handles both real ('f =') and imaginary ('f/i=') modes.

    Returns list of dicts with keys: mode, thz, cm-1, meV, is_imaginary
    """
    pattern = re.compile(
        r"^\s*(\d+)\s+(f(?:/i)?)\s*=\s+([-+]?\d*\.?\d+)\s+THz\s+"
        r"[-+]?\d*\.?\d+\s+2PiTHz\s+([-+]?\d*\.?\d+)\s+cm-1\s+"
        r"([-+]?\d*\.?\d+)\s+meV"
    )

    freq_entries = {}
    with open(outcar_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            match = pattern.search(line)
            if match:
                try:
                    mode_num = int(match.group(1))
                    label = match.group(2)
                    freq_entries[mode_num] = {
                        "mode": mode_num,
                        "thz": float(match.group(3)),
                        "cm-1": float(match.group(4)),
                        "meV": float(match.group(5)),
                        "is_imaginary": label == "f/i",
                    }
                except (ValueError, IndexError) as e:
                    logging.warning("Could not parse frequency from: %s => %s", line.strip(), e)

    return [freq_entries[m] for m in sorted(freq_entries.keys())]


def check_incar_ibrion(calc_dir):
    """Verify that IBRION is set to 5 or 6 for frequency calculation."""
    incar_path = os.path.join(calc_dir, "INCAR")
    if not os.path.exists(incar_path):
        raise CalculationError(f"INCAR not found in {calc_dir}")

    with open(incar_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith(("#", "!")):
                continue
            match = re.search(r"IBRION\s*=\s*(\d+)", line, re.IGNORECASE)
            if match:
                val = int(match.group(1))
                if val not in (5, 6):
                    raise CalculationError(
                        f"IBRION={val} in INCAR; expected 5 or 6 for frequency calculation."
                    )
                logging.info("IBRION=%d confirmed for frequency calculation.", val)
                return
    raise CalculationError("IBRION not found in INCAR.")


def run_freq_analysis(calc_dir):
    """
    Full frequency analysis workflow.

    Returns:
        tuple: (freq_data_list, cm_values_array)
    """
    outcar_path = os.path.join(calc_dir, "OUTCAR")

    if not os.path.exists(outcar_path):
        raise CalculationError(f"OUTCAR not found in {calc_dir}")

    # Check convergence
    if not wait_for_freq_termination(outcar_path):
        raise CalculationError("Frequency calculation did not converge.")

    logging.info("Frequency calculation converged.")

    # Verify INCAR settings
    check_incar_ibrion(calc_dir)

    # Extract frequencies
    freq_data = extract_frequencies(outcar_path)
    if not freq_data:
        logging.warning("No frequency data found in OUTCAR.")
        return [], np.array([])

    # Report imaginary frequencies
    imaginary = [f for f in freq_data if f["is_imaginary"]]
    if imaginary:
        logging.warning("Found %d imaginary frequencies!", len(imaginary))
        for freq in imaginary:
            logging.warning("  Mode %d: %s cm-1 (%s THz)", freq['mode'], freq['cm-1'], freq['thz'])

    logging.info("Extracted %d frequency modes.", len(freq_data))

    # Save JSON
    output_file = os.path.join(calc_dir, "frequency_data.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({"frequencies": freq_data}, f, indent=4)
    logging.info("Frequency data saved to %s", output_file)

    # Extract cm-1 values
    cm_values = np.array([f["cm-1"] for f in freq_data])

    # Save numpy and text files
    np.save(os.path.join(calc_dir, "frequencies_cm1.npy"), cm_values)
    with open(os.path.join(calc_dir, "frequencies_cm1.txt"), "w", encoding="utf-8") as f:
        for val in cm_values:
            f.write(f"{val}\n")

    # Statistics
    logging.info(
        "Frequency stats: min=%.2f, max=%.2f, mean=%.2f cm-1",
        np.min(cm_values), np.max(cm_values), np.mean(cm_values)
    )

    return freq_data, cm_values
