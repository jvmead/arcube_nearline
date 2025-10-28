"""
Configuration constants and settings for Light DQM.

This module contains all configuration constants, default values,
and channel mappings used throughout the light DQM analysis.
"""

import numpy as np

# ----------------------------- #
#       Physical Constants      #
# ----------------------------- #

SAMPLE_RATE = 0.016  # microseconds per sample

# ADC specifications
ADC14_MAX = 8191
ADC14_16_CONVERSION = 2**2  # Conversion factor between 14 and 16 bit ADC

# Voltage specifications
ADC_V_RANGE = 2.0    # Voltage range of ADC
ADC_V_OFFSET = -1.0  # Voltage offset

# ----------------------------- #
#       Channel Configuration   #
# ----------------------------- #

# Channel mapping: select channels 4-15 in each group of 16
CHANNELS = []
for group_start in range(0, 64, 16):
    CHANNELS.extend(range(group_start + 4, min(group_start + 16, 64)))
CHANNELS = np.array(CHANNELS)

# Number of ADCs and channels
N_ADCS = 8
N_CHANNELS = 64
N_EPCBS = len(CHANNELS) // 6

# ----------------------------- #
#    Frequency Analysis Config  #
# ----------------------------- #

# Frequency regions of interest (MHz)
FREQ_ROIS_MHZ = np.array([0.5, 1.8, 4.6, 7.1, 8.5, 10, 11.5, 19, 20, 25, 30])
FREQ_WINDOW_MHZ = 0.4

# ----------------------------- #
#       Threshold Defaults      #
# ----------------------------- #

DEFAULT_PTPS_16BIT = 500
BASELINE_THRESHOLD_ADC16 = 500
BASELINE_K_SIGMA = 3.0
FLATLINE_THRESHOLD = 0.1

# ----------------------------- #
#      Baseline Expected Ranges #
# ----------------------------- #

def get_baseline_ranges():
    """
    Get the expected baseline ranges for each ADC.

    Returns:
        tuple: (min_allowed, max_allowed) arrays of shape (8, 64)
    """
    min_allowed = np.full((N_ADCS, N_CHANNELS), -30000, dtype=float)
    max_allowed = np.full((N_ADCS, N_CHANNELS), -26000, dtype=float)

    # Special case for ADC 6
    min_allowed[6, :] = -26000
    max_allowed[6, :] = -22000

    return min_allowed, max_allowed


# ----------------------------- #
#       Unit Conversions        #
# ----------------------------- #

def get_ptps(ptps_16bit, units='ADC16'):
    """
    Get peak-to-peak values for the specified units.

    Args:
        ptps_16bit (int or array): Peak-to-peak threshold for 16-bit ADC
        units (str): 'ADC16', 'ADC14', or 'V'

    Returns:
        np.ndarray: Peak-to-peak values for each ADC
    """
    ptps_16 = np.array([ptps_16bit] * N_ADCS)

    if units == 'ADC16':
        return ptps_16
    elif units == 'ADC14':
        return ptps_16 / ADC14_16_CONVERSION
    elif units == 'V':
        return ptps_16 * ADC_V_RANGE / (ADC14_MAX * ADC14_16_CONVERSION)
    else:
        raise ValueError("Units must be 'ADC14', 'ADC16', or 'V'.")


def adc16_to_voltage(adc_counts, mask=None):
    """
    Convert ADC16 counts to voltage.

    Args:
        adc_counts (np.ndarray): ADC16 counts
        mask (np.ndarray, optional): Boolean mask to apply

    Returns:
        np.ndarray: Voltage values
    """
    if mask is not None:
        adc_counts = np.where(mask[..., np.newaxis], adc_counts, 0)
    return adc_counts * (ADC_V_RANGE + ADC_V_OFFSET) / (ADC14_MAX * ADC14_16_CONVERSION)


def adjust_threshold_for_units(threshold, units):
    """
    Adjust threshold value based on units.

    Args:
        threshold (float): Threshold in ADC16 units
        units (str): Target units ('ADC16', 'ADC14', or 'V')

    Returns:
        float: Adjusted threshold
    """
    if units == 'ADC14':
        return threshold / ADC14_16_CONVERSION
    return threshold


# ----------------------------- #
#       File Naming Patterns    #
# ----------------------------- #

JSON_FILENAMES = {
    'noises': 'noises.json',
    'baselines': 'baselines.json',
    'clipped_epcb_beam': 'clipped_epcb_beam.json',
    'clipped_ch_beam': 'clipped_ch_beam.json',
    'clipped_epcb_self': 'clipped_epcb_self.json',
    'clipped_ch_self': 'clipped_ch_self.json',
    'negatives_tpc_beam': 'negatives_tpc_beam.json',
    'negatives_epcb_beam': 'negatives_epcb_beam.json',
    'negatives_tpc_self': 'negatives_tpc_self.json',
    'negatives_epcb_self': 'negatives_epcb_self.json',
}


# ----------------------------- #
#       Plot Configuration      #
# ----------------------------- #

PLOT_CONFIG = {
    'dpi': 100,
    'figure_format': 'pdf',
    'color_good': 'green',
    'color_bad': 'red',
    'color_prev': 'red',
    'marker_size': 10,
    'error_bar_capsize': 4,
    'error_bar_linewidth': 1,
    'alpha_bad_channel': 0.25,
}
