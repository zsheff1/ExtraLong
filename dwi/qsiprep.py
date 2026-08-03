#!/usr/bin/env python3
"""
artifact correction for diffusion weighted images
"""

import os
import glob

DATA_DIR = '/project/bbl_gur_evolpsy'
OUTPUT_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi'
LOG_DIR = '/project/bbl_gur_evolpsy/code/logs/dwi/qsiprep'
JOBSCRIPT_DIR = '/project/bbl_gur_evolpsy/code/jobscripts/dwi/qsiprep'
FS_LICENSE_DIR = '/project/bbl_gur_evolpsy/code/anat/freesurfer_license'
EXECUTABLE = '/project/bbl_gur_evolpsy/code/dwi/qsiprep-1.0.1.sif'
OUTPUT_RESOLUTION = str(2)

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(JOBSCRIPT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

for sub in os.listdir(DATA_DIR):
    if not glob.glob(os.path.join(DATA_DIR, sub, 'ses-*/dwi')):
        continue

    cmd = f'''#!/bin/bash
#BSUB -o {LOG_DIR}/{sub}.o
#BSUB -e {LOG_DIR}/{sub}.e
#BSUB -J qsiprep

module load apptainer/1.1.9

export APPTAINER_TMPDIR=/scratch
export APPTAINERENV_SURFER_FRONTDOOR=1

mkdir -p /scratch/$USER/$LSB_JOBID

apptainer run --cleanenv \\
-B {DATA_DIR}:/input:ro \\
-B {OUTPUT_DIR}:/output \\
-B /scratch:/scratch \\
-B {FS_LICENSE_DIR}:/fs_license_dir \\
{EXECUTABLE} \\
/input /output participant \\
--participant-label {sub} \\
--output-resolution {OUTPUT_RESOLUTION} \\
--work-dir /scratch/$USER/$LSB_JOBID \\
--dwi-only \\
--stop-on-first-crash \\
--fs-license-file /fs_license_dir/license.txt \\
--skip-bids-validation \\
--nthreads 6 \\
--omp-nthreads 4'''

    # write command to jobscript and execute
    jobscript_path = os.path.join(JOBSCRIPT_DIR, f'{sub}.sh')
    with open(jobscript_path, 'w', opener=lambda path, flags: os.open(path, flags, 0o775)) as jobscript_file:
        jobscript_file.write(cmd)
    os.system(f'bsub < {jobscript_path}')