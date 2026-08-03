#!/usr/bin/env python3

import os

FSL_DIR = '$FSLDIR/data/atlases/JHU'
STATS_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi/stats'
ATLAS_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi/atlas'
ROI_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi/atlas/roi'
TARGET_FA = 'mean_FA.nii.gz'
ATLAS_FA = 'JHU-ICBM-FA-2mm.nii.gz'
ATLAS_TRACTS = 'JHU-ICBM-tracts-maxprob-thr25-2mm.nii.gz'
ATLAS_LABELS = 'JHU-ICBM-labels-2mm.nii.gz'
JOBSCRIPT_PATH = '/project/bbl_gur_evolpsy/code/jobscripts/dwi/roi/roi_generate.sh'
LOG_BASE = '/project/bbl_gur_evolpsy/code/logs/dwi/roi/roi_generate'
PAD_EXECUTABLE = '/project/bbl_gur_evolpsy/code/dwi/pad.py'
PAD = '18 19 9 10 18 19'

os.makedirs(os.path.dirname(LOG_BASE), exist_ok = True)
os.makedirs(os.path.dirname(JOBSCRIPT_PATH), exist_ok = True)

cmd = f'''#!/bin/bash
#BSUB -o {LOG_BASE}.o
#BSUB -e {LOG_BASE}.e
#BSUB -J roi_generate

module load afni_openmp/20.1
module load ANTs/2.3.5
module load fsl/6.0.3

mkdir -p {ATLAS_DIR}
mkdir -p {ROI_DIR}

# pad, flip from RPI to LPI, center: for JHU FA and atlas
cp {FSL_DIR}/{ATLAS_FA} {ATLAS_DIR}/{ATLAS_FA}
{PAD_EXECUTABLE} {ATLAS_DIR}/{ATLAS_FA} {ATLAS_DIR}/{ATLAS_FA} {PAD}
fslswapdim {ATLAS_DIR}/{ATLAS_FA} -x y z {ATLAS_DIR}/{ATLAS_FA}
fslorient -swaporient {ATLAS_DIR}/{ATLAS_FA}
3drefit -xorigin 0 -yorigin 0 -zorigin 0 {ATLAS_DIR}/{ATLAS_FA}

cp {FSL_DIR}/{ATLAS_TRACTS} {ATLAS_DIR}/{ATLAS_TRACTS}
{PAD_EXECUTABLE} {ATLAS_DIR}/{ATLAS_TRACTS} {ATLAS_DIR}/{ATLAS_TRACTS} {PAD}
fslswapdim {ATLAS_DIR}/{ATLAS_TRACTS} -x y z {ATLAS_DIR}/{ATLAS_TRACTS}
fslmaths {ATLAS_DIR}/{ATLAS_TRACTS} {ATLAS_DIR}/{ATLAS_TRACTS} -odt char
fslorient -swaporient {ATLAS_DIR}/{ATLAS_TRACTS}
3drefit -xorigin 0 -yorigin 0 -zorigin 0 {ATLAS_DIR}/{ATLAS_TRACTS}

cp {FSL_DIR}/{ATLAS_LABELS} {ATLAS_DIR}/{ATLAS_LABELS}
{PAD_EXECUTABLE} {ATLAS_DIR}/{ATLAS_LABELS} {ATLAS_DIR}/{ATLAS_LABELS} {PAD}
fslswapdim {ATLAS_DIR}/{ATLAS_LABELS} -x y z {ATLAS_DIR}/{ATLAS_LABELS}
fslmaths {ATLAS_DIR}/{ATLAS_LABELS} {ATLAS_DIR}/{ATLAS_LABELS} -odt char
fslorient -swaporient {ATLAS_DIR}/{ATLAS_LABELS}
3drefit -xorigin 0 -yorigin 0 -zorigin 0 {ATLAS_DIR}/{ATLAS_LABELS}

# rigid and affine registration of FA map to mean space
antsRegistration --dimensionality 3 \\
--output {ATLAS_DIR}/ICBM2EVOL_ \\
--interpolation Linear \\
--transform Rigid[0.1] \\
--metric MI[{STATS_DIR}/{TARGET_FA}, {ATLAS_DIR}/{ATLAS_FA}, 1, 32, Regular, 0.25] \\
--convergence [500x250x100, 1e-6, 10] \\
--shrink-factors 4x2x1 \\
--smoothing-sigmas 2x1x0vox \\
--transform Affine[0.1] \\
--metric MI[{STATS_DIR}/{TARGET_FA}, {ATLAS_DIR}/{ATLAS_FA}, 1, 32, Regular, 0.25] \\
--convergence [500x250x100, 1e-6, 10] \\
--shrink-factors 4x2x1 \\
--smoothing-sigmas 2x1x0vox

# nonlinear registration of FA map to mean space
antsRegistration --dimensionality 3 \\
--initial-moving-transform {ATLAS_DIR}/ICBM2EVOL_0GenericAffine.mat \\
--output {ATLAS_DIR}/ICBM2EVOL_ \\
--interpolation Linear \\
--transform SyN[0.1,3,0] \\
--metric CC[{STATS_DIR}/{TARGET_FA}, {ATLAS_DIR}/{ATLAS_FA}, 1, 4] \\
--convergence [100x70x50, 1e-6, 10] \\
--shrink-factors 4x2x1 \\
--smoothing-sigmas 2x1x0vox

# apply these transforms to the atlas, moving it to template space
antsApplyTransforms -d 3 \\
-i {ATLAS_DIR}/{ATLAS_TRACTS} \\
-r {STATS_DIR}/{TARGET_FA} \\
-o {ATLAS_DIR}/{ATLAS_TRACTS.replace('ICBM', 'EVOL')} \\
-t {ATLAS_DIR}/ICBM2EVOL_1Warp.nii.gz \\
-t {ATLAS_DIR}/ICBM2EVOL_0GenericAffine.mat \\
-n GenericLabel

# apply these transforms to the atlas, moving it to template space
antsApplyTransforms -d 3 \\
-i {ATLAS_DIR}/{ATLAS_LABELS} \\
-r {STATS_DIR}/{TARGET_FA} \\
-o {ATLAS_DIR}/{ATLAS_LABELS.replace('ICBM', 'EVOL')} \\
-t {ATLAS_DIR}/ICBM2EVOL_1Warp.nii.gz \\
-t {ATLAS_DIR}/ICBM2EVOL_0GenericAffine.mat \\
-n GenericLabel

# break tracts up into a volume for each region
for i in $(seq 1 $(fslstats {FSL_DIR}/{ATLAS_TRACTS} -R | awk '{{print int($2)}}')); do
    printf -v padded "%02d" $i

    fslmaths {ATLAS_DIR}/{ATLAS_TRACTS.replace('ICBM', 'EVOL')} \\
    -thr $i -uthr $i -bin \\
    {ROI_DIR}/roi_tracts_${{padded}}.nii.gz \\
    -odt char
done

# break labels up into a volume for each region
for i in $(seq 1 $(fslstats {FSL_DIR}/{ATLAS_LABELS} -R | awk '{{print int($2)}}')); do
    printf -v padded "%02d" $i

    fslmaths {ATLAS_DIR}/{ATLAS_LABELS.replace('ICBM', 'EVOL')} \\
    -thr $i -uthr $i -bin \\
    {ROI_DIR}/roi_labels_${{padded}}.nii.gz \\
    -odt char
done

'''

with open(JOBSCRIPT_PATH, 'w', opener=lambda path, flags: os.open(path, flags, 0o775)) as jobscript_file:
    jobscript_file.write(cmd)
os.system(f'bsub < {JOBSCRIPT_PATH}')
