#!/bin/bash
export FREESURFER_HOME=/appl/freesurfer-7.1.0
source $FREESURFER_HOME/SetUpFreeSurfer.sh
export LOGS_DIR=~/logs/ExtraLong/LGI_TabulateStats
mkdir -p $LOGS_DIR

project=/project/ExtraLong
bids_dir=${project}/data/datafreeze-2021/bids_directory
fs_dir=${project}/data/datafreeze-2021/FreeSurfer
freeqc_dir=${project}/data/datafreeze-2021/FreeQC/Longitudinal
mkdir -p $freeqc_dir

js_dir=${project}/scripts/jobscripts/datafreeze-2021/TabulateStats_LGI
mkdir -p $js_dir

imgList=`ls $bids_dir/*/*/anat/*.nii.gz`

for img in $imgList; do

        subject=`basename $img | cut -d _ -f 1`
        subjID=`basename $img | cut -d _ -f 1 | cut -d - -f 2`
        session=`basename $img | cut -d _ -f 2`
        echo SUBJECT: $subject SESSION: $session
        
        input="${fs_dir}/${subject}/${session}"
        output="${freeqc_dir}/${subject}/${session}"
        mkdir -p ${output}

        jobscript=${js_dir}/${subject}_${session}.sh

        cat <<- EOS > ${jobscript}
            #!/bin/bash
            export FREESURFER_HOME=/appl/freesurfer-7.1.0
            source /appl/freesurfer-7.1.0/SetUpFreeSurfer.sh
            export SUBJECTS_DIR=${input}
            SURFER_FRONTDOOR=1 mri_segstats --annot . lh aparc --i ${input}/surf/lh.pial_lgi --sum ${output}/${subject}_${session}_lh.aparc.pial_lgi.stats
            SURFER_FRONTDOOR=1 mri_segstats --annot . rh aparc --i ${input}/surf/rh.pial_lgi --sum ${output}/${subject}_${session}_rh.aparc.pial_lgi.stats
            tail -n 36 ${output}/${subject}_${session}_lh.aparc.pial_lgi.stats > ${output}/${subject}_${session}_lh.aparc.pial_lgi_table.txt
            tail -n 36 ${output}/${subject}_${session}_rh.aparc.pial_lgi.stats > ${output}/${subject}_${session}_rh.aparc.pial_lgi_table.txt
EOS

        chmod +x ${jobscript}
        bsub -e $LOGS_DIR/${subject}_${session}.e -o $LOGS_DIR/${subject}_${session}.o  ${jobscript}
        
done
