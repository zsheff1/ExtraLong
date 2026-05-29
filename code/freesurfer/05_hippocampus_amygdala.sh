#!/usr/bin/env python3

DATA_DIR="/project/ExtraLong/derivatives/freesurfer"
JOBSCRIPT_DIR="/project/ExtraLong/code/jobscripts/freesurfer/05_hippocampus_amygdala"
LOG_DIR="/project/ExtraLong/code/logs/freesurfer/05_hippocampus_amygdala"
FREESURFER_HOME="/appl/freesurfer-8.2.0"
LICENSE="/project/ExtraLong/code/freesurfer/license.txt"
NTHREADS=4

mkdir -p "${JOBSCRIPT_DIR}" "${LOG_DIR}"

find "${DATA_DIR}" -maxdepth 1 -type d -name "sub-*" -printf '%f\n' | while read -r sub; do
    
    mapfile -t sess < <(
        find "${DATA_DIR}/${sub}" -maxdepth 1 -type d -name "ses-*" ! -name "*.long.Template-*" -printf '%f\n' | sort
    )

    if (( ${#sess[@]} > 1 )); then
        executable="segmentHA_T1_long.sh"
        label="Template-${sub#sub-}"
    elif (( ${#sess[@]} == 1 )); then
        executable="segmentHA_T1.sh"
        label="${sess[0]}"
    else
        continue
    fi

    jobscript_path="${JOBSCRIPT_DIR}/${sub}.sh"

    cat <<- EOF > "${jobscript_path}"
	#!/usr/bin/env bash
	#BSUB -J 05_hippocampus_amygdala_${sub}
	#BSUB -m galton
	#BSUB -o {LOG_DIR}/{sub}.o
	#BSUB -e {LOG_DIR}/{sub}.e

	export OMP_NUM_THREADS=${NTHREADS}

	module load freesurfer/8.2.0
	module load matlab/2025a

	export FREESURFER_HOME="${FREESURFER_HOME}"
	source "${FREESURFER_HOME}/SetUpFreeSurfer.sh"
	export SURFER_FRONTDOOR=1
	export FS_LICENSE="${LICENSE}"
	export SUBJECTS_DIR="${DATA_DIR}/${sub}"

	"${FREESURFER_HOME}/bin/${executable}" \\
	${label}

	EOF

    chmod 775 "${jobscript_path}"
    bsub < "${jobscript_path}"

done