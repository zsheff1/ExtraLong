#!/bin/bash

export FREESURFER_HOME=/appl/freesurfer-7.1.1
export LOGS_DIR=/home/kzoner/logs/ExtraLong/fs-long

project=/project/ExtraLong
exclude_csv=${project}/data/qualityAssessment/antssstExclude.csv
output_dir=${project}/data/freesurferLongitudinal

mkdir -p ${project}/scripts/jobscripts/fs-long

subjList=`cat ${exclude_csv} | grep FALSE | cut -d , -f 1 | uniq`

for subj in $subjList; do
	
	sessList=`cat ${exclude_csv} | grep ${subj} | grep FALSE | cut -d , -f 2 | cut -d \" -f 2`
    
    	for sess in $sessList; do
		echo SUBJECT: sub-${subj} SESSION: ses-${sess}
	        
		# Skip session if does not exist in subject's FS output dir
		if [ ! -d "${output_dir}/sub-${subj}/ses-${sess}" ]; then
			echo Session ${sess} does not exist!
			break
		fi
	
	jobscript=${project}/scripts/jobscripts/fs-long/sub-${subj}_ses-${sess}.sh
	
	cat <<- EOS > ${jobscript}
		#!/bin/bash
		
		module load freesurfer/7.1.1
		export FREESURFER_HOME=/appl/freesurfer-7.1.1
		source ${FREESURFER_HOME}/SetUpFreeSurfer.sh
		export SUBJECTS_DIR=${output_dir}/sub-${subj}
		SURFER_FRONTDOOR=1 ${FREESURFER_HOME}/bin/recon-all -long ses-${sess} Template-${subj} -all
	EOS
	
	chmod +x ${jobscript}
	bsub -e $LOGS_DIR/sub-${subj}_ses-${sess}.e -o $LOGS_DIR/sub-${subj}_ses-${sess}.o ${jobscript}
	
	done
done
