#!/usr/bin/env bash

INPUT_DIR="/project/ExtraLong"
OUTPUT_DIR="/project/ExtraLong/derivatives/freesurfer"
JOBSCRIPT_DIR="/project/ExtraLong/code/jobscripts/freesurfer/01_cross_sectional"
LOG_DIR="/project/ExtraLong/code/logs/freesurfer/01_cross_sectional"
FREESURFER_HOME="/appl/freesurfer-8.2.0"
LICENSE="/project/ExtraLong/code/freesurfer/license.txt"
NTHREADS=4

mkdir -p "${JOBSCRIPT_DIR}" "${LOG_DIR}" "${OUTPUT_DIR}"

# Find all T1w images
find "${INPUT_DIR}" -type f -path "*/sub-*/ses-*/anat/*T1w.nii.gz" | while read -r image; do

    if [[ "${image}" =~ (sub-[0-9]+).*(ses-[^/_]+) ]]; then
        sub="${BASH_REMATCH[1]}"
        ses="${BASH_REMATCH[2]}"
    fi

    jobscript_path="${JOBSCRIPT_DIR}/${sub}_${ses}.sh"

    cat <<-EOF > "${jobscript_path}"
	#!/usr/bin/env bash
	#BSUB -J 01_cross_sectional_${sub}_${ses}
	#BSUB -n ${NTHREADS}
	#BSUB -R "span[hosts=1]"
	#BSUB -o ${LOG_DIR}/${sub}_${ses}.o
	#BSUB -e ${LOG_DIR}/${sub}_${ses}.e

	export OMP_NUM_THREADS=${NTHREADS}

	mkdir -p "${OUTPUT_DIR}/${sub}"

	module load freesurfer/8.2.0

	export FREESURFER_HOME="${FREESURFER_HOME}"
	source "${FREESURFER_HOME}/SetUpFreeSurfer.sh"
	export SURFER_FRONTDOOR=1
	export FS_LICENSE="${LICENSE}"
	export SUBJECTS_DIR="${OUTPUT_DIR}/${sub}"

	${FREESURFER_HOME}/bin/recon-all \\
	-i ${image} \\
	-s ${ses} \\
	-parallel \\
	-openmp ${NTHREADS} \\
	-all

	EOF

    chmod 775 "${jobscript_path}"
    bsub < "${jobscript_path}"

done
