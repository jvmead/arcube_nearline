"""
Quality check functions for Light DQM.

This module contains functions for checking data quality issues such as
flatlined channels and baseline deviations.
"""

import logging
import numpy as np

from . import config

logger = logging.getLogger(__name__)


# ----------------------------- #
#    Flatline Detection         #
# ----------------------------- #

def check_flatline(max_values, threshold=None):
    """
    Check if channels are flatlined (no signal activity).

    A channel is considered flatlined if all max values are below the threshold.

    Args:
        max_values (np.ndarray): Max values per event (n_events, n_adcs, n_channels)
        threshold (float, optional): Flatline threshold (default from config)

    Returns:
        np.ndarray: Boolean mask (n_adcs, n_channels) where True = flatlined
    """
    if threshold is None:
        threshold = config.FLATLINE_THRESHOLD

    flatlined = np.all(max_values < threshold, axis=0)

    n_flatlined = np.sum(flatlined)
    logger.info(f"Flatline check: {n_flatlined} channels flatlined")

    return flatlined


# ----------------------------- #
#    Baseline Deviation Check   #
# ----------------------------- #

def check_baseline(prev_baseline, current_baseline, units='ADC16',
                   threshold=None, k_sigma=None):
    """
    Compare current baseline against previous baseline and expected range.

    Returns:
        tuple: (mask, status)
            - mask: Boolean array (n_adcs, n_channels) where True = problem detected
            - status: Integer array with reason codes:
                -1 = outside expected range
                 1 = current uncertainty too large
                 2 = significant change from previous
                 3 = both 1 and 2

    Args:
        prev_baseline (tuple or None): Previous (central, lower, upper)
        current_baseline (tuple): Current (central, lower, upper)
        units (str): Units for baseline values
        threshold (float, optional): Threshold for uncertainty
        k_sigma (float, optional): Number of sigma for directional test

    Returns:
        tuple: (mask, status) boolean mask and status codes
    """
    if threshold is None:
        threshold = config.BASELINE_THRESHOLD_ADC16
    if k_sigma is None:
        k_sigma = config.BASELINE_K_SIGMA

    # Adjust threshold for units
    thr = config.adjust_threshold_for_units(threshold, units)

    curr_c, curr_l, curr_u = current_baseline
    mask = np.zeros_like(curr_c, dtype=bool)
    status = np.zeros_like(curr_c, dtype=int)

    # Check against expected range
    min_allowed, max_allowed = config.get_baseline_ranges()
    mask_range = (curr_c < min_allowed) | (curr_c > max_allowed)
    mask |= mask_range
    status[mask_range] = -1

    # Check current uncertainty
    curr_margin = np.maximum(curr_l, curr_u)
    mask_curr = curr_margin > thr
    mask |= mask_curr
    status[mask_curr] = 1

    # If no previous baseline, return current checks only
    if prev_baseline is None:
        n_problems = np.sum(mask)
        logger.info(f"Baseline check (no previous): {n_problems} channels flagged")
        return mask, status

    # Check against previous baseline
    prev_c, prev_l, prev_u = prev_baseline

    # Directional difference
    diff = curr_c - prev_c
    abs_diff = np.abs(diff)

    # Directional combined uncertainty
    # If current > previous, use curr_l and prev_u
    # If current < previous, use curr_u and prev_l
    sigma_sq = np.where(
        diff > 0,
        curr_l**2 + prev_u**2,
        curr_u**2 + prev_l**2
    )
    sigma = np.sqrt(np.maximum(sigma_sq, np.finfo(float).eps))
    mask_dir = abs_diff > (k_sigma * sigma)

    # Only apply directional mask where not already flagged
    mask |= mask_dir & (~mask)
    status[mask_dir] = 2

    # Mark as status 3 if both current uncertainty and directional change
    status[mask & mask_dir] = 3

    n_problems = np.sum(mask)
    n_range = np.sum(status == -1)
    n_uncertainty = np.sum(status == 1)
    n_change = np.sum(status == 2)
    n_both = np.sum(status == 3)

    logger.info(
        f"Baseline check: {n_problems} channels flagged "
        f"(range: {n_range}, uncertainty: {n_uncertainty}, "
        f"change: {n_change}, both: {n_both})"
    )

    return mask, status
