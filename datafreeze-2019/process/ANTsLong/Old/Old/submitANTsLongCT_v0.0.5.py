### This script submits antslongct
###
### Ellyn Butler
### December 3, 2020 - March 26, 2021

import os
import shutil
import re
import pandas as pd

gr_indir = '/project/ExtraLong/data/groupTemplates/antspriors/'
sst_indir = '/project/ExtraLong/data/singleSubjectTemplates/antssst5/'
outdir = '/project/ExtraLong/data/corticalThickness/antslongct3/'

if not os.path.exists(outdir):
    os.mkdir(outdir)

subjs = os.listdir(sst_indir)

for subj in subjs:
    if not os.path.exists(outdir+subj):
        os.mkdir(outdir+subj)
    directory_contents = os.listdir(outdir+subj)
    if len(directory_contents) > 1:
        print(subj+' already has some output, and as such will not be run again with this output directory')
    else:
        print(subj+' has not previously been run through ANTsLongCT. Running for the first time now.')
        sub_indir = sst_indir+subj
        sub_outdir = outdir+subj
        cmd = ['SINGULARITYENV_projectName=ExtraLong', 'SINGULARITYENV_subLabel=bblid',
            'singularity', 'run', '--writable-tmpfs', '--cleanenv',
            '-B', sub_indir+':/data/input/'+subj, '-B', gr_indir+':/data/input/antspriors/',
            '-B', sub_outdir+':/data/output', '/project/ExtraLong/images/antslongct_0.0.5.sif']
        antslongct_script = sub_outdir+'/antslongct_run.sh'
        os.system('echo '+' '.join(cmd)+' > '+antslongct_script)
        os.system('chmod +x '+antslongct_script)
        os.system('bsub -R "rusage[mem=12GB]" -o '+sub_outdir+'/jobinfo.log '+antslongct_script)
