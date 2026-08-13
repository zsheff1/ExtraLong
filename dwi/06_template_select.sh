#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
code_root=$(cd -- "${script_dir}/.." && pwd)

source "${code_root}/config/project.env"
source "${code_root}/config/dwi.sh"

script_name=$(basename "${BASH_SOURCE[0]}")
script_stem="${script_name%.sh}"

mkdir -p "${JOBSCRIPT_DIR}/${script_stem}" "${LOG_DIR}/${script_stem}" "${BUILD_DIR}" "${SELECT_DIR}"

selection="${TEMPLATE_DIR}/selection.csv"

csvcut -c bin "${selection}" |
tail -n +2 |
sort -u |
while read -r bin; do

    build_image=$(
        csvgrep -c bin -m "${bin}" "${selection}" |
        csvgrep -c build -m True |
        csvcut -c dtitk_path |
        tail -n +2
    )

    mapfile -t select_images < <(
        csvgrep -c bin -m "${bin}" "${selection}" |
        csvgrep -c select -m True |
        csvcut -c fa_path |
        tail -n +2
    )

    if [[ -n "${build_image}" ]]; then
        cp "${build_image}" "${BUILD_DIR}/"

    elif [[ ${#select_images[@]} -ge 3 ]]; then
        bin_dir="${SELECT_DIR}/${bin}"
        mkdir -p "${bin_dir}"

        for select_image in "${select_images[@]}"; do
            new_basename="$(basename ${select_image} _FA.nii.gz).nii.gz"
            cp "${select_image}" "${bin_dir}/${new_basename}"
        done

        jobscript_path="${JOBSCRIPT_DIR}/${script_stem}/${bin}.sh"
        
        cat <<-EOF > "${jobscript_path}"
		#!/usr/bin/env bash
		#BSUB -J ${script_stem}_${bin}
		#BSUB -o ${LOG_DIR}/${script_stem}/${bin}.o
		#BSUB -e ${LOG_DIR}/${script_stem}/${bin}.e

		module load fsl/6.0.3

		cd ${bin_dir}

		tbss_1_preproc *.nii.gz
		tbss_2_reg -n
		tbss_3_postreg -S
		EOF

        chmod 775 "${jobscript_path}"
        bsub < "${jobscript_path}"
    fi
done
