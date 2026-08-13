#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
code_root=$(cd -- "${script_dir}/.." && pwd)

source "${code_root}/config/project.env"
source "${code_root}/config/dwi.sh"
source "${code_root}/dwi/helpers/qc.sh"

mkdir -p "${QC_DIR}" "${SCRATCH_DIR}"

path_volumes="${QC_DIR}/volumes.csv"
path_tsnr_b0="${QC_DIR}/tsnr_b0.csv"

echo "participant_id,session_id,volumes" > "${path_volumes}"
echo "participant_id,session_id,tsnr_b0" > "${path_tsnr_b0}"

find "${DWI_DIR}" -mindepth 1 -maxdepth 1 -type d -name "sub-*" -printf '%f\n' |
sort |
while read -r participant_id; do

    find "${DWI_DIR}/${participant_id}" -mindepth 1 -maxdepth 1 -type d -name "ses-*" -printf '%f\n' |
    sort |
    while read -r session_id; do

        volumes=$(
            get_volumes \
            --image "${DWI_DIR}/${participant_id}/${session_id}/dwi/${participant_id}_${session_id}_space-ACPC_desc-preproc_dwi.nii.gz"
        )

        tsnr_b0=$(
            get_tsnr_b0 \
            --scratch "${SCRATCH_DIR}" \
            --raw "${PROJECT_DIR}/${participant_id}/${session_id}/dwi"
        )

        echo "${participant_id},${session_id},${volumes}" >> "${path_volumes}"
        echo "${participant_id},${session_id},${tsnr_b0}" >> "${path_tsnr_b0}"

    done
done

rm -rf "${SCRATCH_DIR}"
