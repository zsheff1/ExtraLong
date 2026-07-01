#!/usr/bin/env bash

DATA_DIR="/project/ExtraLong/derivatives/freesurfer"
JOBSCRIPT_DIR="/project/ExtraLong/code/jobscripts/freesurfer/02_create_template"
LOG_DIR="/project/ExtraLong/code/logs/freesurfer/02_create_template"
CONTAINER="/appl/containers/freesurfer_8.2.0.sif"
LICENSE="/project/ExtraLong/code/freesurfer/license.txt"
NTHREADS=4

mkdir -p "${JOBSCRIPT_DIR}" "${LOG_DIR}"

for sub in $(find "${DATA_DIR}" -mindepth 1 -maxdepth 1 -type d -name 'sub-*_ses-*' -printf '%f\n' \
    | sed -E 's#(sub-[0-9]{6})_ses-[0-9]{5}#\1#' \
    | sort | uniq -d); do

    timepoints=""
    for ses_dir in "${DATA_DIR}/${sub}"_ses-*; do
        sub_ses=$(basename "$ses_dir")
        [[ "${sub_ses}" =~ ^sub-[0-9]{6}_ses-[0-9]{5}$ ]] || continue
        timepoints+="-tp ${sub_ses} "
    done

    jobscript_path="${JOBSCRIPT_DIR}/${sub}.sh"

    cat <<-EOF > "${jobscript_path}"
	#!/usr/bin/env bash
	#BSUB -J 02_create_template_${sub}
	#BSUB -n ${NTHREADS}
	#BSUB -R "span[hosts=1]"
	#BSUB -o ${LOG_DIR}/${sub}.o
	#BSUB -e ${LOG_DIR}/${sub}.e

	mkdir -p /scratch/\$USER/\$LSB_JOBID
	trap 'echo "Cleaning /scratch/\$USER/\$LSB_JOBID"; rm -rf /scratch/\$USER/\$LSB_JOBID' EXIT

	module load apptainer

	apptainer exec --containall \\
	    --bind "${DATA_DIR}:/data_dir" \\
	    --bind "${LICENSE}:/license.txt:ro" \\
	    --bind "/scratch/\$USER/\$LSB_JOBID:/scratch" \\
	    --pwd /scratch \\
	    --env FS_LICENSE=/license.txt \\
	    --env SUBJECTS_DIR=/data_dir \\
	    --env OMP_NUM_THREADS=${NTHREADS} \\
	    "${CONTAINER}" \\
	    recon-all \\
	    -base ${sub} \\
	    ${timepoints} \\
	    -openmp ${NTHREADS} \\
	    -all
	EOF

    chmod 775 "${jobscript_path}"
    bsub < "${jobscript_path}"

done
