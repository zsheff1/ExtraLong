### This script submits qsub jobs calling the singularity container for freeqc,
### and creates the output directory structure for freeqc on PMACS.
###
### Ellyn Butler
### December 3, 2020

import os
import shutil
import re
import pandas as pd

indir = '/project/ExtraLong/data/freesurferCrossSectional/fmriprep/'
outdir = '/project/ExtraLong/data/singleSubjectTemplates/antssst2/'

# Load csv of subjects and sessions to include in SSTs
dat = pd.read_csv('/project/ExtraLong/data/qualityAssessment/antssstExclude.csv')
dat['bblid'] = dat['bblid'].astype(str)

subjs = ['sub-'+x for x in dat.bblid.unique()]
for subj in subjs:
    # Check if the subject has any sessions that should be included
    bblid = subj.split('-')[1]
    bblid_df = dat[dat['bblid'] == bblid]
    if False in bblid_df.antssstExclude.unique():
        if not os.path.exists(outdir+subj):
            os.mkdir(outdir+subj)
        # Get the session labels to include
        include_df = bblid_df[bblid_df['antssstExclude'] == False]
        sessions_all = ['ses-'+x for x in bblid_df['seslabel']]
        sessions = ['ses-'+x for x in include_df['seslabel']]
        sessions_bad = list(set(sessions_all).difference(sessions))
        if len(sessions_bad) > 0:
            for ses in sessions_bad:
                if os.path.exists(outdir+subj+'/'+ses):
                    os.system('rm -r '+outdir+subj)
                    os.mkdir(outdir+subj)
                    sessions_string = ' '.join(sessions)
                    sub_indir = indir+subj
                    sub_outdir = outdir+subj
                    cmd = ['singularity', 'exec', '--writable-tmpfs', '--cleanenv',
                        '-B', sub_indir+':/data/input', '-B', sub_outdir+':/data/output',
                        '/project/ExtraLong/images/antssst_0.0.3.sif', '/scripts/run.sh', sessions_string]
                    antssst_script = sub_outdir+'/antssst_run.sh'
                    os.system('echo '+' '.join(cmd)+' > '+antssst_script)
                    os.system('chmod +x '+antssst_script)
                    os.system('bsub -o '+sub_outdir+'/jobinfo.log '+antssst_script)
                    break
        else:
            directory_contents = os.listdir(outdir+subj)
            ses_dirs = []
            if len(directory_contents) > 1:
                for item in directory_contents:
                    if os.path.isdir(outdir+subj+'/'+item):
                        ses_dirs.append(item)
                if len(ses_dirs) == len(sessions):
                    if sorted(ses_dirs) != sorted(sessions):
                        print(bblid+' does not have at least one bad session, but the sessions to be included also does not match the sessions already processed. VERY BAD.')
                else:
                    print(bblid+' does not have at least one bad session, but the number of sessions to be included also does not match the number of sessions already processed. VERY BAD.')
            else:
                print(bblid+' has not previously been run through ANTsSST. Running for the first time now.')
                sessions_string = ' '.join(sessions)
                sub_indir = indir+subj
                sub_outdir = outdir+subj
                cmd = ['singularity', 'exec', '--writable-tmpfs', '--cleanenv',
                    '-B', sub_indir+':/data/input', '-B', sub_outdir+':/data/output',
                    '/project/ExtraLong/images/antssst_0.0.3.sif', '/scripts/run.sh', sessions_string]
                antssst_script = sub_outdir+'/antssst_run.sh'
                os.system('echo '+' '.join(cmd)+' > '+antssst_script)
                os.system('chmod +x '+antssst_script)
                os.system('bsub -o '+sub_outdir+'/jobinfo.log '+antssst_script)













# Don't mount home to singularity
# 1. "singularity run as specific user"
# 2. Fake root
