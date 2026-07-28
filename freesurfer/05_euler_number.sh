#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
code_root=$(cd -- "${script_dir}/.." && pwd)

source "${code_root}/config/project.env"
source "${code_root}/config/freesurfer.sh"

script_name=$(basename "${BASH_SOURCE[0]}")
script_stem="${script_name%.sh}"

mkdir -p "${JOBSCRIPT_DIR}" "${LOG_DIR}" "${FREESURFER_DATA_DIR}/tables"

jobscript_path="${JOBSCRIPT_DIR}/${script_stem}.sh"

cat <<-EOF > "${jobscript_path}"
#!/usr/bin/env bash
#BSUB -J ${script_stem}
#BSUB -o ${LOG_DIR}/${script_stem}.o
#BSUB -e ${LOG_DIR}/${script_stem}.e

module load apptainer

apptainer exec --containall \\
    --bind "${FREESURFER_DATA_DIR}:/data_dir" \\
    --bind "${LICENSE}:/license.txt" \\
    "${CONTAINER}" \\
    bash <<'INNER_EOF'

export FS_LICENSE=/license.txt
export SUBJECTS_DIR=/data_dir

get_euler () {
    mris_euler_number "\$1" |
        awk '/euler #/ {
            sub(/.*= /, "")
            sub(/ -->.*/, "")
            print
        }'
}

{
    echo "sub,ses,hemi,euler"

    for sub_ses_dir in /data_dir/sub-*_ses-*; do
        [[ -d "\${sub_ses_dir}" ]] || continue
        [[ \${sub_ses_dir} =~ .*/(sub-[0-9]{6})_(ses-[0-9]{5})$ ]] || continue
        
        sub="\${BASH_REMATCH[1]}"
        ses="\${BASH_REMATCH[2]}"

        for hemi in lh rh; do
            surf="\${sub_ses_dir}/surf/\${hemi}.orig.nofix"

            [[ -f "\${surf}" ]] || continue

            euler="\$(get_euler "\${surf}")"

            echo "\${sub},\${ses},\${hemi},\${euler}"
        done
    done

} > /data_dir/tables/euler_number.csv

INNER_EOF
EOF

chmod 755 "${jobscript_path}"
bsub < "${jobscript_path}"
