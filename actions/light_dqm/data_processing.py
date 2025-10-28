"""
Data processing functions for waveform analysis.

This module contains functions for processing light detector waveforms,
including baseline calculations, noise analysis, and frequency spectra.
"""

import logging
import numpy as np
from scipy.fft import rfft, rfftfreq

from . import config

logger = logging.getLogger(__name__)


# ----------------------------- #
#    Waveform Processing        #
# ----------------------------- #

def get_waveform_info(waveform, units='ADC16', mask=None, ths=None):
    """
    Extract comprehensive information from waveforms.

    Calculates noise, baseline, max values, and identifies clipped waveforms
    and negative spikes.

    Args:
        waveform (np.ndarray): Waveform data (n_events, n_adcs, n_channels, n_samples)
        units (str): Units for the waveform ('ADC16', 'ADC14', or 'V')
        mask (np.ndarray, optional): Event indices to process
        ths (np.ndarray, optional): Threshold for negative spike detection

    Returns:
        tuple: (wvfms, noise, baseline, max_value, clipped, negs)
            - wvfms: Waveforms in specified units
            - noise: Standard deviation of first 50 samples
            - baseline: Mean of first 50 samples
            - max_value: Maximum value above baseline
            - clipped: Boolean mask of clipped waveforms
            - negs: Boolean mask of waveforms with negative spikes
    """
    if mask is not None:
        waveform = waveform[mask]

    # Check for clipped waveforms (at or near ADC saturation)
    clipped = np.any(
        waveform >= (config.ADC14_MAX - 1) * config.ADC14_16_CONVERSION,
        axis=-1
    )

    # Convert units if needed
    if units == 'ADC14':
        waveform = waveform / config.ADC14_16_CONVERSION
    elif units == 'V':
        waveform = config.adc16_to_voltage(waveform)
    elif units != 'ADC16':
        raise ValueError("Units must be 'ADC14', 'ADC16', or 'V'.")

    # Calculate noise (std of first 50 samples)
    noise = np.std(waveform[:, :, :, :50], axis=3)

    # Calculate baseline (mean of first 50 samples)
    baseline = np.mean(waveform[:, :, :, :50], axis=3)

    # Calculate max value above baseline
    max_value = np.max(waveform - baseline[:, :, :, np.newaxis], axis=3)

    # Check for negative spikes below threshold
    if ths is not None:
        negs = np.any(
            waveform - baseline[:, :, :, np.newaxis] < -ths[np.newaxis, :, np.newaxis, np.newaxis],
            axis=-1
        )
    else:
        negs = np.zeros_like(max_value, dtype=bool)

    # Return waveforms in specified units
    wvfms = waveform[:, :, :, :]

    return wvfms, noise, baseline, max_value, clipped, negs


def get_sum_waveform(waveform, units='ADC16', mask=None, clip=True):
    """
    Calculate sum waveform for visualization.

    Args:
        waveform (np.ndarray): Waveform data (n_events, n_adcs, n_channels, n_samples)
        units (str): Units for the waveform ('ADC16', 'ADC14', or 'V')
        mask (np.ndarray, optional): Event mask
        clip (bool): Whether to clip at ADC limit

    Returns:
        np.ndarray: Sum waveform
    """
    if mask is not None:
        waveform = waveform[mask]

    # Convert units
    if units == 'ADC14':
        waveform = waveform / config.ADC14_16_CONVERSION
    elif units == 'V':
        waveform = config.adc16_to_voltage(waveform)
    elif units != 'ADC16':
        raise ValueError("Units must be 'ADC14', 'ADC16', or 'V'.")

    # Sum over samples axis
    sum_waveform = np.sum(waveform, axis=0)

    # Clip if requested (mimic oscilloscope behavior)
    if clip:
        sum_waveform = np.clip(sum_waveform, 0, config.ADC14_MAX * config.ADC14_16_CONVERSION - 1)

    return sum_waveform


