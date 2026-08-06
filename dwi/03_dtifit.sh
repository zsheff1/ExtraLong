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

        dwi="${path}/${sub}_${ses}_space-ACPC_desc-pad_dwi.nii.gz"
        mask="${path}/${sub}_${ses}_space-ACPC_desc-pad_mask.nii.gz"
        bvals="${path}/${sub}_${ses}_space-ACPC_desc-preproc_dwi.bval"
        bvecs="${path}/${sub}_${ses}_space-ACPC_desc-preproc_dwi.bvec"
        out="${path}/${sub}_${ses}"

        [[ -f "${dwi}" &&
           -f "${mask}" &&
           -f "${bvals}" &&
           -f "${bvecs}" ]] || continue

        jobscript_path="${JOBSCRIPT_DIR}/${script_stem}/${sub}_${ses}.sh"

		cat <<-EOF > "${jobscript_path}"
		#!/usr/bin/env bash
		#BSUB -J ${script_stem}_${sub}_${ses}
		#BSUB -o ${LOG_DIR}/${script_stem}/${sub}_${ses}.o
		#BSUB -e ${LOG_DIR}/${script_stem}/${sub}_${ses}.e

		module load fsl/6.0.3

		dtifit \\
		    --data=${dwi} \\
		    --out=${out} \\
		    --mask=${mask} \\
		    --bvecs=${bvecs} \\
		    --bvals=${bvals}
		EOF

        chmod 775 "${jobscript_path}"
        bsub < "${jobscript_path}"

    done
done