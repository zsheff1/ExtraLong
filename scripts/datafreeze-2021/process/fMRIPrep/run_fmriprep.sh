#!/bin/bash

export LOGS_DIR=/home/kzoner/logs/ExtraLong_2021/fMRIPrep-20.2.5
mkdir -p $LOGS_DIR

project=/project/ExtraLong
input_dir=${project}/data/datafreeze-2021/bids_directory
output_dir=${project}/data/datafreeze-2021/fmriprep
work_dir=${project}/data/datafreeze-2021/work
fs_dir=${project}/data/datafreeze-2021/FreeSurfer
js_dir=${project}/scripts/datafreeze-2021/process/fMRIPrep/jobscripts
templateflow=${project}/data/templateflow

SIF=${project}/images/fmriprep_20.2.5.sif

mkdir -p $js_dir

imgList=`ls $input_dir/*/*/anat/*.nii.gz`

for img in $imgList; do

        subj=`basename $img | cut -d _ -f 1`
        sess=`basename $img | cut -d _ -f 2`
        echo SUBJECT: $subj SESSION: $sess
	
	mkdir -p ${work_dir}/${subj}_${sess}

	# Make bids filter file for fMRIPrep 
	${PWD}/make_filter_file.sh ${subj} ${sess}
	filterfile=${PWD}/filterfiles/${sess}_filter.json

	jobscript=${js_dir}/${subj}_${sess}.sh	
	cat <<- EOS > ${jobscript}
		#!/bin/bash
		
		SINGULARITYENV_TEMPLATEFLOW_HOME=/templateflow \\
		SINGULARITYENV_SURFER_FRONTDOOR=1 \\
		singularity run --cleanenv \\
		-B ${input_dir}:/bids:ro \\
		-B ${output_dir}:/out \\
		-B ${fs_dir}/${subj}/${sess}:/freesurfer/${subj} \\
                -B /appl/freesurfer-7.1.1/subjects/fsaverage:/freesurfer/fsaverage:ro \\
		-B ${templateflow}:/templateflow \\
		-B ${filterfile}:/session_filter.json \\
		-B ${work_dir}/${subj}_${sess}:/work \\
		-B ${SINGULARITY_TMPDIR}:/tmp \\
		${SIF} \\
		/bids /out participant \\
		--participant-label ${subj} \\
		--bids-filter-file /session_filter.json \\
		--skull-strip-t1w force \\
		--stop-on-first-crash \\
		--skip-bids-validation \\
		--work-dir /work \\
		--fs-subjects-dir /freesurfer \\
		--anat-only \\
		--random-seed 1 \\
		--n_cpus 1
		
		EOS

	chmod +x ${jobscript}
	bsub -e ${LOGS_DIR}/${subj}_${sess}.e -o ${LOGS_DIR}/${subj}_${sess}.o ${jobscript}
done



