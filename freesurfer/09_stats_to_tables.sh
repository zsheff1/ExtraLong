#!/usr/bin/env bash

set -euo pipefail

source "${code_root}/config/project.env"
source "${code_root}/config/freesurfer.sh"

script_name=$(basename "${BASH_SOURCE[0]}")
script_stem="${script_name%.sh}"

script_name=$(basename "${BASH_SOURCE[0]}")
script_stem="${script_name%.sh}"

mkdir -p "${JOBSCRIPT_DIR}/${script_stem}" "${LOG_DIR}/${script_stem}" "${FREESURFER_DATA_DIR}/tables"

jobscript_path="${JOBSCRIPT_DIR}/${script_stem}.sh"

cat <<-EOF > "${jobscript_path}"
#!/usr/bin/env bash
#BSUB -J ${script_stem}
#BSUB -o ${LOG_DIR}/${script_stem}.o
#BSUB -e ${LOG_DIR}/${script_stem}.e

module load apptainer

apptainer exec --containall \\
    --bind "${FREESURFER_DATA_DIR}:/data_dir" \\
    --bind "${LICENSE}:/license.txt:ro" \\
    --bind "${TABULATE_SUBREGIONS}:/tabulate_subregions.py" \\
    "${CONTAINER}" \\
    bash -c '
        export FS_LICENSE=/license.txt
        export SUBJECTS_DIR=/data_dir

        SUBJECTSFILE="/data_dir/subjectsfile.txt"

        for hemi in lh rh; do
            for meas in area meancurv thickness volume; do
                aparcstats2table \\
                    --subjectsfile "\${SUBJECTSFILE}" --skip \\
                    --hemi "\${hemi}" -m "\${meas}" \\
                    -t "/data_dir/tables/aparc_\${meas}_\${hemi}.tsv"
            done
            asegstats2table \\
                --subjectsfile "\${SUBJECTSFILE}" --skip \\
                -m mean --stats "\${hemi}.aparc.pial_lgi.stats" \\
                -t "/data_dir/tables/aseg_lgi_\${hemi}.tsv"
        done

        asegstats2table \\
            --subjectsfile "\${SUBJECTSFILE}" --skip \\
            -m volume --stats aseg.stats --all-segs \\
            -t /data_dir/tables/aseg_volume.tsv

        asegstats2table \\
            --subjectsfile "\${SUBJECTSFILE}" --skip \\
            -m volume --stats wmparc.stats --all-segs \\
            -t /data_dir/tables/wmparc_volume.tsv

        python3 /tabulate_subregions.py \\
            -f lh.amygNucVolumes.txt \\
            -f lh.hippoSfVolumes.txt \\
            -f rh.amygNucVolumes.txt \\
            -f rh.hippoSfVolumes.txt \\
            -o /data_dir/tables/
    '
EOF

chmod 755 "${jobscript_path}"
bsub < "${jobscript_path}"
