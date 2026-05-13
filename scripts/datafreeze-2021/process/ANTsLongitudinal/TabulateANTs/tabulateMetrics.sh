#!/bin/bash

ANTs_dir=/project/ExtraLong/data/datafreeze-2021/ANTsLongitudinal
output_dir=/project/ExtraLong/data/datafreeze-2021/TabulatedQC/ANTs

CT=$(find ${ANTs_dir}/subjects -newer timestamp -name '*_CorticalThickness.csv')
Vol=$(find ${ANTs_dir}/subjects -newer timestamp  -name '*_Volume.csv')
GMD=$(find ${ANTs_dir}/subjects -newer timestamp  -name '*_GMD.csv')

awk '(NR == 1) || (FNR > 1)' $CT > /project/ExtraLong/data/datafreeze-2021/TabulatedQC/ANTs/CorticalThickness_DKT_$(date +"%m_%d_%Y").csv
awk '(NR == 1) || (FNR > 1)' $Vol > /project/ExtraLong/data/datafreeze-2021/TabulatedQC/ANTs/Volume_DKT_$(date +"%m_%d_%Y").csv
awk '(NR == 1) || (FNR > 1)' $GMD > /project/ExtraLong/data/datafreeze-2021/TabulatedQC/ANTs/GMD_DKT_$(date +"%m_%d_%Y").csv


