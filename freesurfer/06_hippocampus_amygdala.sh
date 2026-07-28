#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
code_root=$(cd -- "${script_dir}/.." && pwd)

source "${code_root}/config/project.env"
source "${code_root}/config/freesurfer.sh"

script_name=$(basename "${BASH_SOURCE[0]}")
script_stem="${script_name%.sh}"

mkdir -p "${JOBSCRIPT_DIR}/${script_stem}" "${LOG_DIR}/${script_stem}"

declare -A seen

while read -r sub_ses; do

    [[ "${sub_ses}" =~ (sub-[0-9]{6})_(ses-[0-9]{5}) ]]

    sub="${BASH_REMATCH[1]}"
    ses="${BASH_REMATCH[2]}"

    if [[ "${sub_ses}" =~ ^sub-[0-9]{6}_ses-[0-9]{5}\.long\.sub-[0-9]{6}$ ]]; then
        if [[ -z "${seen[$sub]}" ]]; then
            seen[$sub]=1
            timepoint="--long-base ${sub}"
        else
            continue
        fi
    else
        timepoint="--cross ${sub_ses}"
    fi

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
	    --bind "/commapp/matlab2019b:/commapp/matlab2019b" \\
	    --bind "/scratch/\$USER/\$LSB_JOBID:/scratch" \\
	    --pwd /scratch \\
	    --env FS_LICENSE=/license.txt \\
	    --env SUBJECTS_DIR=/data_dir \\
	    --env OMP_NUM_THREADS=${NTHREADS} \\
	    "${CONTAINER}" \\
	    segment_subregions hippo-amygdala ${timepoint} --threads ${NTHREADS}

	EOF

    chmod 775 "${jobscript_path}"
    bsub < "${jobscript_path}"

done < "${SUBJECTSFILE}"
