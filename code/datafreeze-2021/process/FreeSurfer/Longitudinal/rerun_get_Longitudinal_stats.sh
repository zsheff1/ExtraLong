#!/bin/bash
export FREESURFER_HOME=/appl/freesurfer-6.0.0
source $FREESURFER_HOME/SetUpFreeSurfer.sh
export LOGS_DIR=~/logs/ExtraLong_2021/Longitudinal/TabulateStats
mkdir -p $LOGS_DIR

project=/project/ExtraLong
bids_dir=${project}/data/datafreeze-2021/bids_directory
fs_dir=${project}/data/datafreeze-2021/FreeSurfer
freeqc_dir=${project}/data/datafreeze-2021/FreeQC/Longitudinal
mkdir -p $freeqc_dir

js_dir=${project}/scripts/jobscripts/datafreeze-2021/TabulateStats-longitudinal
mkdir -p $js_dir

imgList=`ls $bids_dir/*/*/anat/*.nii.gz`

for img in $imgList; do
	
	subject=`basename $img | cut -d _ -f 1`
	subjID=`basename $img | cut -d _ -f 1 | cut -d - -f 2`
	session=`basename $img | cut -d _ -f 2`
	echo SUBJECT: $subject SESSION: $session
	echo SUBJECT: $subject SESSION: $session

    if [ ${subjID} == "011801" ]; then

	    input="${fs_dir}/${subject}/${session}.long.Template-${subjID}"
	    output="${freeqc_dir}/${subject}/${session}"
	    mkdir -p ${output}

	    jobscript=${js_dir}/${subject}_${session}.sh
	
	    cat <<- EOS > ${jobscript}
		    #!/bin/bash
		    export FREESURFER_HOME=/appl/freesurfer-6.0.0
		    source $FREESURFER_HOME/SetUpFreeSurfer.sh
		    export SUBJECTS_DIR=${input}
		    python2 ${FREESURFER_HOME}/bin/asegstats2table --subjects . --delimiter comma --meas volume --skip --statsfile wmparc.stats --all-segs --tablefile ${output}/${subject}_${session}_wmparc_stats.csv
		    python2 ${FREESURFER_HOME}/bin/asegstats2table --subjects . --delimiter comma --meas volume --skip --tablefile ${output}/${subject}_${session}_aseg_stats.csv
		    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi lh --meas volume --skip --tablefile ${output}/${subject}_${session}_aparc_volume_lh.csv
		    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi lh --meas thickness --skip --tablefile ${output}/${subject}_${session}_aparc_thickness_lh.csv
		    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi lh --meas area --skip --tablefile ${output}/${subject}_${session}_aparc_area_lh.csv
		    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi lh --meas meancurv --skip --tablefile ${output}/${subject}_${session}_aparc_meancurv_lh.csv
		    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi rh --meas volume --skip --tablefile ${output}/${subject}_${session}_aparc_volume_rh.csv
		    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi rh --meas thickness --skip --tablefile ${output}/${subject}_${session}_aparc_thickness_rh.csv
		    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi rh --meas area --skip --tablefile ${output}/${subject}_${session}_aparc_area_rh.csv
		    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi rh --meas meancurv --skip --tablefile ${output}/${subject}_${session}_aparc_meancurv_rh.csv
		    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi lh --parc aparc.a2009s --meas volume --skip -t ${output}/${subject}_${session}_lh_a2009s_volume.csv
		    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi lh --parc aparc.a2009s --meas thickness --skip -t ${output}/${subject}_${session}_lh_a2009s_thickness.csv
		    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi lh --parc aparc.a2009s --meas area --skip -t ${output}/${subject}_${session}_lh_a2009s_area.csv
		    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi lh --parc aparc.a2009s --meas meancurv --skip -t ${output}/${subject}_${session}_lh_a2009s_meancurv.csv
		    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi rh --parc aparc.a2009s --meas volume --skip -t ${output}/${subject}_${session}_rh_a2009s_volume.csv
		    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi rh --parc aparc.a2009s --meas thickness --skip -t ${output}/${subject}_${session}_rh_a2009s_thickness.csv
		    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi rh --parc aparc.a2009s --meas area --skip -t ${output}/${subject}_${session}_rh_a2009s_area.csv
		    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi rh --parc aparc.a2009s --meas meancurv --skip -t ${output}/${subject}_${session}_rh_a2009s_meancurv.csv
    		    # DKT Atlas
            	    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi lh --parc aparc.DKTatlas --meas volume --skip -t ${output}/${subject}_${session}_lh_DKTatlas_volume.csv
            	    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi lh --parc aparc.DKTatlas --meas thickness --skip -t ${output}/${subject}_${session}_lh_DKTatlas_thickness.csv
            	    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi lh --parc aparc.DKTatlas --meas area --skip -t ${output}/${subject}_${session}_lh_DKTatlas_area.csv
            	    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi lh --parc aparc.DKTatlas --meas meancurv --skip -t ${output}/${subject}_${session}_lh_DKTatlas_meancurv.csv
            	    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi rh --parc aparc.DKTatlas --meas volume --skip -t ${output}/${subject}_${session}_rh_DKTatlas_volume.csv
            	    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi rh --parc aparc.DKTatlas --meas thickness --skip -t ${output}/${subject}_${session}_rh_DKTatlas_thickness.csv
            	    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi rh --parc aparc.DKTatlas --meas area --skip -t ${output}/${subject}_${session}_rh_DKTatlas_area.csv
            	    python2 ${FREESURFER_HOME}/bin/aparcstats2table --subjects . --delimiter comma --hemi rh --parc aparc.DKTatlas --meas meancurv --skip -t ${output}/${subject}_${session}_rh_DKTatlas_meancurv.csv
				
		    python /project/ExtraLong/scripts/datafreeze-2021/process/FreeSurfer/Extra/idcols.py 'bblid' ${output}/
EOS
	
	    chmod +x ${jobscript}
	    bsub -e $LOGS_DIR/${subject}_${session}.e -o $LOGS_DIR/${subject}_${session}.o  ${jobscript}
    fi
done
