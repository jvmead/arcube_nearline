"""
Utility functions for Light DQM.

This module contains helper functions for statistical calculations,
file I/O operations, and data management.
"""

import os
import json
import logging
import numpy as np
import pandas as pd
from scipy.stats import beta

logger = logging.getLogger(__name__)


# ----------------------------- #
#    Statistical Functions      #
# ----------------------------- #

def clopper_pearson(passed, total, interval=0.68):
    """
    Calculate Clopper-Pearson confidence intervals for binomial proportions.

    This is a numpy-friendly implementation that handles arrays of events.

    Args:
        passed (array-like): Number of events that passed
        total (array-like): Total number of events
        interval (float): Confidence interval (default: 0.68 for 1 sigma)

    Returns:
        tuple: (percentage, error_low, error_high) all as percentages

    Raises:
        ValueError: If passed > total or confidence intervals are out of range
    """
    # Validate inputs
    if np.any(passed > total):
        raise ValueError("Passed events cannot be greater than total events.")

    alpha = 1 - interval

    # Ensure arrays are numpy arrays
    passed = np.asarray(passed)
    total = np.asarray(total)

    # Initialize lower and upper arrays
    lower = np.zeros_like(passed, dtype=float)
    upper = np.ones_like(passed, dtype=float)

    # Mask for valid entries (total > 0)
    valid = total > 0

    # For valid entries, compute lower and upper bounds using beta distribution
    lower[valid] = beta.ppf(alpha/2, passed[valid], total[valid] - passed[valid] + 1)
    upper[valid] = beta.ppf(1 - alpha/2, passed[valid] + 1, total[valid] - passed[valid])

    # Replace NaNs with 0 and 1
    lower = np.nan_to_num(lower, nan=0.0)
    upper = np.nan_to_num(upper, nan=1.0)

    # Fraction calculation
    with np.errstate(divide='ignore', invalid='ignore'):
        frac = np.true_divide(passed, total)
        frac = np.nan_to_num(frac, nan=0.0)

    # If total is zero, set frac to 0
    frac = np.where(total == 0, 0.0, frac)

    # If frac is 0 and total is not zero, set lower and upper bounds
    mask = (frac == 0) & (total != 0)
    lower = np.where(mask, 0.0, lower)
    upper = np.where(mask, 1.0, upper)

    # Validate results
    if np.any(frac < lower) or np.any(frac > upper):
        raise ValueError("Calculated fraction is outside the confidence interval.")
    if np.any(lower < 0) or np.any(upper > 1):
        raise ValueError("Confidence interval bounds are out of range [0, 1].")

    # Calculate errors as percentages
    err_low = 100 * (frac - lower)
    err_up = 100 * (upper - frac)
    pct = 100 * frac

    # Ensure negative error is zero when central value is zero
    mask_no_entries = (total == 0) | (pct == 0)
    err_low[mask_no_entries] = 0.0

    return pct, err_low, err_up


# ----------------------------- #
#    Channel Status Loading     #
# ----------------------------- #

def load_channel_status(channel_status_file):
    """
    Load channel status from CSV file.

    Args:
        channel_status_file (str): Path to channel status CSV file

    Returns:
        np.ndarray or None: Channel status array (0 = good, nonzero = bad)
    """
    try:
        cs_df = pd.read_csv(channel_status_file, header=None)
        cs = cs_df.to_numpy()
        logger.info(f"Channel status loaded successfully from: {channel_status_file}")
        return cs
    except FileNotFoundError:
        logger.warning(f"Channel status file not found: {channel_status_file}")
        return None
    except pd.errors.EmptyDataError:
        logger.warning(f"Channel status file is empty: {channel_status_file}")
        return None
    except Exception as e:
        logger.error(f"Error loading channel status from {channel_status_file}: {e}")
        return None


# ----------------------------- #
#       JSON File I/O           #
# ----------------------------- #

def save_as_json(file_index, data_c, data_l, data_u, output_dir, filename):
    """
    Save data as JSON file with central value and error bounds.

    Data format: file_index, data_c (central), data_l (lower), data_u (upper)
    If file exists, append to it; otherwise create new file.

    Args:
        file_index (int): File index identifier
        data_c (np.ndarray): Central values (2D: ADC x channel)
        data_l (np.ndarray): Lower error bounds
        data_u (np.ndarray): Upper error bounds
        output_dir (str): Output directory path
        filename (str): Output filename
    """
    data = {
        'file_index': int(file_index),
        'data_c': data_c.tolist(),
        'data_l': data_l.tolist(),
        'data_u': data_u.tolist()
    }

    filepath = os.path.join(output_dir, filename)
    mode = 'a' if os.path.exists(filepath) else 'w'

    with open(filepath, mode) as f:
        json.dump(data, f)
        f.write('\n')

    logger.debug(f"Data for file_index {file_index} saved to {filepath}")


