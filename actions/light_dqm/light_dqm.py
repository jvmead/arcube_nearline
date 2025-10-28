#!/usr/bin/env python3

##########################################
##                                      ##
##            ~ Light DQM ~             ##
##                                      ##
##########################################
##
##  Written 09.07.2025
##  Updated 27.08.2025
##  Refactored 28.10.2025 - Migrated to use modular package structure
##
##    - James Mead <jmead@nikhef.nl>
##    - Sindhujha Kumaran <s.kumaran@uci.edu>
##
###########################################
'''
    # example usage:

python light_dqm.py
                       --input_path /global/cfs/cdirs/dune/www/data/2x2/nearline_run2/flowed_light/warm_commission/
                       --file_syntax mpd_run_dbg_rctl_
                       --channel_status_file light_dqm/channel_status.csv
                       --output_dir dqm_plots/
                       --tmp_dir tmp/
                       --units ADC16
                       --ptps16bit 150
                       --start_run 0
                       --nfiles 10
                       --ncomp 5
                       --powspec_nevts 200
                       --max_evts 500
                       --write_json_blobs False
                       --merge_grafana_plots False
                       --plot_all_clipped False
                       --plot_all_negatives False
'''
############################################

import os
import sys
import time
import glob
import argparse
import traceback
from ascii import header, footer

import h5py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from PyPDF2 import PdfMerger

# Import from refactored modules
from config import (
    SAMPLE_RATE, ADC14_MAX, ADC14_16_CONVERSION, ADC_V_RANGE, ADC_V_OFFSET,
    CHANNELS, N_ADCS, N_CHANNELS, N_EPCBS,
    FREQ_ROIS_MHZ, FREQ_WINDOW_MHZ,
    get_ptps, adc16_to_voltage, get_baseline_ranges
)
from utils import (
    clopper_pearson,
    load_channel_status,
    save_as_json, read_from_json,
    save_eff_as_json, read_eff_from_json,
    save_spectra_as_json
)
from data_processing import (
    get_waveform_info, get_sum_waveform, get_max_value_mask, get_noise_spectra
)
from plotting import (
    plot_flatline_mask, plot_baseline_mask,
    plot_sum_waveform, plot_noises, plot_baselines,
    plot_noise_spectra_epcb, plot_noise_spectra_channels,
    plot_clipped_fraction, plot_clipped_tpc_fraction,
    plot_clipped_epcb_fraction, plot_clipped_ch_fraction,
    plot_neg_tpc_fraction, plot_neg_epcb_fraction,
    placeholder_pdf
)
from quality_checks import check_flatline, check_baseline


def parse_args():
    """Parse command-line arguments for Light DQM."""
    parser = argparse.ArgumentParser(description="Process and plot DUNE light file data.")
    parser.add_argument('--input_path', type=str, default='.', help='Path to input file')
    parser.add_argument('--file_syntax', type=str, default='.', help='File name syntax')
    parser.add_argument('--channel_status_file', type=str, default='actions/light_dqm/channel_status_warmRun2.csv', help='Channel status file')
    parser.add_argument('--output_dir', type=str, default='dqm_plots/', help='Directory to save final output plots')
    parser.add_argument('--tmp_dir', type=str, default='tmp/', help='Directory to save temporary output plots')
    parser.add_argument('--units', type=str, default='ADC16', choices=['ADC16', 'ADC14', 'V'], help='Units for waveform')
    parser.add_argument('--ptps16bit', type=int, default=500, help='Peak-to-peak threshold for 16-bit ADC')
    parser.add_argument('--start_run', type=int, default=0, help='Starting file index for processing')
    parser.add_argument('--nfiles', type=int, default=1, help='Number of files to process')
    parser.add_argument('--ncomp', type=int, default=-1, help='Number of previous files to compare')
    parser.add_argument('--powspec_nevts', type=int, default=500, help='Number of events to process per file for noise spectra')
    parser.add_argument('--max_evts', type=int, default=500, help='Maximum number of events to process for the whole file')
    parser.add_argument('--write_json_blobs', type=bool, default=False, help='Write noise spectra blobs to json files')
    parser.add_argument('--merge_grafana_plots', type=bool, default=False, help='Merge baselines and flatlines grafana plots')
    parser.add_argument('--plot_all_clipped', type=bool, default=False, help='Plot all clipped waveform plots')
    parser.add_argument('--plot_all_negatives', type=bool, default=False, help='Plot all negative baseline plots')

    return parser.parse_args()


