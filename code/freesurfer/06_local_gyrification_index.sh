#!/usr/bin/env bash

DATA_DIR="/project/ExtraLong/derivatives/freesurfer"
JOBSCRIPT_DIR="/project/ExtraLong/code/jobscripts/freesurfer/06_local_gyrification_index"
LOG_DIR="/project/ExtraLong/code/logs/freesurfer/06_local_gyrification_index"
FREESURFER_HOME="/appl/freesurfer-8.2.0"
LICENSE="/project/ExtraLong/code/anat/freesurfer_license/license.txt"

mkdir -p "${JOBSCRIPT_DIR}" "${LOG_DIR}" "${DATA_DIR}/scratch"

find "${DATA_DIR}" -maxdepth 1 -type d -path "*/sub-*_ses-*" | while read -r dir; do

    if [[ "${dir}" =~ (sub-[0-9]+).*(ses-[^/_]+) ]]; then
        sub="${BASH_REMATCH[1]}"
        ses="${BASH_REMATCH[2]}"
    fi

    jobscript_path="${JOBSCRIPT_DIR}/${sub}_${ses}.sh"

    cat <<- EOF > "${jobscript_path}"
	#!/usr/bin/env bash
	#BSUB -J 06_local_gyrification_index_${sub}_${ses}
	#BSUB -m galton
	#BSUB -o ${LOG_DIR}/${sub}_${ses}.o
	#BSUB -e ${LOG_DIR}/${sub}_${ses}.e
	
	module load freesurfer/8.2.0
	module load matlab/2025a

	export FREESURFER_HOME="${FREESURFER_HOME}"
	source "${FREESURFER_HOME}/SetUpFreeSurfer.sh"
	export SURFER_FRONTDOOR=1
	export FS_LICENSE="${LICENSE}"
	export SUBJECTS_DIR="${DATA_DIR}/${sub}"

	"${FREESURFER_HOME}/bin/${executable}" \\
	-s "${sub}_${ses}" \\
	-localGI

	EOF

    chmod 775 "${jobscript_path}"
    bsub < "${jobscript_path}"

done