def read_from_json(file_indices, output_dir, filename):
    """
    Read data from JSON file for specified file indices.

    Averages central values and combines errors in quadrature.

    Args:
        file_indices (list or None): List of file indices to read
        output_dir (str): Directory containing JSON file
        filename (str): JSON filename

    Returns:
        tuple or None: (data_c, data_l, data_u) averaged/combined data, or None
    """
    if file_indices is None or len(file_indices) == 0:
        return None

    filepath = os.path.join(output_dir, filename)
    if not os.path.exists(filepath):
        logger.info(f"JSON file not found: {filepath}, not making comparisons")
        return None

    data_c, data_l, data_u = [], [], []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get('file_index') in file_indices:
                        data_c.append(entry['data_c'])
                        data_l.append(entry['data_l'])
                        data_u.append(entry['data_u'])
                except json.JSONDecodeError:
                    logger.warning(f"Skipping malformed line in {filepath}: {line.strip()}")
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
        return None

    if len(data_c) == 0:
        return None

    # Convert to arrays and combine
    data_c = np.array(data_c)
    data_l = np.array(data_l)
    data_u = np.array(data_u)

    # Average central values, combine errors in quadrature
    data_c = np.mean(data_c, axis=0)
    data_l = np.sqrt(np.sum(data_l**2, axis=0))
    data_u = np.sqrt(np.sum(data_u**2, axis=0))

    return data_c, data_l, data_u


def save_eff_as_json(file_index, passed, totals, output_dir, filename):
    """
    Save efficiency data (passed/total) as JSON file.

    Args:
        file_index (int): File index identifier
        passed (np.ndarray): Number of events that passed (2D: ADC x channel)
        totals (np.ndarray): Total number of events
        output_dir (str): Output directory path
        filename (str): Output filename
    """
    data = {
        'file_index': int(file_index),
        'pass': passed.tolist(),
        'totals': totals.tolist()
    }

    filepath = os.path.join(output_dir, filename)
    mode = 'a' if os.path.exists(filepath) else 'w'

    with open(filepath, mode) as f:
        json.dump(data, f)
        f.write('\n')

    logger.debug(f"Efficiency data for file_index {file_index} saved to {filepath}")


def read_eff_from_json(file_indices, output_dir, filename):
    """
    Read efficiency data from JSON file and combine.

    Args:
        file_indices (list or None): List of file indices to read
        output_dir (str): Directory containing JSON file
        filename (str): JSON filename

    Returns:
        tuple or None: (passed, totals) summed data, or None
    """
    if file_indices is None or len(file_indices) == 0:
        return None

    filepath = os.path.join(output_dir, filename)
    if not os.path.exists(filepath):
        logger.info(f"Efficiency JSON file not found: {filepath}")
        return None

    passed, totals = [], []
    try:
        with open(filepath, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    if entry.get('file_index') in file_indices:
                        passed.append(entry['pass'])
                        totals.append(entry['totals'])
                except json.JSONDecodeError:
                    logger.warning(f"Skipping malformed line in {filepath}: {line.strip()}")
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
        return None

    if len(passed) == 0 or len(totals) == 0:
        return None

    # Sum passed and totals
    passed = np.sum(np.array(passed), axis=0)
    totals = np.sum(np.array(totals), axis=0)

    return passed, totals


def save_spectra_as_json(file_index, spectra_roi, output_dir, filename):
    """
    Save frequency spectra data as JSON file.

    Args:
        file_index (int): File index identifier
        spectra_roi (np.ndarray): Spectra data (2D: ADC x channel)
        output_dir (str): Output directory path
        filename (str): Output filename
    """
    data = {
        'file_index': int(file_index),
        'spectra_roi': spectra_roi.tolist()
    }

    filepath = os.path.join(output_dir, filename)
    mode = 'a' if os.path.exists(filepath) else 'w'

    with open(filepath, mode) as f:
        json.dump(data, f)
        f.write('\n')

    logger.debug(f"Spectra data for file_index {file_index} saved to {filepath}")


# ----------------------------- #
#       Directory Management    #
# ----------------------------- #

def ensure_directory_exists(directory):
    """
    Ensure a directory exists, create if it doesn't.

    Args:
        directory (str): Directory path

    Raises:
        Exception: If directory cannot be created
    """
    try:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Directory is ready: {directory}")
    except Exception as e:
        logger.error(f"Error creating directory {directory}: {e}")
        raise


def find_flow_files(input_path, file_syntax):
    """
    Find all FLOW.hdf5 files matching the pattern.

    Args:
        input_path (str): Directory to search
        file_syntax (str): File prefix pattern

    Returns:
        list: Sorted list of matching filenames
    """
    all_files = [
        f for f in os.listdir(input_path)
        if f.startswith(file_syntax) and f.endswith('.FLOW.hdf5')
    ]
    all_files.sort()
    return all_files
