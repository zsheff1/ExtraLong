#!/bin/bash

export FREESURFER_HOME=/appl/freesurfer-7.1.1
export LOGS_DIR=/home/kzoner/logs/fs-test
mkdir -p $LOGS_DIR

project=/project/ExtraLong
input_dir=${project}/data/datafreeze-2021/bids_directory
output_dir=~/fs-test
js_dir=${project}/scripts/process/datafreeze-2021/FreeSurfer/jobscripts/fs-test

mkdir -p $js_dir

imgList=`ls $input_dir/*/*/anat/*.nii.gz`

subj=sub-139490
sess=ses-08461
img=`find ${input_dir}/${subj}/${sess}/anat/ -name "*.nii.gz"`
echo $img

for iter in {1..4}; do
	
	echo SUBJECT: $subj SESSION: $sess ITER: $iter
	
	subj_dir=$output_dir/run-$iter
	mkdir -p $subj_dir

	jobscript=${js_dir}/test_${iter}.sh
	
	cat <<- EOS > ${jobscript}
		#!/bin/bash
		
		module load freesurfer/7.1.1
		export FREESURFER_HOME=/appl/freesurfer-7.1.1
		source ${FREESURFER_HOME}/SetUpFreeSurfer.sh
	
		SURFER_FRONTDOOR=1 ${FREESURFER_HOME}/bin/recon-all \\
			-i $img \\
			-sd $subj_dir \\
			-s $sess -all -norandomness
	EOS

	chmod +x ${jobscript}
	bsub -e $LOGS_DIR/test_${iter}.e -o $LOGS_DIR/test_${iter}.o ${jobscript}
done
