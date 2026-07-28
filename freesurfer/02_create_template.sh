#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
code_root=$(cd -- "${script_dir}/.." && pwd)

source "${code_root}/config/project.env"
source "${code_root}/config/freesurfer.sh"

script_name=$(basename "${BASH_SOURCE[0]}")
script_stem="${script_name%.sh}"

mkdir -p "${JOBSCRIPT_DIR}/${script_stem}" "${LOG_DIR}/${script_stem}"

for sub in $(find "${FREESURFER_DATA_DIR}" -mindepth 1 -maxdepth 1 -type d -name 'sub-*_ses-*' -printf '%f\n' \
    | sed -E 's#(sub-[0-9]{6})_ses-[0-9]{5}#\1#' \
    | sort | uniq -d); do

    timepoints=""
    for ses_dir in "${FREESURFER_DATA_DIR}/${sub}"_ses-*; do
        sub_ses=$(basename "$ses_dir")
        [[ "${sub_ses}" =~ ^sub-[0-9]{6}_ses-[0-9]{5}$ ]] || continue
        timepoints+="-tp ${sub_ses} "
    done

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

	apptainer exec --containall \\
	    --bind "${FREESURFER_DATA_DIR}:/data_dir" \\
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
