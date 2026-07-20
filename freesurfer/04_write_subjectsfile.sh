#!/usr/bin/env bash

set -euo pipefail

config=${1:?Usage: $0 CONFIG}
source "$config"

find "${DATA_DIR}" -mindepth 1 -maxdepth 1 -type d -name "sub-*_ses-*" -printf '%f\n' |
while read -r sub_ses; do

    sub="${sub_ses%%_ses-*}"

    if [[ "${sub_ses}" =~ ^sub-[0-9]{6}_ses-[0-9]{5}\.long\.sub-[0-9]{6}$ ]] \
       || [[ ! -d "${DATA_DIR}/${sub}" ]]; then
        echo "${sub_ses}"
    fi

done | sort > "${SUBJECTSFILE}"
