#!/usr/bin/env python3
"""
Computes raw QC metrics
"""

import os 
import glob
import re

INPUT_DIR = '/project/bbl_gur_evolpsy'
OUTPUT_DIR = '/project/bbl_gur_evolpsy/derivatives/qc'
EXECUTABLE_DIR = '/project/bbl_projects/apps/melliott/scripts'
JOBSCRIPT_DIR = '/project/bbl_gur_evolpsy/code/jobscripts/qc'
LOG_DIR = '/project/bbl_gur_evolpsy/code/logs/qc'
SUB_PATTERN = re.compile(r'sub-\d+')
SES_PATTERN = re.compile(r'ses-[^/]+')
TASK_PATTERN = re.compile(r'task-[^_]+')
ACQ_PATTERN = re.compile(r'acq-[^_]+')

os.makedirs(JOBSCRIPT_DIR, exist_ok = True)
os.makedirs(LOG_DIR, exist_ok = True)
for mode in ['anat', 'dwi', 'func', 'perf']:
  os.makedirs(os.path.join(OUTPUT_DIR, mode), exist_ok = True)
os.makedirs(os.path.join(OUTPUT_DIR, 'dwi', 'work'), exist_ok = True)


# anat
cmd = f'''#!/bin/bash
#BSUB -o {LOG_DIR}/anat.o
#BSUB -e {LOG_DIR}/anat.e
#BSUB -J qc_anat

module load freesurfer/7.1.1
export FREESURFER_HOME=/appl/freesurfer-7.1.1
source /appl/freesurfer-7.1.1/SetUpFreeSurfer.sh
export SURFER_FRONTDOOR=1
export SUBJECTS_DIR=/appl/freesurfer-7.1.1/subjects
'''

for path in glob.glob(os.path.join(INPUT_DIR, 'derivatives/freesurfer/sub-*/ses-*/surf')):
  sub = SUB_PATTERN.search(path).group(0)
  ses = SES_PATTERN.search(path).group(0)
  if 'long' in ses:
    continue
  cmd += f'''
/appl/freesurfer-7.1.1/bin/mris_euler_number {path}/lh.orig.nofix > {OUTPUT_DIR}/anat/{sub}_{ses}_lh.txt
/appl/freesurfer-7.1.1/bin/mris_euler_number {path}/rh.orig.nofix > {OUTPUT_DIR}/anat/{sub}_{ses}_rh.txt'''

# write command to jobscript and execute
jobscript_path = os.path.join(JOBSCRIPT_DIR, 'anat.sh')
with open(jobscript_path, 'w', opener=lambda path, flags: os.open(path, flags, 0o775)) as jobscript_file:
  jobscript_file.write(cmd)
os.system(f'bsub < {jobscript_path}')


# dwi
cmd = f'''#!/bin/bash
#BSUB -o {LOG_DIR}/dwi.o
#BSUB -e {LOG_DIR}/dwi.e
#BSUB -J qc_dwi

module load fsl
module load afni_openmp

ulimit -c 0

export QAPATH={EXECUTABLE_DIR}
export PATH=$QAPATH:$PATH

cd {EXECUTABLE_DIR}
'''

