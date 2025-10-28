#!/usr/bin/env python3
"""
Script to extract plotting functions from light_dqm.py and create plotting.py module.

This script automates the extraction of all plot_* functions from the original
light_dqm.py file and creates a properly formatted plotting.py module.
"""

import re
import os

def extract_plotting_functions():
    """Extract all plotting functions from light_dqm.py"""

    # Read the original file
    with open('light_dqm.py', 'r') as f:
        lines = f.readlines()

    # Find all plot function definitions and their line numbers
    plot_functions = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith('def plot_'):
            func_name = line.split('(')[0].replace('def ', '').strip()
            func_lines = [line]
            i += 1
            # Collect function body
            while i < len(lines) and (lines[i].startswith(' ') or lines[i].startswith('\t') or lines[i].strip() == ''):
                func_lines.append(lines[i])
                i += 1
                # Break if we hit another function definition
                if i < len(lines) and lines[i].startswith('def ') and not lines[i-1].strip():
                    break
            plot_functions[func_name] = ''.join(func_lines)
        else:
            i += 1

    return plot_functions

def create_plotting_module(plot_functions):
    """Create plotting.py with all extracted functions"""

    header = '''"""
Plotting functions for Light DQM.

This module contains all plotting functions for visualizing light detector
data quality metrics, including waveforms, baselines, noise spectra,
and quality check results.
"""

import logging
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.lines import Line2D

from . import config
from . import utils

logger = logging.getLogger(__name__)


# ----------------------------- #
#    Grafana Status Plots       #
# ----------------------------- #

'''

    with open('plotting.py', 'w') as f:
        f.write(header)
        for func_name, func_code in plot_functions.items():
            f.write(f"\n{func_code}\n")

    print(f"Created plotting.py with {len(plot_functions)} functions:")
    for func_name in plot_functions.keys():
        print(f"  - {func_name}")

if __name__ == '__main__':
    print("Extracting plotting functions from light_dqm.py...")
    functions = extract_plotting_functions()
    create_plotting_module(functions)
    print(f"\nSuccessfully created plotting.py!")
    print(f"Total functions extracted: {len(functions)}")
