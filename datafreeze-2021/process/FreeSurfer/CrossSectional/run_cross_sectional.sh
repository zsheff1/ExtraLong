#!/bin/bash

export FREESURFER_HOME=/appl/freesurfer-7.1.1
export LOGS_DIR=/home/kzoner/logs/ExtraLong_2021/FreeSurfer-7.1.1
mkdir -p $LOGS_DIR

project=/project/ExtraLong
input_dir=${project}/data/datafreeze-2021/bids_directory
output_dir=${project}/data/datafreeze-2021/FreeSurfer
js_dir=${project}/scripts/datafreeze-2021/process/FreeSurfer/jobscripts/cross_sectional

mkdir -p $js_dir

imgList=`ls $input_dir/*/*/anat/*.nii.gz`

for img in $imgList; do
	
	subj=`basename $img | cut -d _ -f 1`
	sess=`basename $img | cut -d _ -f 2`
	echo SUBJECT: $subj SESSION: $sess
	
	subj_dir=$output_dir/$subj
	mkdir -p $subj_dir

	jobscript=${js_dir}/${subj}_${sess}.sh
	
	cat <<- EOS > ${jobscript}
		#!/bin/bash
		
		module load freesurfer/7.1.1
		export FREESURFER_HOME=/appl/freesurfer-7.1.1
		source ${FREESURFER_HOME}/SetUpFreeSurfer.sh
	
		SURFER_FRONTDOOR=1 ${FREESURFER_HOME}/bin/recon-all \\
			-i $img \\
			-sd $subj_dir \\
			-s $sess -all
	EOS

	chmod +x ${jobscript}
	bsub -e $LOGS_DIR/${subj}_${sess}.e -o $LOGS_DIR/${subj}_${sess}.o ${jobscript}
done
