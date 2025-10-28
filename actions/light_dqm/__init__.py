"""
DUNE Light Data Quality Monitoring Package

This package provides tools for monitoring and analyzing light detector data
from the DUNE experiment.

Modules:
    config: Configuration constants and settings
    utils: Utility functions for data processing and file I/O
    data_processing: Waveform processing and analysis functions
    plotting: Plotting functions for visualization
    quality_checks: Data quality check functions
"""

__version__ = "2.0.0"
__author__ = "James Mead, Sindhujha Kumaran"
__email__ = "jmead@nikhef.nl, s.kumaran@uci.edu"

# Import key components for convenient access
from . import config
from . import utils
from . import data_processing
from . import plotting
from . import quality_checks

__all__ = [
    'config',
    'utils',
    'data_processing',
    'plotting',
    'quality_checks',
]
