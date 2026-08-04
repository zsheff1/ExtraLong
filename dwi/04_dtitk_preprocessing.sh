#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
code_root=$(cd -- "${script_dir}/.." && pwd)

source "${code_root}/config/project.env"
source "${code_root}/config/dwi.sh"

script_name=$(basename "${BASH_SOURCE[0]}")
script_stem="${script_name%.sh}"

mkdir -p "${JOBSCRIPT_DIR}/${script_stem}" "${LOG_DIR}/${script_stem}"

find "${DATA_DIR}" -mindepth 1 -maxdepth 1 -type d -name "sub-*" -printf '%f\n' |
while read -r sub; do

    find "${DATA_DIR}/${sub}" -mindepth 1 -maxdepth 1 -type d -name "ses-*" -printf '%f\n' |
    while read -r ses; do

        path="${DATA_DIR}/${sub}/${ses}/dwi"
        input="${path}/${sub}_${ses}"
        output="${path}/${sub}_${ses}.nii.gz"

        [[ -f "${path}/${sub}_${ses}_FA.nii.gz" ]] || continue

        jobscript_path="${JOBSCRIPT_DIR}/${script_stem}/${sub}_${ses}.sh"

		cat <<-EOF > "${jobscript_path}"
		#!/usr/bin/env bash
		#BSUB -J ${script_stem}_${sub}_${ses}
		#BSUB -o ${LOG_DIR}/${script_stem}/${sub}_${ses}.o
		#BSUB -e ${LOG_DIR}/${script_stem}/${sub}_${ses}.e

		module load dtitk/2.3.1

		TVFromEigenSystem -basename ${input} -type FSL -out ${output}
		TVtool -in ${output} -scale ${FACTOR} -out ${output}
		TVtool -in ${output} -spd -out ${output}
		TVAdjustVoxelspace -in ${output} -origin 0 0 0
		EOF

        chmod 775 "${jobscript_path}"
        bsub < "${jobscript_path}"

    done
done