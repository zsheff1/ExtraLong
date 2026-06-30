#!/usr/bin/env bash

DATA_DIR="/project/ExtraLong/derivatives/freesurfer"
JOBSCRIPT_DIR="/project/ExtraLong/code/jobscripts/freesurfer/03_longitudinal"
LOG_DIR="/project/ExtraLong/code/logs/freesurfer/03_longitudinal"
CONTAINER="/appl/containers/freesurfer_8.2.0.sif"
LICENSE="/project/ExtraLong/code/freesurfer/license.txt"
NTHREADS=4

mkdir -p "${JOBSCRIPT_DIR}" "${LOG_DIR}"

find "${DATA_DIR}" -mindepth 1 -maxdepth 1 -type d -name "sub-*" ! -name "sub-*_ses-*" -printf '%f\n' |
while read -r sub; do

    find "${DATA_DIR}" -mindepth 1 -maxdepth 1 -type d -name "${sub}_ses-*" ! -name "*.long.sub-*" -printf '%f\n' |
    while read -r sub_ses; do

        ses="${sub_ses#${sub}_}"

        jobscript_path="${JOBSCRIPT_DIR}/${sub}_${ses}.sh"

        cat <<-EOF > "${jobscript_path}"
		#!/usr/bin/env bash
		#BSUB -J 03_longitudinal_${sub}_${ses}
		#BSUB -n ${NTHREADS}
		#BSUB -R "span[hosts=1]"
		#BSUB -o ${LOG_DIR}/${sub}_${ses}.o
		#BSUB -e ${LOG_DIR}/${sub}_${ses}.e

		mkdir -p /scratch/\$USER/\$LSB_JOBID
		trap 'echo "Cleaning /scratch/\$USER/\$LSB_JOBID"; rm -rf /scratch/\$USER/\$LSB_JOBID' EXIT

		module load apptainer

		apptainer exec --containall \\
		    --bind "${DATA_DIR}:/data_dir" \\
		    --bind "${LICENSE}:/license.txt" \\
		    --bind "/scratch/\$USER/\$LSB_JOBID:/scratch" \\
		    --pwd /scratch \\
		    --env FS_LICENSE=/license.txt \\
		    --env SUBJECTS_DIR=/data_dir \\
		    --env OMP_NUM_THREADS=${NTHREADS} \\
		    "${CONTAINER}" \\
		    recon-all \\
		    -long "${sub}_${ses}" "${sub}" \\
		    -openmp ${NTHREADS} \\
		    -all
		EOF

        chmod 775 "${jobscript_path}"
        bsub < "${jobscript_path}"

    done
done
