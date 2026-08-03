#!/usr/bin/env python3

import os
import glob

DWI_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi'
STATS_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi/stats'
LOG_BASE = '/project/bbl_gur_evolpsy/code/logs/dwi/dwi_merge/dwi_merge'
JOBSCRIPT_PATH = '/project/bbl_gur_evolpsy/code/jobscripts/dwi/dwi_merge/dwi_merge.sh'
THRESHOLD = str(0.2)

os.makedirs(os.path.dirname(LOG_BASE), exist_ok = True)
os.makedirs(os.path.dirname(JOBSCRIPT_PATH), exist_ok = True)
os.makedirs(STATS_DIR, exist_ok = True)

images = sorted([image for image in glob.glob(os.path.join(DWI_DIR, 'sub-*/ses-*/dwi/sub-*_ses-*_diffeo.nii.gz')) if '_aff_diffeo' not in os.path.basename(image)])
with open(os.path.join(STATS_DIR, 'subs.txt'), 'w') as file_handler:
    file_handler.writelines(f'{image}\n' for image in images)

cmd = f'''#!/bin/bash
#BSUB -o {LOG_BASE}.o
#BSUB -e {LOG_BASE}.e
#BSUB -J dwi_merge

module load dtitk/2.3.1
module load fsl/6.0.3

TVMean -in {STATS_DIR}/subs.txt -out {STATS_DIR}/mean_tensor.nii.gz
TVtool -in {STATS_DIR}/mean_tensor.nii.gz -fa
mv {STATS_DIR}/mean_tensor_fa.nii.gz {STATS_DIR}/mean_FA.nii.gz
fslmaths {STATS_DIR}/mean_FA.nii.gz -thr {THRESHOLD} -bin {STATS_DIR}/mean_FA_mask.nii.gz -odt char
'''

for metric in ['AD', 'FA', 'MD', 'RD']:
    metric_images = ' '.join([image.replace('diffeo.nii.gz', f'diffeo_{metric.lower()}.nii.gz') for image in images])
    cmd += f'fslmerge -t {STATS_DIR}/all_{metric}.nii.gz {metric_images}\n'

# write command to jobscript and execute
with open(JOBSCRIPT_PATH, 'w', opener=lambda path, flags: os.open(path, flags, 0o775)) as jobscript_file:
    jobscript_file.write(cmd)
os.system(f'bsub < {JOBSCRIPT_PATH}')