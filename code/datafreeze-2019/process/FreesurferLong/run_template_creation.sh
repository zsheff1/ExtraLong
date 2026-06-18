#!/bin/bash

export FREESURFER_HOME=/appl/freesurfer-7.1.1
export LOGS_DIR=/home/kzoner/logs/ExtraLong/fs-base

project=/project/ExtraLong
exclude_csv=${project}/data/qualityAssessment/antssstExclude.csv
output_dir=${project}/data/freesurferLongitudinal

mkdir -p ${project}/scripts/jobscripts/fs-base

subjList=`cat ${exclude_csv} | grep FALSE | cut -d , -f 1 | uniq`

for subject in $subjList; do
	sessList=`cat ${exclude_csv} | grep ${subject} | grep FALSE | cut -d , -f 2 | cut -d \" -f 2`
    
    	tpArgs=""
    	for session in $sessList; do 
        	tpArgs="${tpArgs} -tp ses-${session}"; 
    	done

    	jobscript=${project}/scripts/jobscripts/fs-base/sub-${subject}.sh
	
	cat <<- EOS > ${jobscript}
		#!/bin/bash
		
		module load freesurfer/7.1.1
		export FREESURFER_HOME=/appl/freesurfer-7.1.1
		source ${FREESURFER_HOME}/SetUpFreeSurfer.sh
		export SUBJECTS_DIR=${output_dir}/sub-${subject}
		SURFER_FRONTDOOR=1 ${FREESURFER_HOME}/bin/recon-all -base Template-${subject} ${tpArgs} -all
	EOS
	
	chmod +x ${jobscript}
	bsub -e $LOGS_DIR/sub-${subject}.e -o $LOGS_DIR/sub-${subject}.o ${jobscript}
done
