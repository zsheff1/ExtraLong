#!/usr/bin/env bash

DATA_DIR="/project/ExtraLong/derivatives/freesurfer"
JOBSCRIPT_DIR="/project/ExtraLong/code/jobscripts/freesurfer"
LOG_DIR="/project/ExtraLong/code/logs/freesurfer"
CONTAINER="/appl/containers/freesurfer_8.2.0.sif"
LICENSE="/project/ExtraLong/code/freesurfer/license.txt"

mkdir -p "${JOBSCRIPT_DIR}" "${LOG_DIR}" "${DATA_DIR}/tables"

jobscript_path="${JOBSCRIPT_DIR}/07_stats_to_tables.sh"

cat <<-EOF > "${jobscript_path}"
	#!/usr/bin/env bash
	#BSUB -o ${LOG_DIR}/07_stats_to_tables.o
	#BSUB -e ${LOG_DIR}/07_stats_to_tables.e
	#BSUB -J 07_stats_to_tables

	module load apptainer

	apptainer exec --cleanenv \\
	    --bind "${DATA_DIR}:/data_dir" \\
	    --bind "${LICENSE}:/license.txt" \\
	    "${CONTAINER}" \\
	    bash -c '
	        export FS_LICENSE=/license.txt
	        export SURFER_FRONTDOOR=1
	        export SUBJECTS_DIR=/data_dir

	        aparcstats2table --subjects ${subjects} -d comma --hemi lh -m area --skip -t /data_dir/tables/aparc_area_left.csv
	        aparcstats2table --subjects ${subjects} -d comma --hemi rh -m area --skip -t /data_dir/tables/aparc_area_right.csv
	        aparcstats2table --subjects ${subjects} -d comma --hemi lh -m meancurv --skip -t /data_dir/tables/aparc_meancurv_left.csv
	        aparcstats2table --subjects ${subjects} -d comma --hemi rh -m meancurv --skip -t /data_dir/tables/aparc_meancurv_right.csv
	        aparcstats2table --subjects ${subjects} -d comma --hemi lh -m thickness --skip -t /data_dir/tables/aparc_thickness_left.csv
	        aparcstats2table --subjects ${subjects} -d comma --hemi rh -m thickness --skip -t /data_dir/tables/aparc_thickness_right.csv
	        aparcstats2table --subjects ${subjects} -d comma --hemi lh -m volume --skip -t /data_dir/tables/aparc_volume_left.csv
	        aparcstats2table --subjects ${subjects} -d comma --hemi rh -m volume --skip -t /data_dir/tables/aparc_volume_right.csv
	        asegstats2table --subjects ${subjects} -d comma -m volume --skip --statsfile aseg.stats --all-segs -t /data_dir/tables/aseg_volume.csv
	        asegstats2table --subjects ${subjects} -d comma -m volume --skip --statsfile wmparc.stats --all-segs -t /data_dir/tables/wmparc_volume.csv
	        asegstats2table --subjects ${subjects_cs} -d comma --statsfile amygdalar-nuclei.lh.T1.v21.stats -t /data_dir/tables/amygdala_volume_left.csv
	        asegstats2table --subjects ${subjects_cs} -d comma --statsfile amygdalar-nuclei.rh.T1.v21.stats -t /data_dir/tables/amygdala_volume_right.csv
	        asegstats2table --subjects ${subjects_cs} -d comma --statsfile hipposubfields.lh.T1.v21.stats -t /data_dir/tables/hippocampus_volume_left.csv
	        asegstats2table --subjects ${subjects_cs} -d comma --statsfile hipposubfields.rh.T1.v21.stats -t /data_dir/tables/hippocampus_volume_right.csv
	    '
EOF

chmod 755 "${jobscript_path}"
bsub < "${jobscript_path}"
