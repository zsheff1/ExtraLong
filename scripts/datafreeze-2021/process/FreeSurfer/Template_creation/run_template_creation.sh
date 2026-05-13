#!/bin/bash

export FREESURFER_HOME=/appl/freesurfer-7.1.1
export LOGS_DIR=/home/hillmann/logs/ExtraLong/fs-base


project=/project/ExtraLong
output_dir=${project}/data/datafreeze-2021/FreeSurfer
subjCSV=${project}/data/datafreeze-2021/QC/demographics+exclusion_datafreeze-2021_euler-212_minspan-180.csv
mkdir -p ${project}/scripts/jobscripts/datafreeze-2021/fs-base

subjList=`cat ${subjCSV} | cut -d , -f 1 | grep -v 'subid' | uniq`

for subject in $subjList; do
	if [ ${#subject} -eq 5 ]; then
		sessList=`cat ${subjCSV} | grep ^${subject} | cut -d , -f 2`
		subject=0${subject}
	else 
                sessList=`cat ${subjCSV} | grep ^${subject} | cut -d , -f 2`
	fi
	    
    	tpArgs=""
    	for session in $sessList; do 
		if [ ${#session} -eq 4 ]; then
			session=0${session}
		fi
        	tpArgs="${tpArgs} -tp ses-${session}"; 
    	done

    	jobscript=${project}/scripts/jobscripts/datafreeze-2021/fs-base/sub-${subject}.sh
	
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
