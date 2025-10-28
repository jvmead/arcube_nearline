# Light DQM Refactoring - Version 2.0

## Overview

The Light DQM (Data Quality Monitoring) package has been completely refactored from a single monolithic script (~2300 lines) into a well-organized Python package with modular components.

## Package Structure

```
actions/light_dqm/
├── __init__.py                 # Package initialization
├── config.py                   # Configuration constants and settings
├── utils.py                    # Utility functions (statistics, I/O)
├── data_processing.py          # Waveform processing functions
├── plotting.py                 # All plotting functions (13 functions)
├── quality_checks.py           # Data quality check functions
├── light_dqm.py               # Main script (refactored)
├── ascii.py                    # ASCII art header/footer
├── extract_plotting.py         # Helper script for extraction
├── channel_status.csv          # Channel status data
├── channel_status_warmRun2.csv # Warm run channel status
├── bbaseln_dchan.json          # Baseline data
└── v3_FOAS-2.json             # Configuration data
```

## Modules

### 1. `config.py` - Configuration and Constants
**Purpose**: Centralizes all configuration constants, default values, and unit conversion functions.

**Key Contents**:
- Physical constants (SAMPLE_RATE, ADC specifications)
- Channel configuration (CHANNELS, N_ADCS, N_CHANNELS)
- Frequency analysis settings (FREQ_ROIS_MHZ, FREQ_WINDOW_MHZ)
- Threshold defaults (DEFAULT_PTPS_16BIT, BASELINE_THRESHOLD_ADC16)
- Unit conversion functions (`get_ptps()`, `adc16_to_voltage()`)
- Baseline expected ranges
- Plot configuration settings

### 2. `utils.py` - Utility Functions
**Purpose**: Provides helper functions for statistical calculations, file I/O, and data management.

**Key Functions**:
- `clopper_pearson()`: Calculate Clopper-Pearson confidence intervals
- `load_channel_status()`: Load channel status from CSV
- `save_as_json()` / `read_from_json()`: Save/load general data
- `save_eff_as_json()` / `read_eff_from_json()`: Save/load efficiency data
- `save_spectra_as_json()`: Save frequency spectra data
- `ensure_directory_exists()`: Directory management
- `find_flow_files()`: File discovery

### 3. `data_processing.py` - Waveform Processing
**Purpose**: Contains all waveform processing and analysis functions.

**Key Functions**:
- `get_waveform_info()`: Extract comprehensive waveform information (noise, baseline, max values, clipping, negatives)
- `get_sum_waveform()`: Calculate sum waveform for visualization
- `get_max_value_mask()`: Create masks for events below threshold
- `get_noise_spectra()`: Calculate noise power spectra using FFT
- `select_events_by_trigger()`: Filter events by trigger type
- `get_equidistant_indices()`: Sample events equidistantly
- `find_interesting_events()`: Find events for visualization

### 4. `plotting.py` - Visualization Functions
**Purpose**: Contains all 13 plotting functions for data visualization.

**Grafana Status Plots**:
- `plot_flatline_mask()`: Plot alive/dead channel status
- `plot_baseline_mask()`: Plot baseline deviation status

**DQM Analysis Plots**:
- `plot_sum_waveform()`: Plot summed waveforms per EPCB
- `plot_noises()`: Plot noise levels by channel
- `plot_baselines()`: Plot baseline values by channel
- `plot_noise_spectra_epcb()`: Plot average noise spectra per EPCB
- `plot_noise_spectra_channels()`: Plot channel-by-channel noise spectra

**Clipping Analysis**:
- `plot_clipped_fraction()`: Total clipped waveform fraction
- `plot_clipped_tpc_fraction()`: Clipped fraction normalized per TPC
- `plot_clipped_epcb_fraction()`: Clipped fraction normalized per EPCB
- `plot_clipped_ch_fraction()`: Clipped fraction per channel

**Negative Spike Analysis**:
- `plot_neg_tpc_fraction()`: Negative spike fraction per TPC
- `plot_neg_epcb_fraction()`: Negative spike fraction per EPCB

