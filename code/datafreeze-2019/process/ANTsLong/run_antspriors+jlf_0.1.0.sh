#!/bin/bash

export LOGS_DIR=/home/kzoner/logs/ants/antspriors
mkdir -p ${LOGS_DIR}

jsDir=~/ants_pipelines/scripts/jobscripts/antspriors
mkdir -p ${jsDir}

fmriprep_dir=/project/ExtraLong/data/freesurferCrossSectional/fmriprep
antssst_dir=~/ants_pipelines/data/singleSubjectTemplates/antssst+jlf-0.1.0
atlas_dir=~/ants_pipelines/data/mindboggleVsBrainCOLOR_Atlases

out_dir=~/ants_pipelines/data/groupTemplates/antspriors-0.1.0
mkdir -p ${out_dir}

jobscript=${jsDir}/antspriors+jlf-0.1.0.sh

cat <<- JOBSCRIPT > ${jobscript}
	#!/bin/bash 
	singularity run --writable-tmpfs --cleanenv --containall \\
		-B ${fmriprep_dir}/sub-91404:/data/input/fmriprep/sub-91404 \\
		-B ${fmriprep_dir}/sub-85392:/data/input/fmriprep/sub-85392 \\
		-B ${fmriprep_dir}/sub-93811:/data/input/fmriprep/sub-93811 \\
		-B ${fmriprep_dir}/sub-100079:/data/input/fmriprep/sub-100079 \\
		-B ${fmriprep_dir}/sub-107903:/data/input/fmriprep/sub-107903 \\
		-B ${fmriprep_dir}/sub-108315:/data/input/fmriprep/sub-108315 \\
		-B ${fmriprep_dir}/sub-114990:/data/input/fmriprep/sub-114990 \\
		-B ${fmriprep_dir}/sub-116147:/data/input/fmriprep/sub-116147 \\
		-B ${antssst_dir}/sub-85392:/data/input/antssst/sub-85392 \\
		-B ${antssst_dir}/sub-91404:/data/input/antssst/sub-91404 \\
		-B ${antssst_dir}/sub-93811:/data/input/antssst/sub-93811 \\
		-B ${antssst_dir}/sub-100079:/data/input/antssst/sub-100079 \\
		-B ${antssst_dir}/sub-107903:/data/input/antssst/sub-107903 \\
		-B ${antssst_dir}/sub-108315:/data/input/antssst/sub-108315 \\
		-B ${antssst_dir}/sub-114990:/data/input/antssst/sub-114990 \\
		-B ${antssst_dir}/sub-116147:/data/input/antssst/sub-116147 \\
		-B ${atlas_dir}:/data/input/atlases \\
		-B ${out_dir}:/data/output \\
		~/ants_pipelines/images/antspriors_0.1.0.sif --project ExtraLong --seed 1 --jlf
JOBSCRIPT

chmod +x ${jobscript}
#bsub -e $LOGS_DIR/antspriors+jlf-0.1.0.e -o $LOGS_DIR/antspriors+jlf-0.1.0.o ${jobscript}

