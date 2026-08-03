#!/usr/bin/env python3

import os
import glob
import re
import logging

DATA_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi'
LOG_DIR = '/project/bbl_gur_evolpsy/code/logs/dwi/dtitk_registration'
JOBSCRIPT_DIR = '/project/bbl_gur_evolpsy/code/jobscripts/dwi/dtitk_registration'
SUB_PATTERN = re.compile(r'sub-\d+')
SES_PATTERN = re.compile(r'ses-\w+\d')

os.makedirs(LOG_DIR, exist_ok = True)
os.makedirs(JOBSCRIPT_DIR, exist_ok = True)

logging.basicConfig(
    datefmt = '%Y-%m-%dT%H:%M:%S%z',
    filename = os.path.join(LOG_DIR, 'dtitk_registration.log'),
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
#BSUB -J dtitk_registration_{sub}_{ses}
  
module load dtitk/2.3.1
module load fsl/6.0.3

dti_rigid_reg {DATA_DIR}/template/template.nii.gz {path}/{sub}_{ses}.nii.gz EDS 4 4 4 0.01
dti_affine_reg {DATA_DIR}/template/template.nii.gz {path}/{sub}_{ses}.nii.gz EDS 4 4 4 0.01 1
dti_diffeomorphic_reg {DATA_DIR}/template/template.nii.gz {path}/{sub}_{ses}_aff.nii.gz {DATA_DIR}/template/template_mask.nii.gz 1 6 0.002
dti_warp_to_template {path}/{sub}_{ses}.nii.gz {DATA_DIR}/template/template.nii.gz 2 2 2
TVtool -in {path}/{sub}_{ses}_diffeo.nii.gz -fa
TVtool -in {path}/{sub}_{ses}_diffeo.nii.gz -eigs
fslmaths {path}/{sub}_{ses}_diffeo_lambda2.nii.gz -add {path}/{sub}_{ses}_diffeo_lambda3.nii.gz -div 2 {path}/{sub}_{ses}_diffeo_rd.nii.gz
fslmaths {path}/{sub}_{ses}_diffeo_lambda1.nii.gz -add {path}/{sub}_{ses}_diffeo_lambda2.nii.gz -add {path}/{sub}_{ses}_diffeo_lambda3.nii.gz -div 3 {path}/{sub}_{ses}_diffeo_md.nii.gz
cp {path}/{sub}_{ses}_diffeo_lambda1.nii.gz {path}/{sub}_{ses}_diffeo_ad.nii.gz
'''

    # write command to jobscript and execute
    jobscript_path = os.path.join(JOBSCRIPT_DIR, f'{sub}_{ses}.sh')
    logging.debug(f'writing jobscript to {jobscript_path}')
    with open(jobscript_path, 'w', opener=lambda path, flags: os.open(path, flags, 0o775)) as jobscript_file:
        jobscript_file.write(cmd)
    logging.debug('submitting jobscript to scheduler')
    os.system(f'bsub < {jobscript_path}')