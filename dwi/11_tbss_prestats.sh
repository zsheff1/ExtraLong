#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
code_root=$(cd -- "${script_dir}/.." && pwd)

source "${code_root}/config/project.env"
source "${code_root}/config/dwi.sh"

script_name=$(basename "${BASH_SOURCE[0]}")
script_stem="${script_name%.sh}"

mkdir -p "${STATS_DIR}" "${LOG_DIR}/${script_stem}"

jobscript_path="${JOBSCRIPT_DIR}/${script_stem}.sh"

cat <<-EOF > "${jobscript_path}"
#!/bin/bash
#BSUB -J ${script_stem}
#BSUB -o ${LOG_DIR}/${script_stem}/${script_stem}.o
#BSUB -e ${LOG_DIR}/${script_stem}/${script_stem}.e

module load dtitk/2.3.1
module load fsl/6.0.3

cd "${DATA_DIR}"

tbss_skeleton \\
    -i "${DATA_DIR}/stats/mean_FA.nii.gz" \\
    -o "${DATA_DIR}/stats/mean_FA_skeleton.nii.gz"

tbss_4_prestats "${THRESHOLD}"

for metric in AD MD RD; do
    tbss_skeleton \\
    -i "${DATA_DIR}/stats/mean_FA.nii.gz" \\
    -o "${DATA_DIR}/stats/mean_\${metric}_skeleton.nii.gz" \\
    -p "${THRESHOLD}" \\
    "${DATA_DIR}/stats/mean_FA_skeleton_mask_dst.nii.gz" \\
    "${DATA_DIR}/stats/mean_FA.nii.gz" \\
    "${DATA_DIR}/stats/all_\${metric}.nii.gz" \\
    "${DATA_DIR}/stats/all_\${metric}_skeletonised.nii.gz"
done
EOF

chmod 775 "${jobscript_path}"
bsub < "${jobscript_path}"
