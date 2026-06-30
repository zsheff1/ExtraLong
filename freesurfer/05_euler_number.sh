#!/usr/bin/env bash

DATA_DIR="/project/ExtraLong/derivatives/freesurfer"
JOBSCRIPT_DIR="/project/ExtraLong/code/jobscripts/freesurfer"
LOG_DIR="/project/ExtraLong/code/logs/freesurfer"
CONTAINER="/appl/containers/freesurfer_8.2.0.sif"
LICENSE="/project/ExtraLong/code/freesurfer/license.txt"

mkdir -p "${JOBSCRIPT_DIR}" "${LOG_DIR}" "${DATA_DIR}/tables"

jobscript_path="${JOBSCRIPT_DIR}/05_euler_number.sh"

cat <<-EOF > "${jobscript_path}"
#!/usr/bin/env bash
#BSUB -J 05_euler_number
#BSUB -o ${LOG_DIR}/05_euler_number.o
#BSUB -e ${LOG_DIR}/05_euler_number.e

module load apptainer

apptainer exec --containall \\
    --bind "${DATA_DIR}:/data_dir" \\
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
