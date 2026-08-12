#!/usr/bin/env python3

import os
import glob
import pandas as pd
import nibabel as nib
import re
import shutil
import logging
from pathlib import Path

RAW_DIR = '/project/bbl_gur_evolpsy'
DWI_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi'
SELECT_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi/template/select'
BUILD_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi/template/build'
LOG_DIR = '/project/bbl_gur_evolpsy/code/logs/dwi/template_select'
JOBSCRIPT_DIR = '/project/bbl_gur_evolpsy/code/jobscripts/dwi/template_select'

PARTICIPANTS_PATH = '/project/bbl_gur_evolpsy/participants.tsv'
QC_PATH = '/project/bbl_gur_evolpsy/derivatives/qc/qc.tsv'
SESSIONS_PATH = '/project/bbl_gur_evolpsy/sub-*/sub-*_sessions.tsv'

SUB_PATTERN = re.compile(r'sub-\d{6}')

os.makedirs(LOG_DIR, exist_ok = True)
os.makedirs(JOBSCRIPT_DIR, exist_ok = True)
os.makedirs(SELECT_DIR, exist_ok = True)
os.makedirs(BUILD_DIR, exist_ok = True)

logging.basicConfig(
    datefmt = '%Y-%m-%dT%H:%M:%S%z',
    filename = os.path.join(LOG_DIR, 'template_select.log'),
    format = '%(asctime)s %(levelname)s %(message)s',
    level = logging.DEBUG
)

# define functions
logging.info('define functions')

def check_fieldmap(row):
    sub = row['sub']
    ses = row['ses']
    fmap_dir = os.path.join(RAW_DIR, sub, ses, 'fmap')
    if ses == 'ses-PNC1':
        expected_files = [
            f"{sub}_{ses}_magnitude1.nii.gz",
            f"{sub}_{ses}_magnitude2.nii.gz",
            f"{sub}_{ses}_phase1.nii.gz",
            f"{sub}_{ses}_phase2.nii.gz"
        ]
    elif ses == 'ses-EVOL1':
        expected_files = [
            f"{sub}_{ses}_acq-dwi_dir-AP_epi.nii.gz",
            f"{sub}_{ses}_acq-dwi_dir-PA_epi.nii.gz"
        ]
    else:
        return pd.NA
    return all(os.path.exists(os.path.join(fmap_dir, fname)) for fname in expected_files)