# ----------------------------- #
#             Main              #
# ----------------------------- #

def main():
    """
    Main entry point for DUNE light file processing and plotting.
    """
    # start timer
    start_time = time.time()

    # print header
    header()

    args = parse_args()
    if args.units not in ['ADC16', 'ADC14', 'V']:
        print(f"Invalid units: {args.units}. Must be 'ADC16', 'ADC14', or 'V'.")
        sys.exit(1)

    if args.powspec_nevts > args.max_evts:
        print("Number of events for the power spectrum can't be greater than the total events")
        # set powerspec_nevts to max_evts
        args.powspec_nevts = args.max_evts
        print(f"Setting powerspec_nevts to {args.max_evts} (beware of memory issues with large nevts)")

    # Load channel status
    cs = load_channel_status(args.channel_status_file)

    try:
        os.makedirs(args.output_dir, exist_ok=True)
        print(f"Output directory is ready: {args.output_dir}")
    except Exception as e:
        print(f"Error creating output directory {args.output_dir}: {e}")
        raise

    try:
        os.makedirs(args.tmp_dir, exist_ok=True)
        print(f"Temporary directory is ready: {args.tmp_dir}")
    except Exception as e:
        print(f"Error creating temporary directory {args.tmp_dir}: {e}")
        raise

    # search for any files in --input_path starting with args.file_syntax and ending with '.FLOW.hdf5'
    all_files = [f for f in os.listdir(args.input_path) if f.startswith(args.file_syntax) and f.endswith('.FLOW.hdf5')]
    all_files.sort()
    n_available_files = len(all_files)
    print(f"Found {n_available_files} files in {args.input_path} starting with {args.file_syntax} and ending with .FLOW.hdf5")
    if n_available_files == 0:
        print("No files found. Exiting.")
        sys.exit(1)
    if args.start_run >= n_available_files:
        print(f"Start file index {args.start_run} is out of range. There are only {n_available_files} files available. Exiting.")
        sys.exit(1)
    if args.start_run + args.nfiles > n_available_files:
        args.nfiles = n_available_files - args.start_run
        print(f"Adjusting number of files to process to {args.nfiles} to avoid going out of range.")

    file_time = start_time
    proc_files = 0

    for i_file in range(args.start_run, args.start_run + args.nfiles, 1):

        # Construct the filename based on the input path and file index
        filename = f'{args.input_path}{all_files[i_file]}'
        # just the file name, no path and cutting off .FLOW.hdf5
        short_filename = all_files[i_file][:-10]

        # Skip if file does not exist
        if not os.path.exists(filename):
            print(f"File not found, skipping: {filename}")
            continue
        proc_files += 1
        print(f"Processing file: {filename} with units: {args.units}")

        # Get peak-to-peak thresholds for the specified units
        ptps = get_ptps(args.ptps16bit, args.units)

        try:
            file = h5py.File(filename, 'r')
            print(f"File opened successfully: {filename}")
        except Exception as e:
            print(f"Error opening {filename}: {e}")
            continue

        # Get start and end timestamps in ms
        start_timestamp = file["light/events/data"][0]['utime_ms'][0]
        end_timestamp = file["light/events/data"][-1]['utime_ms'][0]

        # Convert to UTC datetime string
        start_utc = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_timestamp / 1000))
        end_utc = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(end_timestamp / 1000))

        # Convert to US Central Time (UTC-6)
        start_central = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_timestamp / 1000 - 6 * 3600))
        end_central = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(end_timestamp / 1000 - 6 * 3600))
        print(f"File start time (US Central, UTC-6): {start_central}")
        print(f"File end time (US Central, UTC-6): {end_central}")

        # files for comparison
        if args.ncomp == -1 or args.ncomp > i_file:
            ncomps = np.arange(0, i_file, 1)
        elif args.ncomp == 0:
            ncomps = np.array([])
        else:
            ncomps = np.arange(i_file-args.ncomp, i_file, 1)

        # get n events to process
        nevents_total = file["light/wvfm/data"]['samples'].shape[0]
        evts_to_process = args.max_evts
        if args.max_evts > nevents_total:
            print(f"Total number of events to process {args.max_evts} is less than the number of events in the file {nevents_total}, changing to total events")
            evts_to_process = nevents_total

        # select evenly spaced indices up to max_evts
        sel_idx = np.linspace(0, nevents_total - 1, evts_to_process, dtype=int)
        sel_idx = np.unique(sel_idx)  # ensure unique indices

        # define datasets for beam trigger type
        beam_mask = sel_idx[file["light/events/data"]['trig_type'][sel_idx] == 1]
        beam_wvfms, beam_noises, beam_baselines, beam_max_values, beam_clipped, beam_negs = get_waveform_info(
            file["light/wvfm/data"]['samples'], args.units, mask=beam_mask, ths=ptps)
        nbeam_evts = beam_wvfms.shape[0]

        # define datasets for self-trigger type
        strig_mask = sel_idx[file["light/events/data"]['trig_type'][sel_idx] == 0]
        strig_wvfms, strig_noises, strig_baselines, strig_max_values, strig_clipped, strig_negs = get_waveform_info(
            file["light/wvfm/data"]['samples'], args.units, mask=strig_mask, ths=ptps)
        nstrig_evts = strig_wvfms.shape[0]

        # define datasets for all events
        wvfms, noises, baselines, max_values, clipped, negs = get_waveform_info(
            file["light/wvfm/data"]['samples'], args.units, mask=sel_idx, ths=ptps)
        nevts = wvfms.shape[0]

        ###############################################################
        # WORK IN PROGRESS TO TRACK RATIO OF BEAM TO SELF-TRIG EVENTS #
        ###############################################################

        print(f"Waveform info extracted for file: {filename}")
        print("    Total number of events:", wvfms.shape[0])
        print("    Number of beam events:", beam_wvfms.shape[0],
              (f"{100*beam_wvfms.shape[0]/wvfms.shape[0]:.1f}%" if wvfms.shape[0]>0 else "N/A"))
        print("    Number of self-trigger events:", strig_wvfms.shape[0],
              (f"{100*strig_wvfms.shape[0]/wvfms.shape[0]:.1f}%" if wvfms.shape[0]>0 else "N/A"))

        ### DQM PLOTS ###

        # identify event with largest total integral
        integrals = np.sum(wvfms, axis=(1,2,3))
        max_integral_evt = np.argmax(integrals)

        # number of samples over noise threshold
        ptps_broadcasted = get_ptps(args.ptps16bit, 'ADC16')  # Always use ADC16 for this check
        samples_over_th = wvfms > ptps_broadcasted[np.newaxis, :, np.newaxis, np.newaxis]
        nsamples_over_th = np.sum(samples_over_th, axis=(1,2,3))
        max_nsamples_evt = np.argmax(nsamples_over_th)

        # get event number containing the wvfm with the largest diff between consecutive samples
        diffs = np.abs(np.diff(wvfms, axis=-1))
        max_diffs = np.max(diffs, axis=(1,2,3))
        max_diff_evt = np.argmax(max_diffs)

        ####################################################################
        # WIP: find a way to make this a tag for sparking / discharge events
        #evts = np.array([max_integral_evt])
        #evts = np.array([max_nsamples_evt])
        evts = np.array([max_diff_evt])
        ####################################################################

        # sum waveform baselined
        try:
            for evt in evts:
                plot_sum_waveform(wvfms - baselines[:, :, :, np.newaxis],
                          args.units, i_evt=evt, output_name=f'{args.tmp_dir}/plot1_sumwvfm.pdf')
            print(f"Sum waveform plotted for file: {filename}")
        except Exception as e:
            placeholder_pdf(args.tmp_dir, 'plot1_sumwvfm.pdf',
                            "Failed to plot summed waveforms: plot1_sumwvfm.pdf")
            traceback.print_exc()

        # noise power spectra and rois
        if args.powspec_nevts > 0:
            try:
                # get mask
                max_mask = get_max_value_mask(
                    max_values[:args.powspec_nevts], ptps, cs=cs
                )
                wvfms_v = adc16_to_voltage(wvfms[:args.powspec_nevts])
                process_powsp_evts = len(wvfms_v)

                freq_bins, noise_spectra, noise_spectrum, upper, lower = get_noise_spectra(
                    wvfms_v) #, max_mask)
                rois_mhz = FREQ_ROIS_MHZ
                # convert to index from frequency bins
                rois_bins = np.array([np.argmin(np.abs(freq_bins*1e-6 - roi)) for roi in rois_mhz])

                # loop over rois, and save spectrum bin to json for tracking rois over time
                if args.write_json_blobs:
                    for i_roi in range(len(rois_bins)):
                        roi_bin = rois_bins[i_roi]
                        spur = noise_spectrum[:, :, roi_bin]
                        # convert to string and replace '.' with '_' for naming convention
                        roi_mhz = str(rois_mhz[i_roi]).replace('.', '_')
                        # save to json
                        save_spectra_as_json(
                            i_file, spur, args.output_dir,
                            f'noise_spectra_roi_{roi_mhz}mhz.json'
                        )
                # free memory
                del wvfms_v

                # plot full spectrum
                plot_noise_spectra_epcb(
                    freq_bins, noise_spectrum, None, None,
                    skip_bad_channels=True, nevts=process_powsp_evts,
                    output_name=f'{args.tmp_dir}/plot5_powspec.pdf',
                )
                print(f"Noise spectra calculated for file: {filename}")

            except Exception as e:
                placeholder_pdf(args.tmp_dir, 'plot5_powspec.pdf',
                                "Failed to plot noise spectra: plot5_powspec.pdf")
                traceback.print_exc()

        # reading and writing noise widths
        try:
            # read noises
            prev_noises = read_from_json(
                ncomps, args.output_dir, 'noises.json'
            ) if i_file - args.start_run > 0 else None
            # Plot noises
            noise_c, noise_l, noise_u = plot_noises(prev_noises,
                strig_noises, i_evt=np.arange(0, strig_baselines.shape[0], 1),
                mask_inactive=False, output_name=f'{args.tmp_dir}/plot4_noises.pdf'
            )
            # write noises
            if args.write_json_blobs:
                save_as_json(
                    i_file, noise_c, noise_l, noise_u,
                    args.output_dir, 'noises.json'
                )
            print(f"Noises plotted for file: {filename}")

        except Exception as e:
            placeholder_pdf(args.tmp_dir, 'plot4_noises.pdf',
                            "Failed to plot noises: plot4_noises.pdf")
            traceback.print_exc()

        # reading and writing baselines
        try:
            # read baselines
            prev_baselines = read_from_json(
                ncomps, args.output_dir, 'baselines.json'
            ) if i_file - args.start_run > 0 else None
            # Plot baselines
            bline_c, bline_l, bline_u = plot_baselines(prev_baselines,
                strig_baselines, i_evt=np.arange(0, strig_baselines.shape[0], 1),
                mask_inactive=False, output_name=f'{args.tmp_dir}/plot2_baselines.pdf'
            )
            # write baselines
            if args.write_json_blobs: save_as_json(i_file, bline_c, bline_l, bline_u,
                         args.output_dir, 'baselines.json')
            print(f"Baselines plotted for file: {filename}")

        except Exception as e:
            placeholder_pdf(args.tmp_dir, 'plot2_baselines.pdf',
                            "Failed to plot baselines: plot2_baselines.pdf")
            traceback.print_exc()

        # for beam events, ADC clipping fraction for waveforms
        if nbeam_evts:
            try:
                # read clipped fraction for events with light on the channels' EPCB
                prev_beam_clipped_inputs = read_eff_from_json(
                    ncomps, args.output_dir, 'clipped_epcb_beam.json'
                ) if i_file - args.start_run > 0 else None
                # get error bars
                prev_beam_clipped = clopper_pearson(
                    prev_beam_clipped_inputs[0], prev_beam_clipped_inputs[1]
                ) if prev_beam_clipped_inputs is not None else None
                # Plot clipped fraction for events with light on the channels' EPCB
                clip_pass, clip_tot = plot_clipped_epcb_fraction(
                    prev_beam_clipped, beam_clipped, beam_max_values, ptps,
                    "Beam trigger (% of events with clipped waveforms, normalized per ECPB)",
                    output_name=f'{args.tmp_dir}/plot6_clipped_beam_epcb.pdf'
                )
                # write clipped fraction for events with light on the channels' EPCB
                if args.write_json_blobs: save_eff_as_json(i_file, clip_pass, clip_tot,
                                args.output_dir, 'clipped_epcb_beam.json')
                print(f"Clipped EPCB fraction plotted for file: {filename}")

                if args.plot_all_clipped:
                    # read beam trigger channel clipped fraction
                    prev_beam_clipped_inputs = read_eff_from_json(
                        ncomps, args.output_dir, 'clipped_ch_beam.json'
                    ) if i_file - args.start_run > 0 else None
                    # get error bars
                    prev_beam_clipped = clopper_pearson(
                        prev_beam_clipped_inputs[0], prev_beam_clipped_inputs[1]
                    ) if prev_beam_clipped_inputs is not None else None
                    # Plot clipped fraction for channels
                    clip_pass, clip_tot = plot_clipped_ch_fraction(
                        prev_beam_clipped, beam_clipped, beam_max_values, ptps,
                        "Beam trigger (% of events with clipped waveforms, normalized per channel)",
                        output_name=f'{args.tmp_dir}/plot6_clipped_beam_ch.pdf'
                    )
                    # write beam trigger channel clipped fraction
                    if args.write_json_blobs: save_eff_as_json(i_file, clip_pass, clip_tot,
                                    args.output_dir, 'clipped_ch_beam.json')
                    print(f"Clipped channel fraction plotted for file: {filename}")

            except Exception as e:
                placeholder_pdf(args.tmp_dir, 'plot6_clipped_beam_epcb.pdf',
                                "Failed to plot clipped fraction for beam events: plot6_clipped_beam_epcb.pdf"
                )
                if args.plot_all_clipped:
                    placeholder_pdf(args.tmp_dir, 'plot6_clipped_beam_ch.pdf',
                                    "Failed to plot clipped fraction for beam events: plot6_clipped_beam_ch.pdf"
                    )
                traceback.print_exc()

        # for self-trigger events, ADC clipping fraction for waveforms
        if nstrig_evts:
            try:
               # read clipped fraction for events with light on the channels' EPCB
                prev_strig_clipped_inputs = read_eff_from_json(
                    ncomps, args.output_dir, 'clipped_epcb_self.json'
                ) if i_file - args.start_run > 0 else None
                # get error bars
                prev_strig_clipped = clopper_pearson(
                    prev_strig_clipped_inputs[0], prev_strig_clipped_inputs[1]
                ) if prev_strig_clipped_inputs is not None else None
                # Plot clipped fraction for events with light on the channels' EPCB
                clip_pass, clip_tot = plot_clipped_epcb_fraction(
                    prev_strig_clipped, strig_clipped, strig_max_values, ptps,
                    "Self-trigger (% of events with clipped waveforms, normalized per EPCB)",
                    output_name=f'{args.tmp_dir}/plot8_clipped_self_epcb.pdf'
                )
                # write clipped fraction for events with light on the channels' EPCB
                if args.write_json_blobs: save_eff_as_json(i_file, clip_pass, clip_tot,
                                args.output_dir, 'clipped_epcb_self.json')
                print(f"Clipped EPCB fraction plotted for file: {filename}")

                if args.plot_all_clipped:
                    # read channel clipped fraction
                    prev_strig_clipped_inputs = read_eff_from_json(
                        ncomps, args.output_dir, 'clipped_ch_self.json'
                    ) if i_file - args.start_run > 0 else None
                    # get error bars
                    prev_strig_clipped = clopper_pearson(
                        prev_strig_clipped_inputs[0], prev_strig_clipped_inputs[1]
                    ) if prev_strig_clipped_inputs is not None else None
                    # Plot clipped fraction for channels
                    clip_pass, clip_tot = plot_clipped_ch_fraction(
                        prev_strig_clipped, strig_clipped, strig_max_values, ptps,
                        "Self-trigger Trigger  (% of events with clipped waveforms, normalized per channel)",
                        output_name=f'{args.tmp_dir}/plot8_clipped_ch_self.pdf'
                    )
                    # write channel clipped fraction
                    if args.write_json_blobs: save_eff_as_json(i_file, clip_pass, clip_tot,
                                    args.output_dir, 'clipped_ch_self.json')
                    print(f"Clipped channel fraction plotted for file: {filename}")

            except Exception as e:
                placeholder_pdf(args.tmp_dir, 'plot8_clipped_self_epcb.pdf',
                                "Failed to plot clipped fraction for self-trigger events: plot8_clipped_self_epcb.pdf")
                if args.plot_all_clipped:
                    placeholder_pdf(args.tmp_dir, 'plot8_clipped_self_ch.pdf',
                                    "Failed to plot clipped fraction for self-trigger events: plot8_clipped_self_ch.pdf")
                traceback.print_exc()

        # for beam events, negative spike fraction for waveforms
        if nbeam_evts:
            try:
                # read negative spike fraction for events with light on the channels' TPC
                prev_beam_negs_inputs = read_eff_from_json(
                    ncomps, args.output_dir, 'negatives_tpc_beam.json'
                ) if i_file - args.start_run > 0 else None
                # get error bars
                prev_beam_negs = clopper_pearson(
                    prev_beam_negs_inputs[0], prev_beam_negs_inputs[1]
                ) if prev_beam_negs_inputs is not None else None
                # plot negative spike fraction for events with light on the channels' TPC
                negs_pass, negs_tot = plot_neg_tpc_fraction(
                    prev_beam_negs, beam_negs, beam_max_values, ptps,
                    "Beam trigger (% of events with -ve spikes, normalized per TPC)",
                    f'{args.tmp_dir}/plot7_negatives_beam_tpc.pdf'
                )
                # write negative spike fraction for events with light on the channels' TPC
                if args.write_json_blobs: save_eff_as_json(i_file, negs_pass, negs_tot,
                                args.output_dir, 'negatives_tpc_beam.json')
                print(f"Negative spike TPC fraction plotted for file: {filename}")

                if args.plot_all_negatives:
                    # read negative spike fraction for events with light on the channels' EPCB
                    prev_beam_negs_inputs = read_eff_from_json(
                        ncomps, args.output_dir, 'negatives_epcb_beam.json'
                    ) if i_file - args.start_run > 0 else None
                    # get error bars
                    prev_beam_negs = clopper_pearson(
                        prev_beam_negs_inputs[0], prev_beam_negs_inputs[1]
                    ) if prev_beam_negs_inputs is not None else None
                    # plot negative spike fraction for events with light on the channels' EPCB
                    negs_pass, negs_tot = plot_neg_epcb_fraction(
                        prev_beam_negs, beam_negs, beam_max_values, ptps,
                        "Beam trigger (% of events with -ve spikes, normalized per EPCB)",
                        f'{args.tmp_dir}/plot7_negatives_beam_epcb.pdf'
                    )
                    # write negative spike fraction for events with light on the channels' EPCB
                    if args.write_json_blobs: save_eff_as_json(i_file, negs_pass, negs_tot,
                                    args.output_dir, 'negatives_epcb_beam.json')
                    print(f"Negative spike EPCB fraction plotted for file: {filename}")

            except Exception as e:
                placeholder_pdf(args.tmp_dir, 'plot7_negatives_beam_tpc.pdf',
                                "Failed to plot -ve spike fraction for beam events: plot7_negatives_beam_tpc.pdf"
                )
                if args.plot_all_negatives:
                    placeholder_pdf(args.tmp_dir, 'plot7_negatives_beam_epcb.pdf',
                                    "Failed to plot -ve spike fraction for beam events: plot7_negatives_beam_epcb.pdf"
                    )
                traceback.print_exc()

        if nstrig_evts:
            try:
                # self-trigger
                prev_strig_negs_inputs = read_eff_from_json(
                    ncomps, args.output_dir, 'negatives_tpc_self.json'
                ) if i_file - args.start_run > 0 else None
                # get error bars
                prev_strig_negs = clopper_pearson(
                    prev_strig_negs_inputs[0], prev_strig_negs_inputs[1]
                ) if prev_strig_negs_inputs is not None else None
                # plot negative spike fraction for events with light on the channels' TPC
                negs_pass, negs_tot = plot_neg_tpc_fraction(
                    prev_strig_negs, strig_negs, strig_max_values, ptps,
                    "Self-trigger (% of events with -ve spikes, normalized per TPC)",
                    f'{args.tmp_dir}/plot9_negatives_self_tpc.pdf'
                )
                # write negative spike fraction for events with light on the channels' TPC
                if args.write_json_blobs: save_eff_as_json(i_file, negs_pass, negs_tot,
                                args.output_dir, 'negatives_tpc_self.json')
                print(f"Negative spike TPC fraction plotted for file: {filename}")

                if args.plot_all_negatives:
                    # read negative spike fraction for events with light on the channels' EPCB
                    prev_strig_negs_inputs = read_eff_from_json(
                        ncomps, args.output_dir, 'negatives_epcb_self.json'
                    ) if i_file - args.start_run > 0 else None
                    # get error bars
                    prev_strig_negs = clopper_pearson(
                        prev_strig_negs_inputs[0], prev_strig_negs_inputs[1]
                    ) if prev_strig_negs_inputs is not None else None
                    # plot negative spike fraction for events with light on the channels' EPCB
                    negs_pass, negs_tot = plot_neg_epcb_fraction(
                        prev_strig_negs, strig_negs, strig_max_values, ptps,
                        "Self-trigger  (% of events with -ve spikes, normalized per EPCB)",
                        f'{args.tmp_dir}/plot9_negatives_self_epcb.pdf'
                    )
                    # write negative spike fraction for events with light on the channels' EPCB
                    if args.write_json_blobs: save_eff_as_json(i_file, negs_pass, negs_tot,
                                    args.output_dir, 'negatives_epcb_self.json')
                    print(f"Negative spike EPCB fraction plotted for file: {filename}")

            except Exception as e:
                placeholder_pdf(args.tmp_dir, 'plot9_negatives_self_tpc.pdf',
                                "Failed to plot -ve spike fraction for self-trigger events: plot9_negatives_self_tpc.pdf"
                )
                if args.plot_all_negatives:
                    placeholder_pdf(args.tmp_dir, 'plot9_negatives_self_epcb.pdf',
                                    "Failed to plot -ve spike fraction for self-trigger events: plot9_negatives_self_epcb.pdf"
                    )
                traceback.print_exc()

        ### GRAFANA PLOTS ###

        # flatlined waveforms
        try:
            # check for flatlining channels
            flatlined = check_flatline(
                max_values, threshold=0.1
            )
            # plotting flatlined channels for grafana
            plot_flatline_mask(
                flatlined, cs, output_name=f'{args.output_dir}/{short_filename}_light_dqm_flatline.png',
                times = (start_central, end_central)
            )
            # plotting flatlined channels
            plot_flatline_mask(
                flatlined, cs, output_name=f'{args.tmp_dir}/plot0_flatline.pdf',
                times = (start_central, end_central), grafana=False
            )
        except Exception as e:
            placeholder_pdf(args.output_dir, f'{short_filename}_light_dqm_flatline.png',
                            "Failed to plot grafana flatline: ..light_dqm_flatline.png")
            placeholder_pdf(args.tmp_dir, 'plot0_flatline.pdf', "Failed to plot flatlined channels: plot0_flatline.pdf")
            traceback.print_exc()

        # baseline fluctuations
        try:
            # checking for baseline fluctuations
            baselined, status = check_baseline(
                prev_baselines, (bline_c, bline_l, bline_u),
                units=args.units, threshold=500
            )

            # plotting baseline fluctuations for grafana
            plot_baseline_mask(
                baselined, cs, output_name=f'{args.output_dir}/{short_filename}_light_dqm_baseline.png',
                times = (start_central, end_central)
            )
            # plotting baseline fluctuations
            plot_baseline_mask(
                baselined, cs, output_name=f'{args.tmp_dir}/plot0_baseline.pdf',
                times = (start_central, end_central), grafana=False
            )

        except Exception as e:
            placeholder_pdf(args.output_dir, f'{short_filename}_light_dqm_baseline.png',
                            "Failed to plot grafana baseline fluctuations: ..light_dqm_baseline.png")
            placeholder_pdf(args.tmp_dir, 'plot0_baseline.pdf',
                            "Failed to plot baseline fluctuations: plot0_baseline.pdf")
            traceback.print_exc()

        # search for files in the output directory and merge pdfs
        merger = PdfMerger()

        # Create a PDF with the arguments, file index, and unix timestamp
        input_path_lines = []
        max_line_length = 40
        input_path = args.input_path
        while len(input_path) > max_line_length:
            split_idx = input_path.rfind('/', 0, max_line_length)
            if split_idx == -1:
                split_idx = max_line_length
            input_path_lines.append(input_path[:split_idx])
            input_path = input_path[split_idx:]
        input_path_lines.append(input_path)

        # split filename at '/' closest to the centre
        filename_lines = []
        max_line_length = 60
        filename_str = filename
        while len(filename_str) > max_line_length:
            split_idx = filename_str.rfind('/', 0, max_line_length)
            if split_idx == -1:
                split_idx = max_line_length
            filename_lines.append(filename_str[:split_idx])
            filename_str = filename_str[split_idx:]
        filename_lines.append(filename_str)

        # Build args_list dynamically, avoiding None entries
        args_list = [f"File index: {i_file}"]

        # Add formatted filename lines
        args_list.extend([line for line in filename_lines if line])

        args_list.append("")
        args_list.append(f"Data start timestamp (CT): {start_central}")
        args_list.append(f"Data end timestamp   (CT): {end_central}")
        args_list.append(f"DQM runtime          (CT): {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() - 21600))}")
        args_list.append("")

        # Add all relevant arguments
        for arg_name in [
            "nfiles", "start_run", "ncomp", "output_dir",
            "units", "ptps16bit", "max_evts", "powspec_nevts"
        ]:
            arg_value = getattr(args, arg_name)
            args_list.append(f"--{arg_name} {arg_value}")

        # remove None
        args_list = [line for line in args_list if line is not None]
        args_pdf = os.path.join(args.tmp_dir, f"args_list_{i_file}.pdf")

        with PdfPages(args_pdf) as pdf:
            fig, ax = plt.subplots(figsize=(8.5, 6))
            ax.axis('off')
            text = "\n".join(args_list)
            ax.text(0.01, 0.99, text, va='top', ha='left', fontsize=12, family='monospace')
            pdf.savefig(fig)
            plt.close(fig)

        # Insert the args PDF at the top of the merged file
        merger.append(args_pdf)
        os.remove(args_pdf)

        # Append all DQM plot PDFs to the merger
        plot_files = sorted(glob.glob(os.path.join(args.tmp_dir, "*plot*.pdf")))
        for plot_path in plot_files:
            if os.path.exists(plot_path):
                merger.append(plot_path)
                os.remove(plot_path)

        merged_pdf_path = os.path.join(args.output_dir, f"{short_filename}_light_dqm_main.pdf")
        merger.write(merged_pdf_path)
        merger.close()

        # timing for file processing
        print(f"Processing completed for file: {filename}")
        print(f"Time taken for file {i_file}: {time.time() - file_time:.2f} seconds")
        file_time = time.time()

    if not proc_files:
        raise ValueError("None of the files were found")

    footer()
    print(f"Time taken all files: {time.time() - start_time:.2f} seconds")


if __name__ == "__main__":
    main()
