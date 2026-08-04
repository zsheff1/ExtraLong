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
		module load fsl/6.0.3

		dti_rigid_reg ${DATA_DIR}/template/template.nii.gz ${path}/${sub}_${ses}.nii.gz EDS 4 4 4 0.01
		dti_affine_reg ${DATA_DIR}/template/template.nii.gz ${path}/${sub}_${ses}.nii.gz EDS 4 4 4 0.01 1
		dti_diffeomorphic_reg ${DATA_DIR}/template/template.nii.gz ${path}/${sub}_${ses}_aff.nii.gz ${DATA_DIR}/template/template_mask.nii.gz 1 6 0.002
		dti_warp_to_template ${path}/${sub}_${ses}.nii.gz ${DATA_DIR}/template/template.nii.gz 2 2 2
		TVtool -in ${path}/${sub}_${ses}_diffeo.nii.gz -fa
		TVtool -in ${path}/${sub}_${ses}_diffeo.nii.gz -eigs
		fslmaths ${path}/${sub}_${ses}_diffeo_lambda2.nii.gz -add ${path}/${sub}_${ses}_diffeo_lambda3.nii.gz -div 2 ${path}/${sub}_${ses}_diffeo_rd.nii.gz
		fslmaths ${path}/${sub}_${ses}_diffeo_lambda1.nii.gz -add ${path}/${sub}_${ses}_diffeo_lambda2.nii.gz -add ${path}/${sub}_${ses}_diffeo_lambda3.nii.gz -div 3 ${path}/${sub}_${ses}_diffeo_md.nii.gz
		cp ${path}/${sub}_${ses}_diffeo_lambda1.nii.gz ${path}/${sub}_${ses}_diffeo_ad.nii.gz
		EOF

        chmod 775 "${jobscript_path}"
        bsub < "${jobscript_path}"

    done
done