**Helper**:
- `placeholder_pdf()`: Create placeholder PDF for errors

### 5. `quality_checks.py` - Quality Check Functions
**Purpose**: Functions for checking data quality issues.

**Key Functions**:
- `check_flatline()`: Detect flatlined (inactive) channels
- `check_baseline()`: Check baseline deviations with detailed status codes:
  - Status -1: Outside expected range
  - Status 1: Current uncertainty too large
  - Status 2: Significant change from previous
  - Status 3: Both 1 and 2

## Key Improvements

### 1. **Modularity**
- Separated concerns into logical modules
- Each module has a clear, focused purpose
- Easy to test and maintain individual components

### 2. **Logging Support**
- Replaced print statements with proper logging
- Configurable log levels
- Better debugging and production monitoring

### 3. **Configuration Management**
- All constants in one place (`config.py`)
- Easy to adjust parameters without code changes
- Consistent naming conventions

### 4. **Code Reusability**
- Functions can be imported and used independently
- Reduced code duplication
- Clear interfaces between modules

### 5. **Documentation**
- Comprehensive docstrings for all functions
- Clear parameter and return value descriptions
- Module-level documentation

### 6. **Error Handling**
- Centralized error handling patterns
- Better exception messages
- Graceful degradation with placeholder PDFs

### 7. **Type Safety**
- Clear expected types in docstrings
- Validation of inputs
- Consistent return types

## Migration Guide

### Old Usage:
```bash
python light_dqm.py --input_path /path/to/data/ --file_syntax mpd_run_ ...
```

### New Usage (same):
```bash
python light_dqm.py --input_path /path/to/data/ --file_syntax mpd_run_ ...
```

The command-line interface remains the same! The refactoring is internal.

### Importing Modules:
```python
# Import the package
from light_dqm import config, utils, data_processing, plotting, quality_checks

# Or import specific functions
from light_dqm.utils import clopper_pearson, load_channel_status
from light_dqm.data_processing import get_waveform_info
from light_dqm.plotting import plot_baselines
from light_dqm.quality_checks import check_flatline

# Access configuration
from light_dqm.config import CHANNELS, N_ADCS, get_ptps
```

## Testing

To verify the refactoring works correctly:

```bash
# Run a test with one file
cd /global/homes/j/jvmead/dune/arcube_nearline
python actions/light_dqm/light_dqm.py \
    --input_path /path/to/test/data/ \
    --file_syntax test_file_ \
    --nfiles 1 \
    --max_evts 100
```

## Removed Files

The following obsolete version files have been removed:
- `light_dqm_v0.py` (949 lines)
- `light_dqm_v1.py` (1376 lines)
- `light_dqm_v2.py` (1436 lines)

These were historical versions that are no longer needed.

## Future Enhancements

Potential improvements for future versions:

1. **Unit Tests**: Add comprehensive test suite
2. **Command-line Interface**: Use `argparse` subcommands for different operations
3. **Configuration Files**: Support YAML/JSON config files
4. **Parallel Processing**: Add multiprocessing for large datasets
5. **Interactive Plots**: Support interactive plotting with Plotly
6. **Database Integration**: Store results in database instead of JSON
7. **REST API**: Create API for programmatic access
8. **Docker Container**: Package as Docker image for easy deployment

## Version History

### Version 2.0.0 (October 2025)
- Complete refactoring into modular package structure
- Added logging support throughout
- Created separate modules for different functionality
- Removed obsolete version files
- Improved documentation and type hints
- Added configuration management

### Previous Versions
- v1.x: Various incremental updates (light_dqm_v0, v1, v2)
- Original: Monolithic script (light_dqm.py, 2321 lines)

## Authors

- James Mead <jmead@nikhef.nl>
- Sindhujha Kumaran <s.kumaran@uci.edu>

## Contact

For questions or issues with the refactored code, please contact the authors or open an issue in the repository.
