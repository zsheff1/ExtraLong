#!/usr/bin/env bash

DATA_DIR="/project/ExtraLong/derivatives/freesurfer"
JOBSCRIPT_DIR="/project/ExtraLong/code/jobscripts/freesurfer/07_local_gyrification_index"
LOG_DIR="/project/ExtraLong/code/logs/freesurfer/07_local_gyrification_index"
CONTAINER="/appl/containers/freesurfer_8.2.0.sif"
LICENSE="/project/ExtraLong/code/anat/freesurfer_license/license.txt"
SUBJECTSFILE="${DATA_DIR}/subjectsfile.txt"

mkdir -p "${JOBSCRIPT_DIR}" "${LOG_DIR}"

while read -r sub_ses; do

    [[ "${sub_ses}" =~ (sub-[0-9]{6})_(ses-[0-9]{5}) ]]

    sub="${BASH_REMATCH[1]}"
    ses="${BASH_REMATCH[2]}"

    if [[ "${sub_ses}" =~ ^sub-[0-9]{6}_ses-[0-9]{5}\.long\.sub-[0-9]{6}$ ]]; then
        timepoint="-long ${sub}_${ses} ${sub}"
    else
        timepoint="-s ${sub_ses}"
    fi

    jobscript_path="${JOBSCRIPT_DIR}/${sub}_${ses}.sh"

    cat <<-EOF > "${jobscript_path}"
	#!/usr/bin/env bash
	#BSUB -J 07_local_gyrification_index_${sub}_${ses}
	#BSUB -m galton
	#BSUB -o ${LOG_DIR}/${sub}_${ses}.o
	#BSUB -e ${LOG_DIR}/${sub}_${ses}.e

	mkdir -p /scratch/\$USER/\$LSB_JOBID
	trap 'echo "Cleaning /scratch/\$USER/\$LSB_JOBID"; rm -rf /scratch/\$USER/\$LSB_JOBID' EXIT

	module load apptainer

	apptainer exec --containall \\
	    --bind "${DATA_DIR}:/data_dir" \\
	    --bind "${LICENSE}:/license.txt:ro" \\
	    --bind "/commapp/matlab2019b:/commapp/matlab2019b" \\
	    --bind "/scratch/\$USER/\$LSB_JOBID:/scratch" \\
	    --pwd /scratch \\
	    --env FS_LICENSE=/license.txt \\
	    --env SUBJECTS_DIR=/data_dir \\
	    --env MATLAB=/commapp/matlab2019b/bin/matlab \\
	    --env MATLAB_PREFDIR=/scratch/matlab_prefs \\
	    --env PREPEND_PATH=/commapp/matlab2019b/bin \\
	    "${CONTAINER}" \\
	    recon-all \\
	    ${timepoint} \\
	    -localGI
	EOF

    chmod 775 "${jobscript_path}"
    bsub < "${jobscript_path}"

done < "${SUBJECTSFILE}"