def get_max_value_mask(max_values, ptps, cs=None):
    """
    Create mask for events below peak-to-peak threshold.

    Args:
        max_values (np.ndarray): Maximum values (n_events, n_adcs, n_channels)
        ptps (int, float, or array): Peak-to-peak thresholds
        cs (np.ndarray, optional): Channel status (0 = good)

    Returns:
        np.ndarray: Boolean mask (True = below threshold and good channel)
    """
    # Convert ptps to array if needed
    if isinstance(ptps, (int, float)):
        ptps = [ptps] * config.N_ADCS
    elif len(ptps) != config.N_ADCS:
        raise ValueError(f"ptps must be a single value or a list of length {config.N_ADCS}")

    # Create mask for values below threshold
    max_mask = max_values < (np.array(ptps)[np.newaxis, :, np.newaxis])

    # Apply channel status mask if provided
    if cs is not None:
        ch_mask = (cs == 0)[np.newaxis, :, :]
        mask = max_mask & ch_mask
    else:
        mask = max_mask

    return mask


# ----------------------------- #
#    Frequency Analysis         #
# ----------------------------- #

def get_noise_spectra(waveform, mask=None):
    """
    Calculate noise power spectra using FFT.

    Args:
        waveform (np.ndarray): Waveform data (n_events, n_adcs, n_channels, n_samples)
        mask (np.ndarray, optional): Event mask (masked values set to NaN)

    Returns:
        tuple: (freq_bins, power_spectra, power_spectrum, upper_quantile, lower_quantile)
            - freq_bins: Frequency bins in Hz
            - power_spectra: Power spectra for all events
            - power_spectrum: Median power spectrum
            - upper_quantile: 84th percentile
            - lower_quantile: 16th percentile
    """
    # Apply mask if provided
    if mask is not None:
        waveform = np.where(mask[..., np.newaxis], waveform, np.nan)

    n_samples = waveform.shape[3]

    # Calculate FFT and power spectrum
    fft_N = rfft(waveform, axis=-1) / int(n_samples / 2 + 1)
    power_spectra = 2 * np.abs(fft_N)**2

    # Calculate quantiles (median and 68% range)
    upper_quantile, power_spectrum, lower_quantile = np.nanquantile(
        power_spectra, [0.84, 0.5, 0.16], axis=0
    )

    # Calculate frequency bins
    freq_bins = rfftfreq(n_samples, d=config.SAMPLE_RATE * 1e-6)

    return freq_bins, power_spectra, power_spectrum, upper_quantile, lower_quantile


# ----------------------------- #
#    Event Selection            #
# ----------------------------- #

def select_events_by_trigger(events_data, trig_type):
    """
    Select events by trigger type.

    Args:
        events_data: HDF5 events dataset
        trig_type (int): Trigger type (0 = self-trigger, 1 = beam)

    Returns:
        np.ndarray: Indices of events with specified trigger type
    """
    return np.where(events_data['trig_type'] == trig_type)[0]


def get_equidistant_indices(total_events, max_events):
    """
    Get equidistant event indices for sampling.

    Args:
        total_events (int): Total number of events available
        max_events (int): Maximum number of events to select

    Returns:
        np.ndarray: Array of equidistant indices
    """
    if max_events >= total_events:
        return np.arange(total_events)

    indices = np.linspace(0, total_events - 1, max_events, dtype=int)
    return np.unique(indices)


# ----------------------------- #
#    Interesting Event Finding  #
# ----------------------------- #

def find_interesting_events(wvfms, baselines, ptps_16):
    """
    Find potentially interesting events for visualization.

    Returns events with:
    - Largest total integral
    - Most samples over threshold
    - Largest consecutive sample difference

    Args:
        wvfms (np.ndarray): Waveform data
        baselines (np.ndarray): Baseline values
        ptps_16 (np.ndarray): Peak-to-peak thresholds in ADC16

    Returns:
        dict: Dictionary with event indices for different criteria
    """
    results = {}

    # Event with largest total integral
    integrals = np.sum(wvfms, axis=(1, 2, 3))
    results['max_integral'] = np.argmax(integrals)

    # Event with most samples over noise threshold
    samples_over_th = wvfms > ptps_16[np.newaxis, :, np.newaxis, np.newaxis]
    nsamples_over_th = np.sum(samples_over_th, axis=(1, 2, 3))
    results['max_samples_over_th'] = np.argmax(nsamples_over_th)

    # Event with largest difference between consecutive samples
    diffs = np.abs(np.diff(wvfms, axis=-1))
    max_diffs = np.max(diffs, axis=(1, 2, 3))
    results['max_diff'] = np.argmax(max_diffs)

    logger.debug(f"Interesting events found: {results}")

    return results
