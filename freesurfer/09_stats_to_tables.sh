#!/usr/bin/env bash

DATA_DIR="/project/ExtraLong/derivatives/freesurfer"
JOBSCRIPT_DIR="/project/ExtraLong/code/jobscripts/freesurfer"
LOG_DIR="/project/ExtraLong/code/logs/freesurfer"
CONTAINER="/appl/containers/freesurfer_8.2.0.sif"
LICENSE="/project/ExtraLong/code/freesurfer/license.txt"

mkdir -p "${JOBSCRIPT_DIR}" "${LOG_DIR}" "${DATA_DIR}/tables"

jobscript_path="${JOBSCRIPT_DIR}/09_stats_to_tables.sh"

cat <<-EOF > "${jobscript_path}"
#!/usr/bin/env bash
#BSUB -o ${LOG_DIR}/09_stats_to_tables.o
#BSUB -e ${LOG_DIR}/09_stats_to_tables.e
#BSUB -J 09_stats_to_tables

module load apptainer

apptainer exec --cleanenv \\
    --bind "${DATA_DIR}:/data_dir" \\
    --bind "${LICENSE}:/license.txt:ro" \\
    "${CONTAINER}" \\
    bash -c '
        export SURFER_FRONTDOOR=1
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

        ConcatenateSubregionsResults.sh \\
            -f amygdalar-nuclei.lh.T1.v21.stats \\
            -f amygdalar-nuclei.rh.T1.v21.stats \\
            -f hipposubfields.lh.T1.v21.stats \\
            -f hipposubfields.rh.T1.v21.stats \\
            -o /data_dir/tables/
    '
EOF

chmod 755 "${jobscript_path}"
bsub < "${jobscript_path}"
