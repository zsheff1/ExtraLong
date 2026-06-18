#!/bin/bash
LOGS_DIR=/home/hillmann/logs/ExtraLong/LGI
mkdir -p ${LOGS_DIR}

project=/project/ExtraLong
FailedCSV=/home/hillmann/Projects/ExtraLong/Data/FailedLGI.csv
output_dir=${project}/data/datafreeze-2021/FreeSurfer
mkdir -p ${project}/scripts/jobscripts/datafreeze-2021/LGI

subjList=`cat ${FailedCSV} | cut -d , -f 2 | grep -v 'bblid' | uniq`

for subj in $subjList; do

    sessList=`cat ${FailedCSV} | grep ${subj} | cut -d , -f 3`
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

	jobscript=${project}/scripts/jobscripts/datafreeze-2021/LGI/sub-${subj}_ses-${sess}.sh

        cat <<- EOS > ${jobscript}
            #!/bin/bash
            export FREESURFER_HOME=/home/hillmann/software/freesurfer-7.1.0
            source /home/hillmann/software/freesurfer-7.1.0/SetUpFreeSurfer.sh
            export SUBJECTS_DIR=${output_dir}/sub-${subj}
            module load matlab/2020b
            SURFER_FRONTDOOR=1 /home/hillmann/software/freesurfer-7.1.0/bin/recon-all -s ses-${sess} -localGI -no-isrunning
EOS

   	chmod +x ${jobscript}
        bsub -q matlab_normal -e $LOGS_DIR/sub-${subj}_ses-${sess}.e -o $LOGS_DIR/sub-${subj}_ses-${sess}.o < ${jobscript}

        done
done
