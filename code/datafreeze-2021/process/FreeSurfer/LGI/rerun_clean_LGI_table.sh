#!/bin/bash
module load R
freeqc_dir=/project/ExtraLong/data/datafreeze-2021/FreeQC/Longitudinal
FailedCSV=/home/hillmann/Projects/ExtraLong/Data/FailedLGI.csv
subjList=`cat ${FailedCSV} | cut -d , -f 2 | grep -v 'bblid' | uniq`

for subj in ${subjList}; do
    sessList=`cat ${FailedCSV} | grep ${subj} | cut -d , -f 3`
    if [ ${#subj} -eq 5 ]; then
        subj=0${subj}
    fi
    for sess in ${sessList}; do
        if [ ${#sess} -eq 4 ]; then
        sess=0${sess}
        fi
        Rscript ~/Projects/ExtraLong/Scripts/Clean_LGI_table.R ${freeqc_dir}/sub-${subj}/ses-${sess}/sub-${subj}_ses-${sess}_lh.aparc.pial_lgi_table.txt ${freeqc_dir}/sub-${subj}/ses-${sess}/sub-${subj}_ses-${sess}_lh.aparc.pial_lgi_clean.csv
        Rscript ~/Projects/ExtraLong/Scripts/Clean_LGI_table.R ${freeqc_dir}/sub-${subj}/ses-${sess}/sub-${subj}_ses-${sess}_rh.aparc.pial_lgi_table.txt ${freeqc_dir}/sub-${subj}/ses-${sess}/sub-${subj}_ses-${sess}_rh.aparc.pial_lgi_clean.csv
    done
done
