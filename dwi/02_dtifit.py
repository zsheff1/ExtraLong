#!/usr/bin/env python3
"""
flips the images from RAI orientation that qsiprep uses to RPI orientation that fsl uses
pads the dwi image and brain mask to get dimensions 128*128*128
fits the tensors
"""

import os
import glob
import re
import logging

DATA_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi'
LOG_DIR = '/project/bbl_gur_evolpsy/code/logs/dwi/dtifit'
JOBSCRIPT_DIR = '/project/bbl_gur_evolpsy/code/jobscripts/dwi/dtifit'
RPI_EXECUTABLE = '/project/bbl_projects/apps/melliott/scripts/force_RPI.sh'
PAD_EXECUTABLE = '/project/bbl_gur_evolpsy/code/dwi/pad.py'
SUB_PATTERN = re.compile(r'sub-\d+')
SES_PATTERN = re.compile(r'ses-\w+\d')
PAD_3D = '24 24 15 15 21 22'
PAD_4D = '24 24 15 15 21 22 0 0'

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(JOBSCRIPT_DIR, exist_ok=True)

logging.basicConfig(
    datefmt = '%Y-%m-%dT%H:%M:%S%z',
    filename = os.path.join(LOG_DIR, 'dtifit.log'),
    format = '%(asctime)s %(levelname)s %(message)s',
    level = logging.DEBUG
)

for path in glob.glob(os.path.join(DATA_DIR, 'sub-*/ses-*/dwi')):
    # find sub and ses info
    sub = SUB_PATTERN.search(path).group(0)
    ses = SES_PATTERN.search(path).group(0)
    logging.info(f'processing {sub}_{ses}')

    # define paths
    logging.debug('defining paths')
    dwi_qsi = os.path.join(path, f'{sub}_{ses}_space-ACPC_desc-preproc_dwi.nii.gz')
    dwi_rpi = os.path.join(path, f'{sub}_{ses}_space-ACPC_desc-preproc_dwi_rpi.nii.gz')
    dwi_pad = os.path.join(path, f'{sub}_{ses}_space-ACPC_desc-preproc_dwi_pad.nii.gz')
    mask_qsi = os.path.join(path, f'{sub}_{ses}_space-ACPC_desc-brain_mask.nii.gz')
    mask_rpi = os.path.join(path, f'{sub}_{ses}_space-ACPC_desc-brain_mask_rpi.nii.gz')
    mask_pad = os.path.join(path, f'{sub}_{ses}_space-ACPC_desc-brain_mask_pad.nii.gz')
    bvals = os.path.join(path, f'{sub}_{ses}_space-ACPC_desc-preproc_dwi.bval')
    bvecs = os.path.join(path, f'{sub}_{ses}_space-ACPC_desc-preproc_dwi.bvec')
    out = os.path.join(path, f'{sub}_{ses}')

    # skip if input data missing
    logging.debug('checking for the presence of input data')
    missing = [image for image in [dwi_qsi, mask_qsi, bvals, bvecs] if not os.path.exists(image)]
    if missing:
        logging.warning(f"skipping {sub}_{ses}, the following {'file' if len(missing) == 1 else 'files'} cannot be found: {' '.join(missing)}")
        continue

    # generate BIDS Filter and jobscript
    logging.debug('generating jobscript')
    cmd = f"""#!/bin/bash
#BSUB -o {LOG_DIR}/{sub}_{ses}.o
#BSUB -e {LOG_DIR}/{sub}_{ses}.e
#BSUB -J dtifit_{sub}_{ses}

module load afni_openmp/20.1
module load fsl/6.0.3

# RPI FLIP
{RPI_EXECUTABLE} {dwi_qsi} {dwi_rpi}
{RPI_EXECUTABLE} {mask_qsi} {mask_rpi}

# PADDING
{PAD_EXECUTABLE} {dwi_rpi} {dwi_pad} {PAD_4D}
{PAD_EXECUTABLE} {mask_rpi} {mask_pad} {PAD_3D}

# DTIFIT
dtifit --data={dwi_pad} --out={out} --mask={mask_pad} --bvecs={bvecs} --bvals={bvals}

"""

    jobscript_path = os.path.join(JOBSCRIPT_DIR, f'{sub}_{ses}.sh')
    logging.debug(f'writing jobscript to {jobscript_path}')
    with open(jobscript_path, 'w', opener=lambda path, flags: os.open(path, flags, 0o775)) as jobscript_file:
        jobscript_file.write(cmd)
    logging.debug(f'submitting jobscript to scheduler')
    os.system(f'bsub < {jobscript_path}')
