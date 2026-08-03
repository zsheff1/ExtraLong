#!/usr/bin/env python3

import os
import glob

DATA_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi'
LOG_BASE = '/project/bbl_gur_evolpsy/code/logs/dwi/tbss/tbss_prestats'
JOBSCRIPT_PATH = '/project/bbl_gur_evolpsy/code/jobscripts/dwi/tbss/tbss_prestats.sh'
THRESHOLD = str(0.2)

os.makedirs(os.path.dirname(LOG_BASE), exist_ok = True)
os.makedirs(os.path.dirname(JOBSCRIPT_PATH), exist_ok = True)

cmd = f'''#!/bin/bash
#BSUB -o {LOG_BASE}.o
#BSUB -e {LOG_BASE}.e
#BSUB -J tbss

module load dtitk/2.3.1
module load fsl/6.0.3

cd {DATA_DIR}

tbss_skeleton -i {DATA_DIR}/stats/mean_FA.nii.gz -o {DATA_DIR}/stats/mean_FA_skeleton.nii.gz
tbss_4_prestats {THRESHOLD}

'''

for metric in ['AD', 'MD', 'RD']:
    cmd += f'''# {metric}
tbss_skeleton \\
  -i {DATA_DIR}/stats/mean_FA.nii.gz \\
  -o {DATA_DIR}/stats/mean_{metric}_skeleton.nii.gz \\
  -p {THRESHOLD} \\
    {DATA_DIR}/stats/mean_FA_skeleton_mask_dst.nii.gz \\
    {DATA_DIR}/stats/mean_FA.nii.gz \\
    {DATA_DIR}/stats/all_{metric}.nii.gz \\
    {DATA_DIR}/stats/all_{metric}_skeletonised.nii.gz

'''

# write command to jobscript and execute
with open(JOBSCRIPT_PATH, 'w', opener=lambda path, flags: os.open(path, flags, 0o775)) as jobscript_file:
    jobscript_file.write(cmd)
os.system(f'bsub < {JOBSCRIPT_PATH}')