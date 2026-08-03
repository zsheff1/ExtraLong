#!/usr/bin/env python3

import os
import glob
import re
import logging

DTITK_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi'
LOG_BASE = '/project/bbl_gur_evolpsy/code/logs/dwi/template_build/template_build'
TEMPLATE_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi/template'
SELECT_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi/template/select'
BUILD_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi/template/build'
JOBSCRIPT_PATH = '/project/bbl_gur_evolpsy/code/jobscripts/dwi/template_build/template_build.sh'
INITIAL_TEMPLATE = '/project/bbl_gur_evolpsy/code/dwi/go1_n14_template.nii.gz'
PAD_EXECUTABLE = '/project/bbl_gur_evolpsy/code/dwi/pad.py'
PAD = '24 24 15 15 21 22 0 0 0 0'
SUB_SES_PATTERN = re.compile(r'(sub-\d{6})_(ses-\w{3,4}1)')

os.makedirs(os.path.dirname(LOG_BASE), exist_ok = True)
os.makedirs(os.path.dirname(JOBSCRIPT_PATH), exist_ok = True)

logging.basicConfig(
    datefmt = '%Y-%m-%dT%H:%M:%S%z',
    filename = f'{LOG_BASE}.log',
    format = '%(asctime)s %(levelname)s %(message)s',
    level = logging.DEBUG
)

logging.info('finding those sessions identified as most representative for each bin by FSL\'s TBSS')
selected_dtitk = []
for best in glob.glob(os.path.join(SELECT_DIR, '*/FA/best.msf')):
    with open(best) as file:
        content = file.read().strip()
        sub, ses = SUB_SES_PATTERN.search(content).groups()
        dtitk_image = os.path.join(DTITK_DIR, sub, ses, 'dwi', f'{sub}_{ses}.nii.gz')
        selected_dtitk.append(dtitk_image)

logging.info('writing sub.txt')
selected_build = sorted(
    glob.glob(os.path.join(BUILD_DIR, 'sub-*_ses-*.nii.gz')) +
    [os.path.join(BUILD_DIR, os.path.basename(image)) for image in selected_dtitk]
)

with open(os.path.join(BUILD_DIR, 'subs.txt'), 'w') as file:
    file.writelines(f'{image}\n' for image in selected_build)

logging.info('generating jobscript')
cmd = f'''#!/bin/bash
#BSUB -o {LOG_BASE}.o
#BSUB -e {LOG_BASE}.e
#BSUB -J template_build

module load dtitk/2.3.1
module load fsl/6.0.3

cd {BUILD_DIR}

# COPY SELECTED IMAGES TO BUILD_DIR/
'''

for image in selected_dtitk:
    cmd += f'cp {image} {BUILD_DIR}\n'

cmd += f'''

# MAKE THE TEMPLATE
cp {INITIAL_TEMPLATE} {BUILD_DIR}/initial_template.nii.gz
TVResample -in {BUILD_DIR}/initial_template.nii.gz -align center -size 80 98 85 -vsize 2 2 2
{PAD_EXECUTABLE} {BUILD_DIR}/initial_template.nii.gz {BUILD_DIR}/initial_template.nii.gz {PAD}
TVAdjustVoxelspace -in {BUILD_DIR}/initial_template.nii.gz -origin 0 0 0
dti_template_bootstrap initial_template.nii.gz subs.txt
mv mean_initial.nii.gz template.nii.gz

# MAKE THE TEMPLATE MASK
bet template.nii.gz template_brain.nii.gz -f 0.3 -m
fslmaths template_brain_mask.nii.gz -Tmax -bin template_mask.nii.gz -odt char

mv {BUILD_DIR}/template.nii.gz {TEMPLATE_DIR}
mv {BUILD_DIR}/template_mask.nii.gz {TEMPLATE_DIR}
'''

logging.info(f'writing jobscript to {JOBSCRIPT_PATH}')
with open(JOBSCRIPT_PATH, 'w', opener=lambda path, flags: os.open(path, flags, 0o775)) as jobscript_file:
    jobscript_file.write(cmd)
logging.info('submitting jobscript')
os.system(f'bsub < {JOBSCRIPT_PATH}')