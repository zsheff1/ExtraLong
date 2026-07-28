#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
code_root=$(cd -- "${script_dir}/.." && pwd)

source "${code_root}/config/project.env"
source "${code_root}/config/freesurfer.sh"

script_name=$(basename "${BASH_SOURCE[0]}")
script_stem="${script_name%.sh}"

mkdir -p "${JOBSCRIPT_DIR}/${script_stem}" "${LOG_DIR}/${script_stem}"

find "${FREESURFER_DATA_DIR}" -mindepth 1 -maxdepth 1 -type d -name "sub-*" ! -name "sub-*_ses-*" -printf '%f\n' |
while read -r sub; do

    find "${FREESURFER_DATA_DIR}" -mindepth 1 -maxdepth 1 -type d -name "${sub}_ses-*" ! -name "*.long.sub-*" -printf '%f\n' |
    while read -r sub_ses; do

        ses="${sub_ses#${sub}_}"

        jobscript_path="${JOBSCRIPT_DIR}/${script_stem}/${sub}_${ses}.sh"

        cat <<-EOF > "${jobscript_path}"
		#!/usr/bin/env bash
		#BSUB -J ${script_stem}_${sub}_${ses}
		#BSUB -n ${NTHREADS}
		#BSUB -R "span[hosts=1]"
		#BSUB -o ${LOG_DIR}/${script_stem}/${sub}_${ses}.o
		#BSUB -e ${LOG_DIR}/${script_stem}/${sub}_${ses}.e

		mkdir -p /scratch/\$USER/\$LSB_JOBID
		trap 'echo "Cleaning /scratch/\$USER/\$LSB_JOBID"; rm -rf /scratch/\$USER/\$LSB_JOBID' EXIT

		module load apptainer

		apptainer exec --containall \\
		    --bind "${FREESURFER_DATA_DIR}:/data_dir" \\
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