def select_from_bin(group, bin_label):
    group = group.sort_values('qc', ascending=False).copy()
    n = len(group)
    top_n = (n // 2) + (n % 2)
    group['select_tbss'] = [True]*top_n + [False]*(n - top_n) if n >= 5 else [False]*n
    group['select_dtitk'] = [True] + [False]*(n - 1) if n < 5 else [False]*n
    group['bin'] = bin_label
    return group

# determine template images level 1
logging.info('read sessions.tsv for each participant and combine into a single dataframe')
dfs = []
for session in glob.glob(os.path.join(SESSIONS_PATH)):
    sub = SUB_PATTERN.search(session).group()
    df = pd.read_csv(session, sep = '\t')
    df['participant_id'] = sub
    df = df[['participant_id', 'session_id', 'age']]
    dfs.append(df)
sessions = pd.concat(dfs, ignore_index = True)

logging.info('read participants.tsv')
participants = pd.read_csv(PARTICIPANTS_PATH, sep='\t')

logging.info('read qc.tsv')
qc = (
    pd.read_csv(QC_PATH, sep='\t')
    .rename(columns={'dwi_tsnr_b0': 'qc'})
    .loc[:, ["sub", "ses", "qc"]]
)

logging.info('combine participants sessions, and qc into images')
images = (
    sessions
    .merge(participants, how = 'left', on = 'participant_id')
    .rename(columns={'participant_id': 'sub', 'session_id': 'ses'})
    .loc[:, ["sub", "ses", "age", "sex"]]
    .merge(qc, how = 'left', on = ['sub', 'ses'])
)

logging.info('define relevant paths for each sub_ses')
logging.info('remove those sub_ses where the corresponding dtitk preprocessed image doesn\'t exist')
images = (
    images
    .assign(
        dtitk_path=lambda df: Path(DWI_DIR) / df["sub"] / df["ses"] / "dwi" / (df["sub"] + "_" + df["ses"] + ".nii.gz"),
        fa_path=lambda df: Path(DWI_DIR) / df["sub"] / df["ses"] / "dwi" / (df["sub"] + "_" + df["ses"] + "_FA.nii.gz"),
        qsiprep_path=lambda df: Path(DWI_DIR) / df["sub"] / df["ses"] / "dwi" / (df["sub"] + "_" + df["ses"] + "_space-ACPC_desc-preproc_dwi.nii.gz")
    )
    .loc[lambda df: df["dtitk_path"].map(Path.exists)]
)

logging.info('read in the number of volumes for each qsiprep preprocessed image and remove those images where the number of volumes imply that it\'s only run-01 of ses-PNC1 missing run-02')
images = (
    images
    .assign(
        volumes=lambda df: df["qsiprep_path"].map(
            lambda path: nib.load(path).shape[3]
        )
    )
    .loc[lambda df: df["volumes"].gt(35)]
)

logging.info('for each sub_ses check if the corresponding fieldmaps exist and remove those sub_ses without a full compliment of fieldmaps')
images = (
    images
    .assign(
        fieldmap=lambda df: df.apply(check_fieldmap, axis=1)
    )
    .loc[lambda df: df["fieldmap"]]
)

logging.info('creats age bins of 2 years (8 year old age bin is seperate) and combine with sex to find template bins')
logging.info('subset to only be those columns we care about moving forward')
logging.info('within each bin determine which images move forward directly to dtitk template creation and which move forward to TBSS selection')
images = (
    images
    .assign(bin = lambda df: df["age"].astype("str").str.zfill(2) + df["sex"].str[0])
    .loc[:, ['bin', 'qc', 'dtitk_path', 'fa_path']]
    .groupby('bin', group_keys=False)
    .apply(lambda g: select_from_bin(g, g.name), include_groups=False)
)

logging.info('for those bins where there aren\'t enough images to run the TBSS pipeline pick the image with highest QC and move directly to dtitk template creation')
for _, image in images[images['select_dtitk']].iterrows():
    shutil.copy(image['dtitk_path'], BUILD_DIR)
logging.info('for those bins with 5 or more images run the TBSS pipeline to select the most representative image from each bin')
for bin in images['bin'].unique().tolist():
    n = sum(images['bin'] == bin)
    if n < 5:
        continue

    cmd = f"""#!/bin/bash
#BSUB -o {LOG_DIR}/{bin}.o
#BSUB -e {LOG_DIR}/{bin}.e
#BSUB -J template_select_{bin}

module load fsl/6.0.3

mkdir -p {SELECT_DIR}/{bin}

"""

    for image in images.loc[(images['bin'] == bin) & (images['select_tbss']), 'fa_path'].tolist():
        cmd += f"cp {image} {SELECT_DIR}/{bin}/{os.path.basename(image).replace('_FA', '')}\n"

    cmd += f"""
cd {SELECT_DIR}/{bin}
    
tbss_1_preproc *.nii.gz
tbss_2_reg -n
tbss_3_postreg -S
"""

    jobscript_path = os.path.join(JOBSCRIPT_DIR, f'{bin}.sh')
    logging.debug(f'writing jobscript to {jobscript_path}')
    with open(jobscript_path, 'w', opener=lambda path, flags: os.open(path, flags, 0o775)) as jobscript_file:
        jobscript_file.write(cmd)
    logging.debug(f'submitting jobscript to scheduler')
    os.system(f'bsub < {jobscript_path}')
