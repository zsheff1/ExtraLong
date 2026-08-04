#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
code_root=$(cd -- "${script_dir}/.." && pwd)

source "${code_root}/config/project.env"
source "${code_root}/config/dwi.sh"

script_name=$(basename "${BASH_SOURCE[0]}")
script_stem="${script_name%.sh}"

mkdir -p "${DATA_DIR}" "${TEMPLATEFLOW_HOME}" "${JOBSCRIPT_DIR}/${script_stem}" "${LOG_DIR}/${script_stem}"

find "${PROJECT_DIR}" -mindepth 1 -maxdepth 1 -type d -name "sub-*" -printf '%f\n' |
while read -r sub; do

	dwi_dir=$(find "${PROJECT_DIR}/${sub}" -mindepth 3 -maxdepth 3 -type f -name "*_dwi.nii.gz")
	[[ -n ${dwi_dir} ]] || continue

    jobscript_path="${JOBSCRIPT_DIR}/${script_stem}/${sub}.sh"

    cat <<-EOF > "${jobscript_path}"
	#!/usr/bin/env bash
	#BSUB -J ${script_stem}_${sub}
	#BSUB -n ${NTHREADS}
	#BSUB -R "span[hosts=1]"
	#BSUB -o ${LOG_DIR}/${script_stem}/${sub}.o
	#BSUB -e ${LOG_DIR}/${script_stem}/${sub}.e

	mkdir -p /scratch/\$USER/\$LSB_JOBID
	trap 'echo "Cleaning /scratch/\$USER/\$LSB_JOBID"; rm -rf /scratch/\$USER/\$LSB_JOBID' EXIT

	module load apptainer

	apptainer run --containall \\
	    --bind "${PROJECT_DIR}:/input:ro" \\
	    --bind "${DATA_DIR}:/output" \\
	    --bind "/scratch/\$USER/\$LSB_JOBID:/scratch" \\
	    --bind "${LICENSE}:/license.txt:ro" \\
		--bind "${TEMPLATEFLOW_HOME}:/templateflow:ro" \\
		--env TEMPLATEFLOW_HOME="/templateflow" \\
	    "${CONTAINER}" \\
	    /input /output participant \\
	    --participant-label ${sub} \\
	    --output-resolution ${OUTPUT_RESOLUTION} \\
	    --work-dir /scratch \\
	    --dwi-only \\
	    --stop-on-first-crash \\
	    --fs-license-file /license.txt \\
	    --skip-bids-validation \\
	    --nthreads ${NTHREADS} \\
	    --omp-nthreads ${OMP_NTHREADS}
	EOF

    chmod 775 "${jobscript_path}"
    bsub < "${jobscript_path}"

done
