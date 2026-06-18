#!/bin/bash

export LOGS_DIR=/home/hillmann/logs/ExtraLong_2021/ANTs/ANTsSST-0.1.2
mkdir -p ${LOGS_DIR}

scripts="/project/ExtraLong/scripts/datafreeze-2021/process/ANTsLongitudinal"
jsDir=${scripts}/jobscripts/ANTsSST-0.1.2
mkdir -p ${jsDir}

data="/project/ExtraLong/data/datafreeze-2021"
fmriprep_dir=${data}/fmriprep
antslong_dir=${data}/ANTsLongitudinal
atlas_dir="/project/ExtraLong/data/mindboggleVsBrainCOLOR_Atlases"
include_csv=${data}/QC/sessions_for_inclusion.csv
#subList=$(cat ${include_csv} | cut -d , -f 1 | sed "s/subid//" | uniq)
subList='088760 130896' 

echo "ANTsSST will be run on $(echo $subList | wc -w) subjects"


for subject in $subList; do

	sessions=$(cat ${include_csv} | grep ${subject} | cut -d , -f 2 | sed "s/^/ses-/" | tr "\n" " ")
	subject=sub-${subject}
	echo SUBJECT: $subject
	echo SESSIONS: $sessions

	out_dir=${antslong_dir}/subjects/${subject}
	mkdir -p ${out_dir}

	jobscript=${jsDir}/${subject}.sh

	cat <<-JOBSCRIPT >${jobscript}
		#!/bin/bash

		singularity run --writable-tmpfs --cleanenv  \\
			-B ${fmriprep_dir}/${subject}:/data/input/fmriprep \\
			-B ${out_dir}:/data/output \\
			-B ${atlas_dir}:/data/input/atlases \\
			/project/ExtraLong/images/antssst_0.1.2.sif --use-deep --seed 1 ${sessions}

	JOBSCRIPT

	chmod +x ${jobscript}
	bsub -e $LOGS_DIR/${subject}.e -o $LOGS_DIR/${subject}.o ${jobscript}
done