executable = 'qa_dti_v4.sh'
for path in glob.glob(os.path.join(INPUT_DIR, 'sub-*/ses-*/dwi')):
  sub = SUB_PATTERN.search(path).group(0)
  ses = SES_PATTERN.search(path).group(0)
  if ses == 'ses-EVOL1':
    nifti = glob.glob(os.path.join(path, '*.nii.gz'))[0]
    bval = glob.glob(os.path.join(path, '*.bval'))[0]
    bvec = glob.glob(os.path.join(path, '*.bvec'))[0]
    cmd += f'\n{executable} {nifti} {bval} {bvec} 100 {OUTPUT_DIR}/dwi/{sub}_{ses}.txt'
  elif ses == 'ses-PNC1':
    nifti = os.path.join(OUTPUT_DIR, 'dwi/work', f'{sub}_{ses}_dwi.nii.gz')
    nifti_01 = os.path.join(path, f'{sub}_{ses}_run-01_dwi.nii.gz')
    nifti_02 = os.path.join(path, f'{sub}_{ses}_run-02_dwi.nii.gz')
    bval = os.path.join(OUTPUT_DIR, 'dwi/work', f'{sub}_{ses}_dwi.bval')
    bval_01 = os.path.join(path, f'{sub}_{ses}_run-01_dwi.bval')
    bval_02 = os.path.join(path, f'{sub}_{ses}_run-02_dwi.bval')
    bvec = os.path.join(OUTPUT_DIR, 'dwi/work', f'{sub}_{ses}_dwi.bvec')
    bvec_01 = os.path.join(path, f'{sub}_{ses}_run-01_dwi.bvec')
    bvec_02 = os.path.join(path, f'{sub}_{ses}_run-02_dwi.bvec')
    cmd += f'''
fslmerge -t {nifti} {nifti_01} {nifti_02}
paste -d " " {bval_01} {bval_02} > {bval}
paste -d " " {bvec_01} {bvec_02} > {bvec}
{executable} {nifti} {bval} {bvec} 100 {OUTPUT_DIR}/dwi/{sub}_{ses}.txt'''

# write command to jobscript and execute
jobscript_path = os.path.join(JOBSCRIPT_DIR, 'dwi.sh')
with open(jobscript_path, 'w', opener=lambda path, flags: os.open(path, flags, 0o775)) as jobscript_file:
  jobscript_file.write(cmd)
os.system(f'bsub < {jobscript_path}')


# func
cmd = f'''#!/bin/bash
#BSUB -o {LOG_DIR}/func.o
#BSUB -e {LOG_DIR}/func.e
#BSUB -J qc_func

module load fsl
module load afni_openmp

ulimit -c 0

export QAPATH={EXECUTABLE_DIR}
export PATH=$QAPATH:$PATH

cd {EXECUTABLE_DIR}
'''

executable = 'qa_bold_v4.sh'
for image in glob.glob(os.path.join(INPUT_DIR, 'sub-*/ses-*/func/*bold.nii.gz')):
  sub = SUB_PATTERN.search(image).group(0)
  ses = SES_PATTERN.search(image).group(0)
  task = TASK_PATTERN.search(image).group(0)
  cmd += f'\n{executable} {image} {OUTPUT_DIR}/func/{sub}_{ses}_{task}.txt'
  
# write command to jobscript and execute
jobscript_path = os.path.join(JOBSCRIPT_DIR, 'func.sh')
with open(jobscript_path, 'w', opener=lambda path, flags: os.open(path, flags, 0o775)) as jobscript_file:
  jobscript_file.write(cmd)
os.system(f'bsub < {jobscript_path}')


# perf
cmd = f'''#!/bin/bash
#BSUB -o {LOG_DIR}/perf.o
#BSUB -e {LOG_DIR}/perf.e
#BSUB -J qc_perf

module load fsl
module load afni_openmp

ulimit -c 0

export QAPATH={EXECUTABLE_DIR}
export PATH=$QAPATH:$PATH

cd {EXECUTABLE_DIR}
'''

executable = 'qa_pcasl_v2.sh'
for image in glob.glob(os.path.join(INPUT_DIR, 'sub-*/ses-*/perf/*asl.nii.gz')):
  sub = SUB_PATTERN.search(image).group(0)
  ses = SES_PATTERN.search(image).group(0)
  acq = ACQ_PATTERN.search(image).group(0)
  cmd += f'\n{executable} {image} {OUTPUT_DIR}/perf/{sub}_{ses}_{acq}.txt'

# write command to jobscript and execute
jobscript_path = os.path.join(JOBSCRIPT_DIR, 'perf.sh')
with open(jobscript_path, 'w', opener=lambda path, flags: os.open(path, flags, 0o775)) as jobscript_file:
  jobscript_file.write(cmd)
os.system(f'bsub < {jobscript_path}')
