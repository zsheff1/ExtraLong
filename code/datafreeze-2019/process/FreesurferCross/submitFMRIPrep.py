### This script submits qsub jobs calling the singularity container for freeqc,
### and creates the output directory structure for freeqc on PMACS.
###
### Ellyn Butler
### October 25, 2020

import os
import shutil
import re
import numpy as np

indir = '/project/ExtraLong/data/bids_directory/'
outdir = '/project/ExtraLong/data/freesurferCrossSectional/fmriprep/'
freelic = '/project/ExtraLong/data/license.txt'

subjs = ['sub-100278', 'sub-117595', 'sub-98585']

for subj in subjs:
    if not os.path.exists(outdir+subj):
        os.mkdir(outdir+subj)
    unprocessed_sessions = np.setdiff1d(os.listdir(indir+subj), os.listdir(outdir+subj))
    for ses in unprocessed_sessions:
        if not os.path.exists(outdir+subj+'/'+ses):
            os.mkdir(outdir+subj+'/'+ses)
        ses_indir = indir+subj+'/'+ses
        ses_outdir = outdir+subj+'/'+ses
        #participant = subj.split('-')[1]
        cmd = ['singularity', 'run', '--writable-tmpfs', '--cleanenv',
            '-B /project/ExtraLong/data/templateflow:/templateflow',
            '-B /project/ExtraLong/data/license.txt:/opt/freesurfer/license.txt',
            '-B /project/ExtraLong/data/',
            '/project/ExtraLong/images/fmriprep_20.0.5.sif', ses_indir, ses_outdir,
            'participant', '--skip_bids_validation', '--anat-only',
            '--fs-license-file /opt/freesurfer/license.txt',
            '--output-spaces MNI152NLin2009cAsym',
            '--skull-strip-template OASIS30ANTs', '--nthreads 7'] # just one session?
            # Default output space: MNI152NLin2009cAsym
            # 'SINGULARITYENV_TEMPLATEFLOW_HOME=/templateflow',
            #${TEMPLATEFLOW_HOME:-$HOME/.cache/templateflow}:/templateflow
        fmriprep_script = ses_outdir+'/fmriprep_run.sh'
        os.system('echo '+' '.join(cmd)+' > '+fmriprep_script)
        os.system('chmod +x '+fmriprep_script)
        os.system('bsub '+fmriprep_script)



  #'SINGULARITYENV_FS_LICENSE=/project/ExtraLong/data/freesurfer.txt',
