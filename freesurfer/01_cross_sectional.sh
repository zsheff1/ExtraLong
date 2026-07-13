#!/usr/bin/env bash

set -euo pipefail

config=${1:?Usage: $0 CONFIG}
source "$config"

script_name=$(basename "${BASH_SOURCE[0]}")
script_stem="${script_name%.sh}"

mkdir -p "${JOBSCRIPT_DIR}/${script_stem}" "${LOG_DIR}/${script_stem}" "${DATA_DIR}"

# Find all T1w images
find "${PROJECT_DIR}" -mindepth 4 -maxdepth 4 -type f -path "*/sub-*/ses-*/anat/*T1w.nii.gz" |
while read -r image; do

    [[ "${image}" =~ (sub-[0-9]{6})_(ses-[0-9]{5}) ]] || continue

    sub="${BASH_REMATCH[1]}"
    ses="${BASH_REMATCH[2]}"

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
	    --bind "${image}:/input.nii.gz:ro" \\
	    --bind "${DATA_DIR}:/data_dir" \\
	    --bind "${LICENSE}:/license.txt:ro" \\
	    --bind "/scratch/\$USER/\$LSB_JOBID:/scratch" \\
	    --pwd /scratch \\
	    --env FS_LICENSE=/license.txt \\
	    --env SUBJECTS_DIR=/data_dir \\
	    --env OMP_NUM_THREADS=${NTHREADS} \\
	    "${CONTAINER}" \\
	    recon-all \\
	    -i /input.nii.gz \\
	    -s "${sub}_${ses}" \\
	    -openmp ${NTHREADS} \\
	    -all
	EOF

    chmod 775 "${jobscript_path}"
    bsub < "${jobscript_path}"

done
