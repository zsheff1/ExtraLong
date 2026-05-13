#!/bin/bash
module load R
freeqc_dir=/project/ExtraLong/data/datafreeze-2021/FreeQC/Longitudinal
subjList=`ls ${freeqc_dir}`

for subj in ${subjList}; do
    sessList=`ls ${freeqc_dir}/${subj}`

    for sess in ${sessList}; do
        Rscript ~/Projects/ExtraLong/Scripts/Clean_LGI_table.R ${freeqc_dir}/${subj}/${sess}/${subj}_${sess}_lh.aparc.pial_lgi_table.txt ${freeqc_dir}/${subj}/${sess}/${subj}_${sess}_lh.aparc.pial_lgi_clean.csv
        Rscript ~/Projects/ExtraLong/Scripts/Clean_LGI_table.R ${freeqc_dir}/${subj}/${sess}/${subj}_${sess}_rh.aparc.pial_lgi_table.txt ${freeqc_dir}/${subj}/${sess}/${subj}_${sess}_rh.aparc.pial_lgi_clean.csv
    done
done
