#!/usr/bin/env bash

DATA_DIR="/project/ExtraLong/derivatives/freesurfer"
JOBSCRIPT_DIR="/project/ExtraLong/code/jobscripts/freesurfer"
LOG_DIR="/project/ExtraLong/code/logs/freesurfer"
FREESURFER_HOME="/appl/freesurfer-8.2.0"
LICENSE="/project/ExtraLong/code/freesurfer/license.txt"

mkdir -p "${JOBSCRIPT_DIR}" "${LOG_DIR}" "${DATA_DIR}/tables"

jobscript_path="${JOBSCRIPT_DIR}/04_euler_number.sh"

cat <<-EOF > "${jobscript_path}"
#!/usr/bin/env bash
#BSUB -J 04_euler_number
#BSUB -o ${LOG_DIR}/04_euler_number.o
#BSUB -e ${LOG_DIR}/04_euler_number.e

get_euler () {
    mris_euler_number "\$1" |
        awk '/euler #/ {
            sub(/.*= /, "")
            sub(/ -->.*/, "")
            print
        }'
}

mkdir -p ${DATA_DIR}/tables

module load freesurfer/8.2.0

export FREESURFER_HOME="${FREESURFER_HOME}"
source "${FREESURFER_HOME}/SetUpFreeSurfer.sh"
export SURFER_FRONTDOOR=1
export FS_LICENSE="${LICENSE}"
export SUBJECTS_DIR="${DATA_DIR}"

{
    echo "sub,ses,hemi,euler"

    for sub_dir in ${DATA_DIR}/sub-*;
    do
        sub="\$(basename "\${sub_dir}")"

        for ses_dir in \${sub_dir}/ses-*;
        do
            ses="\$(basename "\${ses_dir}")"

            if [[ \${ses} =~ Template ]]; then
                continue 1
            fi

            for hemi in lh rh;
            do
                surf="\${ses_dir}/surf/\${hemi}.orig.nofix"

                if [ -f "\${surf}" ]; then
                    euler="\$(get_euler "\${surf}")"
                    echo "\${sub},\${ses},\${hemi},\${euler}"
                else
                    echo "\${sub},\${ses},\${hemi},"
                fi

            done
        done
    done

} > ${DATA_DIR}/tables/euler_number.csv

EOF

chmod 755 "${jobscript_path}"
bsub < "${jobscript_path}"
