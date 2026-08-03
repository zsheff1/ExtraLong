#!/usr/bin/env python3

import os
import glob
import pandas as pd
import nibabel as nib
import re

DWI_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi'
STATS_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi/stats'
INPUT_TSNR_PATH = '/project/bbl_gur_evolpsy/derivatives/qc/qc.tsv'
INPUT_ENIGMA_PATH = '/project/bbl_gur_evolpsy/derivatives/dwi/stats/Proj_Dist.txt'
OUTPUT_PATH = '/project/bbl_gur_evolpsy/derivatives/dwi/stats/dwi_qc.csv'

SUB_SES_PATTERN = re.compile(r'sub-\d{6}_ses-\w{3,4}1')

# qc tsnr
qc_tsnr_b0 = pd.read_csv(INPUT_TSNR_PATH, sep = '\t')
qc_tsnr_b0['sub_ses'] = qc_tsnr_b0['sub'] + '_' + qc_tsnr_b0['ses']
qc_tsnr_b0.rename(columns={'dwi_tsnr_b0': 'tsnr_b0'}, inplace=True)
qc_tsnr_b0 = qc_tsnr_b0[['sub_ses', 'tsnr_b0']]

# qc volumes
qc_volumes = pd.DataFrame(
    [
        (SUB_SES_PATTERN.search(image).group(0) , nib.load(image).shape[3])
        for image in glob.glob(os.path.join(DWI_DIR, 'sub-*', 'ses-*', 'dwi', 'sub-*_ses-*_space-ACPC_desc-preproc_dwi.nii.gz'))
    ],
    columns = ['sub_ses', 'volumes']
)

# qc enigma
with open(INPUT_ENIGMA_PATH) as file:
    _ = next(file)
    qc_enigma = [tuple(line.strip().replace('  ', ' ').split(' ')) for line in file]

qc_enigma = pd.DataFrame(qc_enigma, columns = ['sub_ses', 'mean_projection_distance', 'max_projection_distance'])
qc_enigma = qc_enigma[['sub_ses', 'mean_projection_distance']]

# qc merged
qc = pd.merge(pd.merge(qc_volumes, qc_tsnr_b0, on='sub_ses', how='left'), qc_enigma, on='sub_ses', how='left')
qc.to_csv(OUTPUT_PATH, index = False)