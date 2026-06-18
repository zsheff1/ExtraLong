#!/bin/bash

export FREESURFER_HOME=/appl/freesurfer-7.1.1
export LOGS_DIR=/home/hillmann/logs/ExtraLong_2021/fs-long

project=/project/ExtraLong
subjCSV=${project}/data/datafreeze-2021/QC/demographics+exclusion_datafreeze-2021_euler-212_minspan-180.csv
output_dir=${project}/data/datafreeze-2021/FreeSurfer
mkdir -p ${project}/scripts/jobscripts/datafreeze-2021/fs-long

#subjList=`cat ${subjCSV} | cut -d , -f 1 | grep -v 'subid' | uniq`

#for subj in $subjList; do
subj='11801'
sessList=`cat ${subjCSV} | grep ${subj} | cut -d , -f 2`
if [ ${#subj} -eq 5 ]; then
    subj=0${subj}
fi

for sess in $sessList; do

    if [ ${#sess} -eq 4 ]; then
        sess=0${sess}
    fi
    echo SUBJECT: sub-${subj} SESSION: ses-${sess}

     # Skip session if does not exist in subject's FS output dir
    if [ ! -d "${output_dir}/sub-${subj}/ses-${sess}" ]; then
        echo Session ${sess} does not exist!
        break
    fi

    jobscript=${project}/scripts/jobscripts/datafreeze-2021/fs-long/sub-${subj}_ses-${sess}.sh

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
#done
