#!/usr/bin/env python3

import re
import os
import glob

DWI_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi'
STATS_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi/stats'
ROI_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi/atlas/roi'
OUTPUT_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi/stats/roi'
LOG_DIR = '/project/bbl_gur_evolpsy/code/logs/dwi/roi'
JOBSCRIPT_DIR = '/project/bbl_gur_evolpsy/code/jobscripts/dwi/roi'
METRICS = ['ad', 'fa', 'md', 'rd']

SUB_SES_PATTERN = re.compile(r'sub-\d+_ses-\w+\d')

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(JOBSCRIPT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

for diffeo_image in glob.glob(os.path.join(DWI_DIR, 'sub-*/ses-*/dwi/sub-*_ses-*_diffeo.nii.gz')):
    if '_aff_diffeo' in os.path.basename(diffeo_image):
        continue

    sub_ses = SUB_SES_PATTERN.search(diffeo_image).group(0)
    for metric in METRICS:
        target_image = diffeo_image.replace('diffeo.nii.gz', f'diffeo_{metric}.nii.gz')

        cmd = f"""#!/bin/bash
#BSUB -o {LOG_DIR}/extract_{sub_ses}_{metric}.o
#BSUB -e {LOG_DIR}/extract_{sub_ses}_{metric}.e
#BSUB -J extract_{sub_ses}_{metric}

module load fsl/6.0.3

output="{OUTPUT_DIR}/{sub_ses}_{metric}.txt"
> "$output"

for roi in {ROI_DIR}/roi*.nii.gz; do
    mean=$(fslstats "{target_image}" -k "$roi" -M)
    echo "$roi: $mean" >> "$output"
done
"""

        jobscript_path = os.path.join(JOBSCRIPT_DIR, f'extract_{sub_ses}_{metric}.sh')
        with open(jobscript_path, 'w', opener=lambda path, flags: os.open(path, flags, 0o775)) as jobscript_file:
            jobscript_file.write(cmd)
        os.system(f'bsub < {jobscript_path}')
