### This script takes the output of pickSubjsForTemplate_onlytwo.R (subject/sessions
### pairs in a csv) and calls antspriors to create a group template and priors
### SIMPLIFIED MULTIVARIATE CALL
###
### Ellyn Butler
### March 1, 2021

import os
import shutil
import re
import pandas as pd

prepdir = '/project/ExtraLong/data/freesurferCrossSectional/fmriprep/'
sstdir = '/project/ExtraLong/data/singleSubjectTemplates/antssst5/'
outdir = '/project/ExtraLong/data/groupTemplates/versionTwentyFour/'

if not os.path.isdir(outdir):
    os.mkdir(outdir)

# Load csv of subjects and sessions to include in SSTs
dat = pd.read_csv('/project/ExtraLong/data/groupTemplates/subjsFromN752_set5.csv')
dat['bblid'] = dat.bblid.astype(str)

dataToBind = ''

# Create bind call to individual session data
for index, row in dat.iterrows():
    # Find aseg
    ses_prepdir = prepdir+'sub-'+row['bblid']+'/ses-'+row['seslabel']+'/anat'
    aseg = [item for item in os.listdir(ses_prepdir) if '-aseg_dseg.nii.gz' in item]
    aseg = aseg[0] if len(aseg) == 1 else print(row['bblid']+' '+row['seslabel']+' is messed up')
    dataToBind = dataToBind+'-B '+ses_prepdir+'/'+aseg+':/data/input/'+aseg+' '
    # Find warp
    ses_sstdir = sstdir+'sub-'+row['bblid']+'/ses-'+row['seslabel']
    warp = [item for item in os.listdir(ses_sstdir) if 'Warp.nii.gz' in item and 'Inverse' not in item]
    warp = warp[0] if len(warp) == 1 else print(row['bblid']+' '+row['seslabel']+' is messed up')
    dataToBind = dataToBind+'-B '+ses_sstdir+'/'+warp+':/data/input/'+warp+' '
    # Find affine
    affine = [item for item in os.listdir(ses_sstdir) if 'Affine' in item]
    affine = affine[0] if len(affine) == 1 else print(row['bblid']+' '+row['seslabel']+' is messed up')
    dataToBind = dataToBind+'-B '+ses_sstdir+'/'+affine+':/data/input/'+affine+' '

# Create bind call to SST data
for bblid in dat['bblid'].unique():
    template_dir = sstdir+'sub-'+bblid
    template = [item for item in os.listdir(template_dir) if 'template' in item and 'warp' not in item and '.nii.gz' in item]
    template = template[0] if len(template) == 1 else print(bblid+' is messed up')
    dataToBind = dataToBind+'-B '+template_dir+'/'+template+':/data/input/'+template+' '

# Create bind call to output directory
dataToBind = dataToBind+'-B /project/ExtraLong/data/groupTemplates/versionTwentyFour:/data/output '

# Bind the mindboggle images
#dataToBind = dataToBind+'-B /project/ExtraLong/data/mindboggle/dataverse_files:/data/input/dataverse_files'
dataToBind = dataToBind+'-B /project/ExtraLong/data/mindboggleVsBrainCOLOR_Atlases:/data/input/mindboggleVsBrainCOLOR_Atlases'


cmd = ['SINGULARITYENV_projectName=ExtraLong', 'SINGULARITYENV_NumSSTs=8',
        'SINGULARITYENV_atlases=nowhitematter', 'singularity', 'exec',
        '--writable-tmpfs', '--cleanenv', dataToBind,
        '/project/ExtraLong/images/antspriors_0.0.34.sif', '/scripts/run.sh']
antspriors_script = outdir+'antspriors_run.sh'
os.system('echo '+' '.join(cmd)+' > '+antspriors_script)
os.system('chmod +x '+antspriors_script)
os.system('bsub -o '+outdir+'/jobinfo.log -n 8 '+antspriors_script)
