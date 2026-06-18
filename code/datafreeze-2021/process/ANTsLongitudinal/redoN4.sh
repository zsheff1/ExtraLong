#!/bin/bash

# Set env vars for ANTs
export ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS=1
export ANTS_RANDOM_SEED=1

# Make tmp dir
tmpdir="/data/output/tmp"
mkdir -p ${tmpdir}

InDir=/data/input
SubDir=/data/output

sessions="$@"

# Get subject label.
ses=$(echo ${sessions} | cut -d ' ' -f 1)
sub=$(find ${InDir}/fmriprep/ -name "*${ses}_*desc-preproc_T1w.nii.gz" -not -name "*space*" -exec basename {} \; | cut -d _ -f 1)

# For each session, preprocess the T1w image and brain mask.
for ses in ${sessions}; do

	# Make output sub-directory per session.
	SesDir=${SubDir}/sessions/${ses}
	mkdir -p ${SesDir}

	# Copy T1w image to session output dir.
	t1w="${SesDir}/${sub}_${ses}_T1w.nii.gz"
	find ${InDir}/fmriprep/${ses}/anat -name "${sub}_${ses}_*desc-preproc_T1w.nii.gz" -not -name "*space*" \
		-exec cp {} "${t1w}" \;

	# TODO: try with ANTsBrainExtraction??
	# Copy T1w brain mask to session output dir.
	mask="${SesDir}/${sub}_${ses}_brain-mask.nii.gz"
	find ${InDir}/fmriprep/${ses}/anat -name "${sub}_${ses}_*desc-brain_mask.nii.gz" -not -name "*space*" \
		-exec cp {} "${mask}" \;

	# Dialate and smooth brain mask from fMRIPrep to use as weight image in N4
	n4weight="${tmpdir}/${sub}_${ses}_brain-mask-DS.nii.gz"
	ImageMath 3 ${n4weight} MD ${mask} 5 879 # Dialate x5
	SmoothImage 3 ${n4weight} 3 ${n4weight}  # Smooth x3

	# Threshold T1w image to get mask of non-zero intensities for N4.
	n4mask="${tmpdir}/${sub}_${ses}_N4Mask.nii.gz"
	ThresholdImage 3 ${t1w} ${n4mask} 0.01 Inf

	# N4 Bias correction with weighted with mask.
	PROGNAME="N4BiasFieldCorrection"
	# TODO: parameter tuning??
	N4BiasFieldCorrection -d 3 \
		-b [ 200 ] \
		-c [ 100x100x100x100 ] \
		--input-image ${t1w} \
		--mask-image ${n4mask} \
		--weight-image ${n4weight} \
		--output ${t1w}

	# Pad and scale the N4-corrected T1w image.
	ImageMath 3 ${t1w} PadImage ${t1w} 25 # Pad x 25 voxels
	ImageMath 3 ${t1w} Normalize ${t1w} 1 # Normalize to [0, 1]
	
	# Also pad the T1w mask to stay in same space as T1w.
	ImageMath 3 ${mask} PadImage ${mask} 25 # Pad x 25 voxels

done
