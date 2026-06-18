#!/bin/bash

export LOGS_DIR=~/logs/ExtraLong_2021/FreeQC
mkdir -p $LOGS_DIR

project=/project/ExtraLong
bids_dir=${project}/data/datafreeze-2021/bids_directory
fs_dir=${project}/data/datafreeze-2021/FreeSurfer
freeqc_dir=${project}/data/datafreeze-2021/FreeQC
mkdir -p $freeqc_dir

js_dir=${project}/scripts/datafreeze-2021/process/FreeQC/jobscripts
mkdir -p $js_dir

imgList=`ls $bids_dir/*/*/anat/*.nii.gz`

for img in $imgList; do
	
	subject=`basename $img | cut -d _ -f 1`
	session=`basename $img | cut -d _ -f 2`
	echo SUBJECT: $subject SESSION: $session

	input="${fs_dir}/${subject}/${session}"
	output="${freeqc_dir}/${subject}/${session}"
	mkdir -p ${output}

	jobscript=${js_dir}/${subject}_${session}.sh
	
	cat <<- EOS > ${jobscript}
		#!/bin/bash
		
		SINGULARITYENV_SURFER_FRONTDOOR=1 \\
		singularity run --writable-tmpfs --cleanenv --containall \\
		-B ${input}:/input/data \\
		-B ${project}/data/license.txt:/opt/freesurfer/license.txt \\
		-B ${output}:/output \\
		${project}/images/freeqc_0.0.14.sif --subject ${subject} --session ${session}
	EOS
	
	chmod +x ${jobscript}
	bsub -e $LOGS_DIR/${subject}_${session}.e -o $LOGS_DIR/${subject}_${session}.o  ${jobscript}
done


