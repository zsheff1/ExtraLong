### This script takes the output of pickSubjsForTemplate_onlytwo.R (subject/sessions
### pairs in a csv) and calls antspriors to create a group template and priors
### SIMPLIFIED MULTIVARIATE CALL
###
### Ellyn Butler
### March 16, 2021

import os
import shutil
import re
import pandas as pd

prepdir = '/project/ExtraLong/data/freesurferCrossSectional/fmriprep/'
sstdir = '/project/ExtraLong/data/singleSubjectTemplates/antssst5/'
outdir = '/project/ExtraLong/data/groupTemplates/antspriors/'

if not os.path.isdir(outdir):
    os.mkdir(outdir)

# Load csv of subjects and sessions to include in SSTs
dat = pd.read_csv('/project/ExtraLong/data/groupTemplates/subjsFromN752_set5.csv')
dat['bblid'] = dat.bblid.astype(str)

dataToBind = ''

for bblid in dat['bblid'].unique():
    # Create bind call to fmriprep data
    sub_prepdir = prepdir+'sub-'+bblid
    dataToBind = dataToBind+'-B '+sub_prepdir+':/data/input/fmriprep/sub-'+bblid+' '
    # Create bind call to SST data
    template_dir = sstdir+'sub-'+bblid
    dataToBind = dataToBind+'-B '+template_dir+':/data/input/antssst/sub-'+bblid+' '

# Create bind call to output directory
dataToBind = dataToBind+'-B '+outdir+':/data/output '

# Bind the mindboggle images
#dataToBind = dataToBind+'-B /project/ExtraLong/data/mindboggle/dataverse_files:/data/input/dataverse_files'
dataToBind = dataToBind+'-B /project/ExtraLong/data/mindboggleVsBrainCOLOR_Atlases:/data/input/mindboggleVsBrainCOLOR_Atlases'


cmd = ['SINGULARITYENV_projectName=ExtraLong', 'SINGULARITYENV_NumSSTs=8',
        'SINGULARITYENV_atlases=nowhitematter', 'singularity', 'run',
        '--writable-tmpfs', '--cleanenv', dataToBind,
        '/project/ExtraLong/images/antspriors_0.0.35.sif']
antspriors_script = outdir+'antspriors_run.sh'
os.system('echo '+' '.join(cmd)+' > '+antspriors_script)
os.system('chmod +x '+antspriors_script)
os.system('bsub -o '+outdir+'/jobinfo.log -n 8 '+antspriors_script)
