#!/usr/bin/env python3

import os
import glob
import re
import logging

DATA_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi'
LOG_DIR = '/project/bbl_gur_evolpsy/code/logs/dwi/dtitk_preprocessing'
JOBSCRIPT_DIR = '/project/bbl_gur_evolpsy/code/jobscripts/dwi/dtitk_preprocessing'
FACTOR = str(1000)
SUB_PATTERN = re.compile(r'sub-\d+')
SES_PATTERN = re.compile(r'ses-\w+\d')

os.makedirs(LOG_DIR, exist_ok = True)
os.makedirs(JOBSCRIPT_DIR, exist_ok = True)

logging.basicConfig(
    datefmt = '%Y-%m-%dT%H:%M:%S%z',
    filename = os.path.join(LOG_DIR, 'dtitk_preprocessing.log'),
    format = '%(asctime)s %(levelname)s %(message)s',
    level = logging.DEBUG
)

for image in glob.glob(os.path.join(DATA_DIR, 'sub-*/ses-*/dwi/sub-*_ses-*_FA.nii.gz')):
    # find sub and ses info
    sub = SUB_PATTERN.search(image).group(0)
    ses = SES_PATTERN.search(image).group(0)
    path = os.path.dirname(image)
    logging.info(f'processing {sub}_{ses}')

    logging.debug('generating jobscript')
    cmd = f'''#!/bin/bash
#BSUB -o {LOG_DIR}/{sub}_{ses}.o
#BSUB -e {LOG_DIR}/{sub}_{ses}.e
#BSUB -J dtitk_preprocessing_{sub}_{ses}

module load dtitk/2.3.1

TVFromEigenSystem -basename {path}/{sub}_{ses} -type FSL -out {path}/{sub}_{ses}.nii.gz
TVtool -in {path}/{sub}_{ses}.nii.gz -scale {FACTOR} -out {path}/{sub}_{ses}.nii.gz
TVtool -in {path}/{sub}_{ses}.nii.gz -spd -out {path}/{sub}_{ses}.nii.gz
TVAdjustVoxelspace -in {path}/{sub}_{ses}.nii.gz -origin 0 0 0
'''

    # write command to jobscript and execute
    jobscript_path = os.path.join(JOBSCRIPT_DIR, f'{sub}_{ses}.sh')
    logging.debug(f'writing jobscript to {jobscript_path}')
    with open(jobscript_path, 'w', opener=lambda path, flags: os.open(path, flags, 0o775)) as jobscript_file:
        jobscript_file.write(cmd)
    logging.debug('submitting jobscript to scheduler')
    os.system(f'bsub < {jobscript_path}')