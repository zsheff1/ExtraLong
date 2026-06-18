#!/bin/bash

project=/project/ExtraLong

export LOGS_DIR=/home/kzoner/logs/ExtraLong/freeqc-base
mkdir -p ${LOGS_DIR}

jsDir=${project}/scripts/jobscripts/freeqc-base
mkdir -p ${jsDir}

subList=`ls ${project}/data/freesurferLongitudinal`

for subject in $subList; do
	
	#echo SUBJECT: $subject

	subId=`echo $subject | cut -d - -f 2`
	fsDir=${project}/data/freesurferLongitudinal/${subject}/Template-${subId}

	# Skip if subj doesn't have Template-* dir	
	if [ ! -d ${fsDir} ]; then
		echo Skipping ${subject}. No Template-* dir.
		continue
	fi
	
	outDir=${project}/data/freeqcLongitudinal/${subject}/Template
	mkdir -p ${outDir}

	jobscript=${jsDir}/${subject}.sh
	
	cat <<- EOS > ${jobscript}
		#!/bin/bash

		SINGULARITYENV_SURFER_FRONTDOOR=1 \\
		singularity run --writable-tmpfs --cleanenv \\
		-B ${fsDir}:/input/data \\
		-B ${project}/data/license.txt:/opt/freesurfer/license.txt \\
		-B ${outDir}:/output \\
		${project}/images/freeqc_0.0.14.sif --subject ${subject} --session ses-Template
	EOS

	chmod +x ${jobscript}
		
	bsub -e $LOGS_DIR/${subject}.e -o $LOGS_DIR/${subject}.o ${jobscript}

done


