#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
code_root=$(cd -- "${script_dir}/.." && pwd)

source "${code_root}/config/project.env"
source "${code_root}/config/freesurfer.sh"

find "${FREESURFER_DATA_DIR}" -mindepth 1 -maxdepth 1 -type d -name "sub-*_ses-*" -printf '%f\n' |
while read -r sub_ses; do

    sub="${sub_ses%%_ses-*}"

    if [[ "${sub_ses}" =~ ^sub-[0-9]{6}_ses-[0-9]{5}\.long\.sub-[0-9]{6}$ ]] \
       || [[ ! -d "${FREESURFER_DATA_DIR}/${sub}" ]]; then
        echo "${sub_ses}"
    fi

done | sort > "${SUBJECTSFILE}"
