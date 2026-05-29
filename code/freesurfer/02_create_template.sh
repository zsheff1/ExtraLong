#!/usr/bin/env bash

DATA_DIR="/project/ExtraLong/derivatives/freesurfer"
JOBSCRIPT_DIR="/project/ExtraLong/code/jobscripts/freesurfer/02_create_template"
LOG_DIR="/project/ExtraLong/code/logs/freesurfer/02_create_template"
FREESURFER_HOME="/appl/freesurfer-8.2.0"
LICENSE="/project/ExtraLong/code/freesurfer/license.txt"
NTHREADS=4

mkdir -p "${JOBSCRIPT_DIR}" "${LOG_DIR}"

find "${DATA_DIR}" -maxdepth 1 -type d -name "sub-*" -printf '%f\n' | while read -r sub; do
    
    sub_base="${sub#sub-}"
    mapfile -t sess < <(
        find "${DATA_DIR}/${sub}" -maxdepth 1 -type d -name "ses-*" ! -name "*.long.Template-*" -printf '%f\n' | sort
    )

    if (( ${#sess[@]} < 2 )); then
        continue
    fi

    timepoints=""
    for ses in "${sess[@]}"; do
        timepoints+="-tp ${ses} "
    done

    jobscript_path="${JOBSCRIPT_DIR}/${sub}.sh"

    cat <<-EOF > "${jobscript_path}"
	#!/usr/bin/env bash
	#BSUB -J 02_create_template_${sub}
	#BSUB -n ${NTHREADS}
	#BSUB -R "span[hosts=1]"
	#BSUB -o ${LOG_DIR}/${sub}.o
	#BSUB -e ${LOG_DIR}/${sub}.e

	export OMP_NUM_THREADS=${NTHREADS}

	module load freesurfer/8.2.0

	export FREESURFER_HOME="${FREESURFER_HOME}"
	source "${FREESURFER_HOME}/SetUpFreeSurfer.sh"
	export SURFER_FRONTDOOR=1
	export FS_LICENSE="${LICENSE}"
	export SUBJECTS_DIR="${DATA_DIR}/${sub}"

	${FREESURFER_HOME}/bin/recon-all \\
	-base Template-${sub_base} \\
	"${timepoints}" \\
	-parallel \\
	-openmp ${NTHREADS} \\
	-all

	EOF

    chmod 775 "${jobscript_path}"
    bsub < "${jobscript_path}"

done
