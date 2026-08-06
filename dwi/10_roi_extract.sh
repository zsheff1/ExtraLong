#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
code_root=$(cd -- "${script_dir}/.." && pwd)

source "${code_root}/config/project.env"
source "${code_root}/config/dwi.sh"

script_name=$(basename "${BASH_SOURCE[0]}")
script_stem="${script_name%.sh}"

mkdir -p "${JOBSCRIPT_DIR}/${script_stem}" "${LOG_DIR}/${script_stem}" "${STATS_DIR}/roi"

find "${DATA_DIR}" -mindepth 1 -maxdepth 1 -type d -name "sub-*" -printf '%f\n' |
while read -r sub; do

    find "${DATA_DIR}/${sub}" -mindepth 1 -maxdepth 1 -type d -name "ses-*" -printf '%f\n' |
    while read -r ses; do

        jobscript_path="${JOBSCRIPT_DIR}/${script_stem}/${sub}_${ses}.sh"

		cat <<-EOF > "${jobscript_path}"
		#!/usr/bin/env bash
		#BSUB -J ${script_stem}_${sub}_${ses}
		#BSUB -o ${LOG_DIR}/${script_stem}/${sub}_${ses}.o
		#BSUB -e ${LOG_DIR}/${script_stem}/${sub}_${ses}.e

		module load fsl/6.0.3

		output="${STATS_DIR}/roi/${sub}_${ses}.csv"
		echo "sub,ses,metric,atlas,region,value" > "\${output}"

		for metric in ad fa md rd; do

		    target_image="${DATA_DIR}/${sub}/${ses}/dwi/${sub}_${ses}_diffeo_\${metric}.nii.gz"
		    [[ -f "\${target_image}" ]] || continue

		    for roi in "${ROI_DIR}"/roi*.nii.gz; do

		        [[ "\${roi}" =~ roi_([a-z]+)_([0-9]+)\.nii\.gz$ ]]
		        atlas="\${BASH_REMATCH[1]}"
		        region="\${BASH_REMATCH[2]}"

		        value=\$(fslstats "\${target_image}" -k "\${roi}" -M)
		        echo "${sub},${ses},\${metric},\${atlas},\${region},\${value}" >> "\${output}"
		    done
		done
		EOF

        chmod 775 "${jobscript_path}"
        bsub < "${jobscript_path}"

    done
done
