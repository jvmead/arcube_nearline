"""
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


def plot_flatline_mask(flatline_mask, channel_status=None, times=None,
                       output_name='flatline_mask.png', grafana=True):
    n_adcs = flatline_mask.shape[0]
    n_channels = flatline_mask.shape[1]
    fig, ax = plt.subplots(figsize=(14, 3))
    ax.set_xlim(-0.5, n_channels - 0.5)
    ax.set_ylim(-0.5, n_adcs - 0.5)
    ax.set_xticks(np.arange(n_channels))
    ax.set_yticks(np.arange(n_adcs))
    ax.set_xlabel('Channel')
    ax.set_ylabel('ADC')
    ax.set_xticklabels(np.arange(n_channels))
    ax.set_yticklabels(np.arange(n_adcs))

    for i in range(n_adcs):
        for j in range(n_channels):
            alpha = 1.0
            # Skip inactive channels
            if channel_status is not None and channel_status[i, j] == -1:
                continue
            if grafana:
                if channel_status is not None and channel_status[i, j] in [1,3]:
                        ax.plot(j, i, marker='.', color='black', markersize=10)
                elif flatline_mask[i, j]:
                        ax.text(
                            j, i-0.1, "☹️",  # or "😢"
                            color="red",
                            fontsize=14,
                            ha="center",
                            va="center"
                        )
                else:
                    ax.plot(j, i, marker='o', color='green', markersize=10, fillstyle='none')


            else:
                if flatline_mask[i, j]:
                    ax.plot(j, i, marker='x', color='red', markersize=12, markeredgewidth=2)
                else:
                    ax.plot(j, i, marker='o', color='green', markersize=10, fillstyle='none')
                if channel_status is not None and channel_status[i, j] in [1,3]:
                    ax.plot(j, i, marker='.', color='black', markersize=10)


    plt.title("Alive and dead channels", y=1.18, fontsize=14)
    plt.tight_layout()

    # add faded line at x=31.5
    ax.axvline(x=31.5, color='grey', linestyle='-', linewidth=1, alpha=0.5)
    # add faded line at y = 1.5, 3.5, 5.5, 7.5
    for y in range(1, n_adcs):
        if y % 2 == 0:
            ax.axhline(y=y - 0.5, color='grey', linestyle='-', linewidth=1, alpha=0.5)


    legend_handles = [
        Line2D([0], [0], marker='.', color='black', linestyle='None', markersize=10,
               label='Ignore known problem channels'),
        Line2D([0], [0], marker='o', color='green', markerfacecolor='none',
               linestyle='None', markersize=10, label='Still living')
    ]

    if grafana:
        legend_handles.append(
            Line2D([0], [0], linestyle='None', marker=r"$☹$", color='red',
                   markersize=12, markeredgewidth=0.2, label='Dead (contact LRS expert)')
        )
    else:
        legend_handles.append(
            Line2D([0], [0], marker='x', color='red', linestyle='None', markersize=10,
                   label='Dead (contact LRS expert)')
        )

    # Place legend above the plot, in one lineer', bbox_to_anchor=(0.5, -0.35), ncol=3, frameon=False)
    plt.legend(handles=legend_handles, loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=3, frameon=False)
    # add start and end times to the top left
    if times is not None:
        # Place the time text above the plot, aligned with the legend
        ax.text(0.01, 1.15, f'Start: {times[0]}\nEnd:  {times[1]}', transform=ax.transAxes,
                fontsize=10, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
    # Make the figure slightly larger to fit the legend
    fig.set_size_inches(16, 4)
    # Increase the top margin to fit the legend
    plt.subplots_adjust(top=0.82)
    output = f"{output_name}"
    plt.savefig(output)




def plot_baseline_mask(baseline_mask, channel_status=None, times=None,
                       output_name='baseline_mask.png', grafana=True):
    """
    Plot an 8x64 grid with red cross for baseline outliers, green circle for normal.
    Optionally mark known bad channels with a black dot.
    """
    n_adcs = baseline_mask.shape[0]
    n_channels = baseline_mask.shape[1]
    fig, ax = plt.subplots(figsize=(14, 3))
    ax.set_xlim(-0.5, n_channels - 0.5)
    ax.set_ylim(-0.5, n_adcs - 0.5)
    ax.set_xticks(np.arange(n_channels))
    ax.set_yticks(np.arange(n_adcs))
    ax.set_xlabel('Channel')
    ax.set_ylabel('ADC')
    ax.set_xticklabels(np.arange(n_channels))
    ax.set_yticklabels(np.arange(n_adcs))

    for i in range(n_adcs):
        for j in range(n_channels):
            # Skip inactive channels
            if channel_status is not None and channel_status[i, j] == -1:
                continue

            if grafana:
                if channel_status is not None and channel_status[i, j] in [2,3]:
                        ax.plot(j, i, marker='.', color='black', markersize=10)
                elif baseline_mask[i, j]:
                    ax.text(
                        j, i-0.1, "☹️",  # or "😢"
                        color="red",
                        fontsize=14,
                        ha="center",
                        va="center"
                    )

                else:
                    ax.plot(j, i, marker='o', color='green', markersize=10, fillstyle='none')

            else:
                if baseline_mask[i, j]:
                    ax.plot(j, i, marker='x', color='red', markersize=12, markeredgewidth=2)
                else:
                    ax.plot(j, i, marker='o', color='green', markersize=10, fillstyle='none')
                if channel_status is not None and channel_status[i, j] in [2,3]:
                    ax.plot(j, i, marker='.', color='black', markersize=10)

    plt.title("Channels baseline status", y=1.18, fontsize=14)
    plt.tight_layout()
    # add faded line at x=31.5
    ax.axvline(x=31.5, color='grey', linestyle='-', linewidth=1, alpha=0.5)
    # add faded line at y = 1.5, 3.5, 5.5, 7.5
    for y in range(1, n_adcs):
        if y % 2 == 0:
            ax.axhline(y=y - 0.5, color='grey', linestyle='-', linewidth=1, alpha=0.5)
    legend_handles = [
        Line2D([0], [0], marker='.', color='black', linestyle='None', markersize=10,
               label='Ignore known problem channels'),
        Line2D([0], [0], marker='o', color='green', markerfacecolor='none',
               linestyle='None', markersize=10, label='Stable')
    ]

    if grafana:
        legend_handles.append(
            Line2D([0], [0], linestyle='None', marker=r"$☹$", color='red',
                   markersize=12, markeredgewidth=0.2, label='Deviation (contact LRS expert)')
        )
    else:
        legend_handles.append(
            Line2D([0], [0], marker='x', color='red', linestyle='None', markersize=10,
                   label='Deviation (contact LRS expert)')
        )


    plt.legend(handles=legend_handles, loc='upper center', bbox_to_anchor=(0.5, 1.15), ncol=3, frameon=False)
    # add start and end times to the top left
    if times is not None:
        # Place the time text above the plot, aligned with the legend
        ax.text(0.01, 1.15, f'Start: {times[0]}\nEnd:  {times[1]}', transform=ax.transAxes,
                fontsize=10, verticalalignment='top', bbox=dict(facecolor='white', alpha=0.8, edgecolor='none'))
    # Make the figure slightly larger to fit the legend
    fig.set_size_inches(16, 4)
    plt.subplots_adjust(top=0.82)
    output = f"{output_name}"
    plt.savefig(output)




def plot_sum_waveform(waveform, units='ADC16', i_evt=0, output_name='sum_waveform.pdf'):
    # waveform shape: (n_events, n_adcs, n_channels, n_samples)
    n_epcbs = int(len(channels) // 6)
    n_adcs = waveform.shape[1]
    n_samples = waveform.shape[3]
    nrows = n_adcs * (n_epcbs // 2)
    ncols = 2
    _, axes = plt.subplots(nrows, ncols, figsize=(20, 2 * nrows), sharex=True)

    # Ensure axes is always 2D
    if nrows == 1:
        axes = np.expand_dims(axes, axis=0)
    if ncols == 1:
        axes = np.expand_dims(axes, axis=1)

    for i in range(n_adcs):
        for j in range(n_epcbs):
            idx = i * (n_epcbs // 2) + (j // 2)
            tt_idx = j % 2
            channels_list = channels[j * 6:(j + 1) * 6]
            # Extract waveform for this event, ADC, and EPCB channels
            epcb_waveform = waveform[i_evt, i, channels_list, :]
            # loop over channels
            for ch in range(len(channels_list)):
                axes[idx, tt_idx].plot(epcb_waveform[ch, :], label=f'Channel {channels_list[ch]}')
            # plot total
            sum_wvfm = get_sum_waveform(epcb_waveform, units=units)
            # set title
            axes[idx, tt_idx].set_title(f'Event {i_evt} - Non-beam trigger timing')
            axes[idx, tt_idx].plot(sum_wvfm, color='black', alpha=0.5, label='Sum ADC')
            axes[idx, tt_idx].set_title(f'ADC {i} - EPCB {j} summed waveforms')
            axes[idx, tt_idx].set_ylabel(f'{units} counts')
            axes[idx, tt_idx].legend(loc='upper right', fontsize='small')
            axes[idx, tt_idx].grid(True)
            axes[idx, tt_idx].set_xlim(0, n_samples)
            axes[idx, tt_idx].set_ylim(-5000, 70000)
    axes[-1, 0].set_xlabel('Samples/ time (ticks)')
    axes[-1, 1].set_xlabel('Samples/ time (ticks)')
    plt.tight_layout()
    plt.show()
    # save as pdf
    output_pdf = f"{args.tmp_dir}/{output_name}"
    with PdfPages(output_pdf) as pdf:
        pdf.savefig()
        plt.close()




def plot_noises(prev_noises, noises, i_evt, mask_inactive=True,
                format_bad_channels=True, output_name='noises.pdf'):
    n_adcs = noises.shape[1]
    axes = plt.subplots(n_adcs, 1, figsize=(10, 2*n_adcs), sharex=True)[1]

    medians = np.median(noises[i_evt,:,:], axis=0)
    lowers = np.percentile(noises[i_evt,:,:], 16, axis=0) - medians
    uppers = np.percentile(noises[i_evt,:,:], 84, axis=0) - medians

    for i in range(n_adcs):
        ax = axes[i]
        channels_idx = np.arange(noises.shape[2])
        # mask inactive channels
        if mask_inactive:
            mask = np.isin(channels_idx, channels)
        else:
            mask = np.ones_like(channels_idx, dtype=bool)
        # Default values
        median = np.full(noises.shape[2], np.nan)
        lower  = np.full(noises.shape[2], np.nan)
        upper  = np.full(noises.shape[2], np.nan)

        if isinstance(i_evt, np.ndarray) and len(i_evt) > 1:
            # Get 68% central quantile range (16th and 84th percentiles)
            median = medians[i, :]
            lower = -lowers[i, :]
            upper = uppers[i, :]
            # Set alpha to 0.5 for bad channels (cs != 0)
            if format_bad_channels and cs.shape == (n_adcs, len(channels_idx)):
                alphas = np.ones_like(median)
                bad_mask = cs[i, :] != 0
                alphas[bad_mask] = 0.25
                # Plot previous files with error bars
                if prev_noises is not None:
                    prev_centre, prev_lower, prev_upper = prev_noises
                    prev_centre = prev_centre[i, mask]
                    prev_lower = prev_lower[i, mask]
                    prev_upper = prev_upper[i, mask]
                    for ch, c, l, u in zip(
                        channels_idx[mask], prev_centre, prev_lower, prev_upper
                    ):
                        ax.step(
                            [ch - 0.5, ch + 0.5], [c, c],
                            color='red', alpha=alphas[ch]/2, where='post', linewidth=1
                        )
                        ax.fill_between(
                            [ch - 0.5, ch + 0.5], [c - l, c - l], [c + u, c + u],
                            color='red', alpha=alphas[ch]/4, step='post'
                        )
                # Plot current noise with error bars
                for ch in channels_idx[mask]:
                    ax.errorbar(
                        ch, median[ch], yerr=[[lower[ch]], [upper[ch]]],
                        fmt='.', color='b', markersize=5,
                        linewidth=0.5, capsize=5, capthick=1,
                        alpha=alphas[ch]
                    )
        # formatting
        ax.set_title(f'ADC {i} Noise')
        ax.set_ylabel('Noise (ADC counts)')
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    axes[-1].set_xlabel('channel #')
    # adjust layout
    plt.tight_layout()

    # save as pdf
    output_pdf = f"{args.tmp_dir}/{output_name}"
    with PdfPages(output_pdf) as pdf:
        pdf.savefig()
        plt.close()
    return medians, lowers, uppers




def plot_baselines(prev_baselines, baselines, i_evt, mask_inactive=True,
                   format_bad_channels=True, output_name='baselines.pdf'):
    n_adcs = baselines.shape[1]
    axes = plt.subplots(n_adcs, 1, figsize=(10, 2*n_adcs), sharex=True)[1]
    # Initialize arrays to store median, lower, and upper bounds
    medians = np.median(baselines[i_evt,:,:], axis=0)
    lowers = np.percentile(baselines[i_evt,:,:], 16, axis=0) - medians
    uppers = np.percentile(baselines[i_evt,:,:], 84, axis=0) - medians
    # Loop over each ADC
    for i in range(n_adcs):
        ax = axes[i]
        channels_idx = np.arange(baselines.shape[2])
        # mask inactive channels
        if mask_inactive:
            mask = np.isin(channels_idx, channels)
        else:
            mask = np.ones_like(channels_idx, dtype=bool)

        if isinstance(i_evt, np.ndarray) and len(i_evt) > 1:
            # Get 68% central quantile range (16th and 84th percentiles)
            median = medians[i, mask]
            lower = -lowers[i, mask]
            upper = uppers[i, mask]

            # Set alpha to 0.5 for bad channels (cs != 0)
            if format_bad_channels and cs.shape == (n_adcs, len(channels_idx)):
                alphas = np.ones_like(median)
                bad_mask = cs[i, :] != 0
                alphas[bad_mask] = 0.25

                # Plot previous files with error bars
                if prev_baselines is not None:
                    prev_centre, prev_lower, prev_upper = prev_baselines
                    prev_centre = prev_centre[i, mask]
                    prev_lower = prev_lower[i, mask]
                    prev_upper = prev_upper[i, mask]
                    for ch, c, l, u in zip(
                        channels_idx[mask], prev_centre, prev_lower, prev_upper
                    ):
                        ax.step(
                            [ch - 0.5, ch + 0.5], [c, c],
                            color='red', alpha=alphas[ch]/2, where='post', linewidth=1
                        )
                        ax.fill_between(
                            [ch - 0.5, ch + 0.5], [c - l, c - l], [c + u, c + u],
                            color='red', alpha=alphas[ch]/4, step='post'
                        )
                # Plot current baseline with error bars
                for ch in channels_idx[mask]:
                    ax.errorbar(
                        ch, median[ch], yerr=[[lower[ch]], [upper[ch]]],
                        fmt='.', color='b', markersize=5,
                        linewidth=0.5, capsize=5, capthick=1,
                        alpha=alphas[ch]
                    )
        # formatting
        ax.set_title(f'ADC {i} Baselines')
        ax.set_ylabel('Baseline (ADC counts)')
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # adjust layout
    axes[-1].set_xlabel('channel #')
    plt.tight_layout()
    # save as pdf
    output_pdf = f"{args.tmp_dir}/{output_name}"
    with PdfPages(output_pdf) as pdf:
        pdf.savefig()
        plt.close()
    return medians, lowers, uppers




def plot_noise_spectra_epcb(
    freq_bins, noise_spectra, upper_quantile, lower_quantile,
    skip_bad_channels=True, nevts=None, output_name='noise_spectra_epcb.pdf'):

    n_epcbs = int(len(channels)/6)
    n_adcs = noise_spectra.shape[0]
    axes = plt.subplots(n_adcs, 1, figsize=(20, 2*n_adcs), sharex=True)[1]

    # Mask the first frequency bin (set to nan)
    freq_mask = np.ones_like(freq_bins, dtype=bool)
    freq_mask[0] = False

    for i in range(n_adcs):
        for j in range(n_epcbs):
            idx = i
            # Mask for epcb channels
            epcb_mask = np.zeros(noise_spectra.shape[1], dtype=bool)
            channels_list = channels[j*6:(j+1)*6]
            epcb_mask[channels_list] = True
            # Mask for good channels
            if skip_bad_channels and cs.shape == (n_adcs, len(channels_list)):
                ch_mask = (cs[i, :] == 0)
            else:
                ch_mask = np.ones(noise_spectra.shape[1], dtype=bool)
            ch_mask = np.logical_and(ch_mask, epcb_mask)

            # Average over channels
            avg = np.nanmean(noise_spectra[i, ch_mask], axis=0)
            axes[idx].step(
                freq_bins[freq_mask]/1e6,
                avg[freq_mask],
                where='mid',
                label=f'EPCB {j}'
            )

            axes[idx].set_title(f'ADC {i}, Average Noise Spectrum per EPCB: equidistant {nevts} events')
            axes[idx].set_ylabel('V^2 / bin')
            axes[idx].set_yscale('log')
            axes[idx].set_ylim(5e-10, 1e-5)
            axes[idx].set_xlim(0, 31.25)
            axes[idx].legend(loc='upper right', fontsize='x-small')

            # add grid lines
            axes[idx].grid(True, which='major', linestyle='-', linewidth=0.5)

    axes[-1].set_xlabel('Frequency (MHz)')
    plt.tight_layout()
    plt.show()
    # save as pdf
    output_pdf = f"{args.tmp_dir}/{output_name}"
    with PdfPages(output_pdf) as pdf:
        pdf.savefig()
        plt.close()



def plot_noise_spectra_channels(
    freq_bins, noise_spectra, skip_bad_channels=True,
    nevts=None, output_name='noise_spectra_channels.pdf'):

    n_epcbs = int(len(channels)/6)
    n_adcs = noise_spectra.shape[0]
    axes = plt.subplots(n_adcs*n_epcbs, 1, figsize=(20, 2*n_adcs*n_epcbs), sharex=True)[1]

    # Mask the first frequency bin (set to nan)
    freq_mask = np.ones_like(freq_bins, dtype=bool)
    freq_mask[0] = False

    # defining regions of interest
    vlist = [0.5e6, 1.8e6, 4.6e6, 7.1e6, 8.5e6, 10e6, 11.5e6, 19e6, 20e6, 25e6, 30e6]
    window = 0.4e6

    for i in range(n_adcs):
        for j in range(n_epcbs):
            idx = i * n_epcbs + j
             # mask for epcb channels
            epcb_mask = np.zeros(noise_spectra.shape[1], dtype=bool)
            channels_list = channels[j*6:(j+1)*6]
            epcb_mask[channels_list] = True
            # Mask for good channels
            if skip_bad_channels and cs.shape == (n_adcs, len(channels_list)):
                ch_mask = (cs[i, :] == 0)
            else:
                ch_mask = np.ones(noise_spectra.shape[1], dtype=bool)
            ch_mask = np.logical_and(ch_mask, epcb_mask)

            # Plot each epcb
            for k in ch_mask.nonzero()[0]:

                # plot step for centre line and fill between for error bands
                axes[idx].step(
                    freq_bins[freq_mask]/1e6,
                    noise_spectra[i, k][freq_mask],
                    where='mid', label=f'Channel {k}'
                )

            # Add horizontal line at the minimum value
            min_val = np.nanmin(noise_spectra[i, :, freq_mask])
            axes[idx].axhline(y=min_val, color='k', linestyle='--')
            axes[idx].set_title(f'ADC {i} EPCB {j} average noise spectrum: equidistant {nevts} events')
            axes[idx].legend(loc='upper right', fontsize='small')

            axes[idx].set_ylabel('V^2 / bin')
            axes[idx].set_yscale('log')
            axes[idx].grid(True, which='major', linestyle='-', linewidth=0.5)
            axes[idx].set_ylim(5e-10, 1e-5)
            axes[idx].set_xlim(0, 31.25)

    axes[-1].set_xlabel('Frequency (MHz)')
    plt.tight_layout()
    plt.show()
    # save as pdf
    output_pdf = f"{args.tmp_dir}/{output_name}"
    with PdfPages(output_pdf) as pdf:
        pdf.savefig()
        plt.close()




def plot_clipped_fraction(prev_clipped_evts, clipped_evts, title=None,
                          output_name='clipped_fraction.pdf'):
    n_evts = clipped_evts.shape[0]
    n_adcs = clipped_evts.shape[1]
    n_chs = clipped_evts.shape[2]
    axes = plt.subplots(n_adcs, 1, figsize=(10, 2*n_adcs), sharex=True)[1]
    # initialize arrays to store numerator and denominator for each ADC
    clip_passed = np.zeros((n_adcs, n_chs))
    total_evts = np.zeros((n_adcs, n_chs))

    # Define channels to plot
    for i_adc in range(n_adcs):
        ax = axes[i_adc]

        # Calculate clipped counts for this ADC
        clipped_counts = np.sum(clipped_evts[:,i_adc,:], axis=0)
        # get total events for this file
        total_events = np.array([n_evts] * n_chs) # total events per channel

        # Avoid division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            clipped_pct = 100 * clipped_counts / total_events
            clipped_pct = np.nan_to_num(clipped_pct, nan=0.0)

        # Clopper-Pearson interval (binomial proportion confidence interval)
        clipped_pct, err_low, err_up = clopper_pearson(clipped_counts, total_events)
        ylabel = 'Clipped (% total)'
        ymax = 0

        # define alpha 0.25 for cs!=0
        alphas = np.ones_like(clipped_pct)
        if cs.shape == (n_adcs, n_chs):
            bad_mask = cs[i_adc, :] != 0
            alphas[bad_mask] = 0.25
        # Plot each point individually to allow per-point alpha
        for idx in channels:
            # previous clipped events
            if prev_clipped_evts is not None:
                prev_centre, prev_lower, prev_upper = prev_clipped_evts
                c = prev_centre[i_adc, idx]
                l = prev_lower[i_adc, idx]
                u = prev_upper[i_adc, idx]
                ax.step(
                    [idx - 0.5, idx + 0.5], [c, c],
                    color='red', alpha=alphas[idx]/2, where='post', linewidth=1
                )
                ax.fill_between(
                    [idx - 0.5, idx + 0.5], [c - l, c - l], [c + u, c + u],
                    color='red', alpha=alphas[idx]/4, step='post'
                )
            color = 'b'

            # point + Clopper–Pearson error bars
            yerr_lower = err_low[idx]
            yerr_upper = err_up[idx]
            ax.errorbar(
                idx, clipped_pct[idx],
                yerr=[[yerr_lower], [yerr_upper]],
                fmt='.', ecolor=color, markersize=5,
                capsize=4, linewidth=1, color=color,
                alpha=alphas[idx]
            )
            if clipped_pct[idx] + yerr_upper < 100.0:
                if (ymax < clipped_pct[idx] + yerr_upper):
                    ymax = clipped_pct[idx] + yerr_upper
            if prev_clipped_evts is not None and (c + u < 100.0):
                if (ymax < c + u):
                    ymax = c + u

        # get y-lim from data (excluding values with 0 clipped events)
        ax.set_ylim(0, ymax*1.1 if (ymax < 90 and ymax != 0)
                        else (1 if ymax == 0 else 100))

        # formatting
        ax.set_title(f'ADC {i_adc} - {title}' if title else f'ADC {i_adc}')
        ax.set_ylabel(ylabel)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)

        # save clipped numerator and denominator for later use
        clip_passed[i_adc, :] = clipped_counts
        total_evts[i_adc, :] = total_events
    axes[-1].set_xlabel('channel #')
    plt.tight_layout()
    plt.show()
    # save as pdf
    output_pdf = f"{args.tmp_dir}/{output_name}"
    with PdfPages(output_pdf) as pdf:
        pdf.savefig()
        plt.close()
    return clip_passed, total_events




def plot_clipped_tpc_fraction(prev_clipped_evts, clipped_evts, max_vals, ths,
                              title=None, output_name='clipped_tpc_fraction.pdf'):
    n_adcs = clipped_evts.shape[1]
    axes = plt.subplots(n_adcs, 1, figsize=(10, 2*n_adcs), sharex=True)[1]
    # initialize arrays to store numerator and denominator for each ADC
    clip_passed = np.zeros((n_adcs, 64))
    total_evts = np.zeros((n_adcs, 64))

    # loop over each ADC
    for i_adc in range(n_adcs):
        ax = axes[i_adc]

        # get total events for this file: for each TPC, count events where any channel in the TPC is over ptps
        total_events = np.zeros((64), dtype=int)

        # Calculate clipped counts for this ADC
        clipped_counts = np.sum(clipped_evts[:, i_adc, :], axis=0)
        dir = 1 if i_adc % 2 == 0 else -1
        tpc_range = [i_adc, i_adc + dir]

        # Loop over each TPC
        for i_tpc in tpc_range:
            # Each TPC is associated with two ADCs and 32 channels
            dir = 1 if i_tpc % 2 == 0 else -1
            adc_idx = [i_tpc, i_tpc + dir]
            ch_idx = range(0, 32) if i_tpc % 2 == 0 else range(32, 64)
            # Select the relevant max_vals for these ADCs and channels
            mv = max_vals[:, adc_idx, :][:, :, ch_idx]  # shape: (n_events, 2, 32)
            ptps_sel = ths[adc_idx][:, np.newaxis]  # shape: (2, 1)
            # Find events where any channel in the TPC is over ptps
            over_ptps = np.any(mv > ptps_sel, axis=(1, 2))  # shape: (n_events,)
            count = np.sum(over_ptps)
            for ch in ch_idx:
                total_events[ch] = count

        # Clopper-Pearson interval (binomial proportion confidence interval)
        clipped_pct, err_low, err_up = clopper_pearson(clipped_counts, total_events)
        ylabel = 'Clipped (% TPC)'
        ymax = 0

        # define alpha 0.25 for cs!=0
        alphas = np.ones_like(cs[i_adc, :])
        bad_mask = cs[i_adc, :] != 0
        alphas[bad_mask] = 0.25

        # Plot each point individually to allow per-point alpha
        for idx in channels:
            # previous clipped events
            if prev_clipped_evts is not None:
                prev_centre, prev_lower, prev_upper = prev_clipped_evts
                c = prev_centre[i_adc, idx]
                l = prev_lower[i_adc, idx]
                u = prev_upper[i_adc, idx]
                ax.step(
                    [idx - 0.5, idx + 0.5], [c, c],
                    color='red', alpha=alphas[idx]/2, where='post', linewidth=1
                )
                ax.fill_between(
                    [idx - 0.5, idx + 0.5], [c - l, c - l], [c + u, c + u],
                    color='red', alpha=alphas[idx]/4, step='post'
                )
            color = 'b'

            # point + Clopper–Pearson error bars
            yerr_lower = err_low[idx]
            yerr_upper = err_up[idx]
            ax.errorbar(
                idx, clipped_pct[idx],
                yerr=[[yerr_lower], [yerr_upper]],
                fmt='.', ecolor=color, markersize=5,
                capsize=4, linewidth=1, color=color,
                alpha=alphas[idx]
            )
            if clipped_pct[idx] + yerr_upper < 100.0:
                if (ymax < clipped_pct[idx] + yerr_upper):
                    ymax = clipped_pct[idx] + yerr_upper
            if prev_clipped_evts is not None and (c + u < 100.0):
                if (ymax < c + u):
                    ymax = c + u

        # get y-lim from data (excluding values with 0 clipped events)
        ax.set_ylim(0, ymax*1.1 if (ymax < 90 and ymax != 0)
                        else (1 if ymax == 0 else 100))

        # formatting
        ax.set_title(f'ADC {i_adc} - {title}' if title else f'ADC {i_adc}')
        ax.set_ylabel(ylabel)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)

        # save clipped numerator and denominator for later use
        clip_passed[i_adc, :] = clipped_counts
        total_evts[i_adc, :] = total_events
    axes[-1].set_xlabel('channel #')
    plt.tight_layout()
    plt.show()
    # save as pdf
    output_pdf = f"{args.tmp_dir}/{output_name}"
    with PdfPages(output_pdf) as pdf:
        pdf.savefig()
        plt.close()
    return clip_passed, total_evts




def plot_clipped_epcb_fraction(prev_clipped_evts, clipped_evts, max_vals, ths,
                               title=None, output_name='clipped_epcb_fraction.pdf'):
    n_adcs = clipped_evts.shape[1]
    axes = plt.subplots(n_adcs, 1, figsize=(10, 2*n_adcs), sharex=True)[1]
    # Initialize arrays to store numerator and denominator for each ADC
    clip_passed = np.zeros((n_adcs, 64))
    total_evts = np.zeros((n_adcs, 64))

    # Calculate max_values for each ADC
    for i_adc in range(n_adcs):
        ax = axes[i_adc]

        # get total events for this adc with max_values > ptps
        clipped_events = np.zeros((64))
        total_events = np.zeros((64))
        for i_epcb in range(8):
            channel_indices = channels[i_epcb * 6: (i_epcb + 1) * 6]
            channel_mask = np.zeros(64, dtype=bool)
            channel_mask[channel_indices] = True
            over_ptps = np.any(max_vals[:, i_adc, :]*channel_mask > ths[np.newaxis, i_adc, np.newaxis], axis=-1)
            total_events[channel_indices] = np.sum(over_ptps, axis=0)
            clipped_events[channel_indices] = (
                clipped_evts[:, i_adc, channel_mask][over_ptps].sum(axis=0)
            )

        # Clopper-Pearson interval (binomial proportion confidence interval)
        clipped_pct, err_low, err_up = clopper_pearson(clipped_events, total_events)
        ylabel = 'Clipped (% EPCB)'
        ymax = 0

        # define alpha 0.25 for cs!=0
        alphas = np.ones_like(cs[i_adc, :])
        bad_mask = cs[i_adc, :] != 0
        alphas[bad_mask] = 0.25

        # Plot each point individually to allow per-point alpha
        for idx in channels:
            # previous clipped events
            if prev_clipped_evts is not None:
                prev_centre, prev_lower, prev_upper = prev_clipped_evts
                c = prev_centre[i_adc, idx]
                l = prev_lower[i_adc, idx]
                u = prev_upper[i_adc, idx]
                ax.step(
                    [idx - 0.5, idx + 0.5], [c, c],
                    color='red', alpha=alphas[idx]/2, where='post', linewidth=1
                )
                ax.fill_between(
                    [idx - 0.5, idx + 0.5], [c - l, c - l], [c + u, c + u],
                    color='red', alpha=alphas[idx]/4, step='post'
                )
            color = 'b'

            # point + Clopper–Pearson error bars
            yerr_lower = err_low[idx]
            yerr_upper = err_up[idx]
            ax.errorbar(
                idx, clipped_pct[idx],
                yerr=[[yerr_lower], [yerr_upper]],
                fmt='.', ecolor=color, markersize=5,
                capsize=4, linewidth=1, color=color,
                alpha=alphas[idx]
            )
            if clipped_pct[idx] + yerr_upper < 100.0:
                if (ymax < clipped_pct[idx] + yerr_upper):
                    ymax = clipped_pct[idx] + yerr_upper
            if prev_clipped_evts is not None and (c + u < 100.0):
                if (ymax < c + u):
                    ymax = c + u

        # get y-lim from data (excluding values with 0 clipped events)
        ax.set_ylim(0, ymax*1.1 if (ymax < 90 and ymax != 0)
                        else (1 if ymax == 0 else 100))

        # formatting
        ax.set_title(f'ADC {i_adc} - {title}' if title else f'ADC {i_adc}')
        ax.set_ylabel(ylabel)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)

        # save clipped numerator and denominator for later use
        clip_passed[i_adc, :] = clipped_events
        total_evts[i_adc, :] = total_events
    axes[-1].set_xlabel('channel #')
    plt.tight_layout()
    plt.show()
    # save as pdf
    output_pdf = f"{args.tmp_dir}/{output_name}"
    with PdfPages(output_pdf) as pdf:
        pdf.savefig()
        plt.close()
    return clip_passed, total_evts




def plot_clipped_ch_fraction(prev_clipped_evts, clipped_evts, max_vals, ths,
                             title=None, output_name='clipped_ch_fraction.pdf'):
    n_adcs = clipped_evts.shape[1]
    axes = plt.subplots(n_adcs, 1, figsize=(10, 2*n_adcs), sharex=True)[1]

    # Initialize arrays to store numerator and denominator for each ADC
    clip_passed = np.zeros((n_adcs, 64))
    total_evts = np.zeros((n_adcs, 64))

    # Calculate max_values for each ADC
    for i_adc in range(n_adcs):
        ax = axes[i_adc]

        # Calculate clipped counts for this ADC
        clipped_counts = np.sum(clipped_evts[:,i_adc,:], axis=0)
        # get total events for this adc with max_values > ptps
        total_events = np.sum(max_vals[:, i_adc, :] > ths[np.newaxis, i_adc, np.newaxis], axis=0)

        # Clopper-Pearson interval (binomial proportion confidence interval)
        clipped_pct, err_low, err_up = clopper_pearson(clipped_counts, total_events)
        ylabel = 'Clipped (%)'
        ymax = 0

        # define alpha 0.25 for cs!=0
        alphas = np.ones_like(cs[i_adc, :])
        bad_mask = cs[i_adc, :] != 0
        alphas[bad_mask] = 0.25

        # Plot each point individually to allow per-point alpha
        for idx in channels:
            # previous clipped events
            if prev_clipped_evts is not None:
                prev_centre, prev_lower, prev_upper = prev_clipped_evts
                c = prev_centre[i_adc, idx]
                l = prev_lower[i_adc, idx]
                u = prev_upper[i_adc, idx]
                ax.step(
                    [idx - 0.5, idx + 0.5], [c, c],
                    color='red', alpha=alphas[idx]/2, where='post', linewidth=1
                )
                ax.fill_between(
                    [idx - 0.5, idx + 0.5], [c - l, c - l], [c + u, c + u],
                    color='red', alpha=alphas[idx]/4, step='post'
                )
            color = 'b'

            # point + Clopper–Pearson error bars
            yerr_lower = err_low[idx]
            yerr_upper = err_up[idx]
            ax.errorbar(
                idx, clipped_pct[idx],
                yerr=[[yerr_lower], [yerr_upper]],
                fmt='.', ecolor=color, markersize=5,
                capsize=4, linewidth=1, color=color,
                alpha=alphas[idx]
            )
            if clipped_pct[idx] + yerr_upper < 100.0:
                if (ymax < clipped_pct[idx] + yerr_upper):
                    ymax = clipped_pct[idx] + yerr_upper
            if prev_clipped_evts is not None and (c + u < 100.0):
                if (ymax < c + u):
                    ymax = c + u

        # get y-lim from data (excluding values with 0 clipped events)
        ax.set_ylim(0, ymax*1.1 if (ymax < 90 and ymax != 0)
                        else (1 if ymax == 0 else 100))

        # formatting
        ax.set_title(f'ADC {i_adc} - {title}' if title else f'ADC {i_adc}')
        ax.set_ylabel(ylabel)
        ax.grid(True, which='both', linestyle='--', linewidth=0.5)

        # save numerator and denominator for later use
        clip_passed[i_adc, :] = clipped_counts
        total_evts[i_adc, :] = total_events
    axes[-1].set_xlabel('channel #')
    plt.tight_layout()
    plt.show()
    # save as pdf
    output_pdf = f"{args.tmp_dir}/{output_name}"
    with PdfPages(output_pdf) as pdf:
        pdf.savefig()
        plt.close()
    return clip_passed, total_evts




def plot_neg_tpc_fraction(prev_neg_evts, neg_evts, max_vals, ths,
                          title=None, output_name='neg_tpc_fraction.pdf'):
  n_adcs = neg_evts.shape[1]
  axes = plt.subplots(n_adcs, 1, figsize=(10, 2*n_adcs), sharex=True)[1]

  # Initialize arrays to store numerator and denominator for each ADC
  neg_passed = np.zeros((n_adcs, 64))
  total_evts = np.zeros((n_adcs, 64))

  for i_adc in range(n_adcs):
    ax = axes[i_adc]

    # get total events for this file: for each TPC, count events where any channel in the TPC is over ptps
    total_events = np.zeros((64), dtype=int)

    # Calculate negative spike counts for this ADC
    neg_counts = np.sum(neg_evts[:, i_adc, :], axis=0)
    dir = 1 if i_adc % 2 == 0 else -1
    tpc_range = [i_adc, i_adc + dir]

    for i_tpc in tpc_range:
      dir = 1 if i_tpc % 2 == 0 else -1
      adc_idx = [i_tpc, i_tpc + dir]
      ch_idx = range(0, 32) if i_tpc % 2 == 0 else range(32, 64)
      mv = max_vals[:, adc_idx, :][:, :, ch_idx]
      ptps_sel = ths[adc_idx][:, np.newaxis]
      over_ptps = np.any(mv > ptps_sel, axis=(1, 2))
      count = np.sum(over_ptps)
      for ch in ch_idx:
        total_events[ch] = count

    # Clopper-Pearson interval (binomial proportion confidence interval)
    neg_pct, err_low, err_up = clopper_pearson(neg_counts, total_events)
    ylabel = '-ve baseline (% TPC)'
    ymax = 0

    # define alpha 0.25 for cs!=0
    alphas = np.ones_like(cs[i_adc, :])
    bad_mask = cs[i_adc, :] != 0
    alphas[bad_mask] = 0.25

    # Plot each point individually to allow per-point alpha
    for idx in channels:
        # previous negative events
        if prev_neg_evts is not None:
            prev_centre, prev_lower, prev_upper = prev_neg_evts
            c = prev_centre[i_adc, idx]
            l = prev_lower[i_adc, idx]
            u = prev_upper[i_adc, idx]
            ax.step(
                [idx - 0.5, idx + 0.5], [c, c],
                color='red', alpha=alphas[idx]/2, where='post', linewidth=1
            )
            ax.fill_between(
                [idx - 0.5, idx + 0.5], [c - l, c - l], [c + u, c + u],
                color='red', alpha=alphas[idx]/4, step='post'
            )
        # current file
        color = 'b'

        # point + Clopper–Pearson error bars
        yerr_lower = err_low[idx]
        yerr_upper = err_up[idx]
        ax.errorbar(
            idx, neg_pct[idx],
            yerr=[[yerr_lower], [yerr_upper]],
            fmt='.', ecolor=color, markersize=5,
            capsize=4, linewidth=1, color=color,
            alpha=alphas[idx]
        )
        if neg_pct[idx] + yerr_upper < 100.0:
            if (ymax < neg_pct[idx] + yerr_upper):
                ymax = neg_pct[idx] + yerr_upper
        if prev_neg_evts is not None and (c + u < 100.0):
            if (ymax < c + u):
                ymax = c + u

    # get y-lim from data (excluding values with 0 clipped events)
    ax.set_ylim(0, ymax*1.1 if (ymax < 90 and ymax != 0)
                    else (1 if ymax == 0 else 100))

    # formatting
    ax.set_title(f'ADC {i_adc} - {title}' if title else f'ADC {i_adc}')
    ax.set_ylabel(ylabel)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # save numerator and denominator for later use
    neg_passed[i_adc, :] = neg_counts
    total_evts[i_adc, :] = total_events
    axes[-1].set_xlabel('channel #')
  plt.tight_layout()
  plt.show()
  # save as pdf
  output_pdf = f"{args.tmp_dir}/{output_name}"
  with PdfPages(output_pdf) as pdf:
        pdf.savefig()
        plt.close()
  return neg_passed, total_evts




def plot_neg_epcb_fraction(prev_neg_evts, neg_evts, max_vals, ths,
                           title=None, output_name='neg_epcb_fraction.pdf'):
  n_adcs = neg_evts.shape[1]
  axes = plt.subplots(n_adcs, 1, figsize=(10, 2*n_adcs), sharex=True)[1]

  # Initialize arrays to store numerator and denominator for each ADC
  neg_passed = np.zeros((n_adcs, 64))
  total_evts = np.zeros((n_adcs, 64))

  for i_adc in range(n_adcs):
    ax = axes[i_adc]

    # get total events for this epcb with max_values > ptps
    neg_events = np.zeros((64))
    total_events = np.zeros((64))
    for i_epcb in range(8):
        channel_indices = channels[i_epcb * 6: (i_epcb + 1) * 6]
        channel_mask = np.zeros(64, dtype=bool)
        channel_mask[channel_indices] = True
        over_ptps = np.any(max_vals[:, i_adc, :]*channel_mask > ths[np.newaxis, i_adc, np.newaxis], axis=-1)
        total_events[channel_indices] = np.sum(over_ptps, axis=0)
        neg_events[channel_indices] = (
            neg_evts[:, i_adc, channel_mask][over_ptps].sum(axis=0)
        )

    # Clopper-Pearson interval (binomial proportion confidence interval)
    neg_pct, err_low, err_up = clopper_pearson(neg_events, total_events)
    ylabel = '-ve baseline (% EPCB)'
    ymax = 0

    # define alpha 0.25 for cs!=0
    alphas = np.ones_like(cs[i_adc, :])
    bad_mask = cs[i_adc, :] != 0
    alphas[bad_mask] = 0.25

    # Plot each point individually to allow per-point alpha
    for idx in channels:
        # previous negative events
        if prev_neg_evts is not None:
            prev_centre, prev_lower, prev_upper = prev_neg_evts
            c = prev_centre[i_adc, idx]
            l = prev_lower[i_adc, idx]
            u = prev_upper[i_adc, idx]
            ax.step(
                [idx - 0.5, idx + 0.5], [c, c],
                color='red', alpha=alphas[idx]/2, where='post', linewidth=1
            )
            ax.fill_between(
                [idx - 0.5, idx + 0.5], [c - l, c - l], [c + u, c + u],
                color='red', alpha=alphas[idx]/4, step='post'
            )
        # current file
        color = 'b'

        # point + Clopper–Pearson error bars
        yerr_lower = err_low[idx]
        yerr_upper = err_up[idx]
        ax.errorbar(
            idx, neg_pct[idx],
            yerr=[[yerr_lower], [yerr_upper]],
            fmt='.', ecolor=color, markersize=5,
            capsize=4, linewidth=1, color=color,
            alpha=alphas[idx]
        )
        if neg_pct[idx] + yerr_upper < 100.0:
            if (ymax < neg_pct[idx] + yerr_upper):
                ymax = neg_pct[idx] + yerr_upper
        if prev_neg_evts is not None and (c + u < 100.0):
            if (ymax < c + u):
                ymax = c + u

    # get y-lim from data (excluding values with 0 clipped events)
    ax.set_ylim(0, ymax*1.1 if (ymax < 90 and ymax != 0)
                    else (1 if ymax == 0 else 100))

    # formatting
    ax.set_title(f'ADC {i_adc} - {title}' if title else f'ADC {i_adc}')
    ax.set_ylabel(ylabel)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    # save negative percentages and bounds
    neg_passed[i_adc, :] = neg_events
    total_evts[i_adc, :] = total_events
  axes[-1].set_xlabel('channel #')
  plt.tight_layout()
  plt.show()
  # save as pdf
  output_pdf = f"{args.tmp_dir}/{output_name}"
  with PdfPages(output_pdf) as pdf:
      pdf.savefig()
      plt.close()
  return neg_passed, total_evts




# ----------------------------- #
#    Helper Functions           #
# ----------------------------- #

def placeholder_pdf(output_dir, filename, message):
    """
    Create a placeholder PDF with an error message.
    
    Args:
        output_dir (str): Output directory
        filename (str): PDF filename
        message (str): Error message to display
    """
    import os
    output_pdf = os.path.join(output_dir, filename)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.text(0.5, 0.5, message, fontsize=12, ha='center', va='center')
    ax.axis('off')
    with PdfPages(output_pdf) as pdf:
        pdf.savefig(fig)
        plt.close()
    logger.warning(f"Placeholder PDF created: {output_pdf}")
