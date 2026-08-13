#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
code_root=$(cd -- "${script_dir}/.." && pwd)

source "${code_root}/config/project.env"
source "${code_root}/config/dwi.sh"
source "${code_root}/dwi/helpers/qc.sh"

mkdir -p "${QC_DIR}" "${SCRATCH_DIR}"

path_proj_dist="${QC_DIR}/proj_dist.csv"

echo "participant_id,session_id,mean_proj_dist" > "${path_proj_dist}"

find "${DWI_DIR}" -mindepth 1 -maxdepth 1 -type d -name "sub-*" -printf '%f\n' |
sort |
while read -r participant_id; do

    find "${DWI_DIR}/${participant_id}" -mindepth 1 -maxdepth 1 -type d -name "ses-*" -printf '%f\n' |
    sort |
    while read -r session_id; do

        proj_dist=$(
            get_mean_projection_distance \
            --scratch "${SCRATCH_DIR}" \
            --fa_map "${DWI_DIR}/${participant_id}/${session_id}/dwi/${participant_id}_${session_id}_diffeo_fa.nii.gz" \
            --mean_fa "${STATS_DIR}/mean_FA.nii.gz" \
            --dst_map "${STATS_DIR}/mean_FA_skeleton_mask_dst.nii.gz" \
            --mask "${STATS_DIR}/mean_FA_skeleton_mask.nii.gz"
        )

        echo "${participant_id},${session_id},${proj_dist}" >> "${path_proj_dist}"

    done
done

rm -rf "${SCRATCH_DIR}"
