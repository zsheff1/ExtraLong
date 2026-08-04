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

        dwi_qsi="${path}/${sub}_${ses}_space-ACPC_desc-preproc_dwi.nii.gz"
        dwi_rpi="${path}/${sub}_${ses}_space-ACPC_desc-rpi_dwi.nii.gz"
        dwi_pad="${path}/${sub}_${ses}_space-ACPC_desc-pad_dwi.nii.gz"
        mask_qsi="${path}/${sub}_${ses}_space-ACPC_desc-brain_mask.nii.gz"
        mask_rpi="${path}/${sub}_${ses}_space-ACPC_desc-rpi_mask.nii.gz"
        mask_pad="${path}/${sub}_${ses}_space-ACPC_desc-pad_mask.nii.gz"

        [[ -f "${dwi_qsi}" && -f "${mask_qsi}" ]] || continue

        jobscript_path="${JOBSCRIPT_DIR}/${script_stem}/${sub}_${ses}.sh"

		cat <<-EOF > "${jobscript_path}"
		#!/usr/bin/env bash
		#BSUB -J ${script_stem}_${sub}_${ses}
		#BSUB -o ${LOG_DIR}/${script_stem}/${sub}_${ses}.o
		#BSUB -e ${LOG_DIR}/${script_stem}/${sub}_${ses}.e

		module load afni_openmp/20.1

		# RPI FLIP
		${RPI_EXECUTABLE} ${dwi_qsi} ${dwi_rpi}
		${RPI_EXECUTABLE} ${mask_qsi} ${mask_rpi}

		# PADDING
		${PAD_EXECUTABLE} ${dwi_rpi} ${dwi_pad} ${PAD_4D}
		${PAD_EXECUTABLE} ${mask_rpi} ${mask_pad} ${PAD_3D}
		EOF

        chmod 775 "${jobscript_path}"
        bsub < "${jobscript_path}"

    done
done