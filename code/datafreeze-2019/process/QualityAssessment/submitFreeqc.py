### This script submits qsub jobs calling the singularity container for freeqc,
### and creates the output directory structure for freeqc on PMACS.
###
### Ellyn Butler
### October 15, 2020 - October 16, 2020

import os
import shutil
import re
import logging

indir = '/project/ExtraLong/data/freesurferCrossSectional/freesurfer/'
outdir = '/project/ExtraLong/data/freesurferCrossSectional/freeqc/'
subcol = 'bblid'
freelic = '/project/ExtraLong/data/license.txt'

for subj in os.listdir(indir):
    if not os.path.exists(outdir+subj):
        os.mkdir(outdir+subj)
    for ses in os.listdir(indir+subj):
        if not os.path.exists(outdir+subj+'/'+ses):
            os.mkdir(outdir+subj+'/'+ses)
        ses_indir = indir+subj+'/'+ses
        ses_outdir = outdir+subj+'/'+ses
        cmd = ['SINGULARITYENV_SUBCOL='+subcol, 'SINGULARITYENV_SUBNAME='+subj,
            'SINGULARITYENV_SESNAME='+ses, 'singularity', 'run', '--writable-tmpfs', '--cleanenv',
            '-B', ses_indir+':/input/data', '-B', freelic+':/input/license/license.txt',
            '-B', ses_outdir+':/output', '/project/ExtraLong/images/freeqc_0.0.9.sif']
        freeqc_script = ses_outdir+'/freeqc_run.sh'
        os.system('echo '+' '.join(cmd)+' > '+freeqc_script)
        os.system('chmod +x '+freeqc_script)
        os.system('bsub '+freeqc_script)


# Don't mount home to singularity
# 1. "singularity run as specific user"
# 2. Fake root
