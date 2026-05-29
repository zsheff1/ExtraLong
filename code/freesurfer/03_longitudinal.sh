#!/usr/bin/env bash

DATA_DIR="/project/ExtraLong/derivatives/freesurfer"
JOBSCRIPT_DIR="/project/ExtraLong/code/jobscripts/freesurfer/03_longitudinal"
LOG_DIR="/project/ExtraLong/code/logs/freesurfer/03_longitudinal"
CONTAINER="/appl/containers/freesurfer_8.2.0.sif"
LICENSE="/project/ExtraLong/code/freesurfer/license.txt"
NTHREADS=4

mkdir -p "${JOBSCRIPT_DIR}" "${LOG_DIR}"

find "${DATA_DIR}" -mindepth 2 -maxdepth 2 -type d -name "Template-*" -printf '%f\n' | while read -r template; do

    sub="sub-${template#Template-}"

    find "${DATA_DIR}/${sub}" -maxdepth 1 -type d -name "ses-*" ! -name "*.long.Template-*" -printf '%f\n' | sort | while read -r ses; do
        
        jobscript_path="${JOBSCRIPT_DIR}/${sub}_${ses}.sh"

        cat <<-EOF > "${jobscript_path}"
		#!/usr/bin/env bash
		#BSUB -J 03_longitudinal_${sub}_${ses}
		#BSUB -n ${NTHREADS}
		#BSUB -R "span[hosts=1]"
		#BSUB -o ${LOG_DIR}/${sub}_${ses}.o
		#BSUB -e ${LOG_DIR}/${sub}_${ses}.e

		export OMP_NUM_THREADS=${NTHREADS}

		module load freesurfer/8.2.0

		export FREESURFER_HOME="${FREESURFER_HOME}"
		source "${FREESURFER_HOME}/SetUpFreeSurfer.sh"
		export SURFER_FRONTDOOR=1
		export FS_LICENSE="${LICENSE}"
		export SUBJECTS_DIR="${OUTPUT_DIR}/${sub}"

		${FREESURFER_HOME}/bin/recon-all \\
		-long "${ses}" "${template}" \\
		-parallel \\
		-openmp ${NTHREADS} \\
		-all

		EOF

        chmod 775 "${jobscript_path}"
        bsub < "${jobscript_path}"

    done
done