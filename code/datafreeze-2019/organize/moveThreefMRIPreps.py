### This script moves the three session that weren't processed on Flywheel,
### and were instead processed on PMACS, into the correct directory structure.
###
### Ellyn Butler
### October 29, 2020

import os
import shutil

outdir = '/project/ExtraLong/data/freesurferCrossSectional/'

subses = {'sub-100278':'ses-PNC3', 'sub-117595':'ses-PNC1', 'sub-98585':'ses-PNC1'} #completed 

for sublabel in list(subses.keys()): ######### Will take a lot of time for a lot of subjects!
    if not os.path.exists(outdir+'fmriprep/'+sublabel):
        os.mkdir(outdir+'fmriprep/'+sublabel)
    if not os.path.exists(outdir+'freesurfer/'+sublabel):
        os.mkdir(outdir+'freesurfer/'+sublabel)
    seslabel = subses[sublabel]
    for processeddir in ['fmriprep', 'freesurfer']:
        source = outdir+'fmriprep/'+sublabel+'/'+seslabel+'/'+processeddir
        files = os.listdir(source) #######
        notsubdirfiles = []
        for dI in os.listdir(source):
            if os.path.isdir(os.path.join(source, dI)) and 'sub-' in dI:
                subdir = dI
            else:
                notsubdirfiles.append(dI)
        # Move contents of session-specific fmriprep dir to a session directory
        # within the fmriprep-created subject directory.
        procdir = source+'/'+sublabel # Where the processed output lives
        sesdir = outdir+processeddir+'/'+sublabel+'/'+seslabel # Where we want the output to end up, and where all of it began if processeddir is fmriprep
        if not os.path.exists(sesdir):
            os.mkdir(sesdir)
        for file in notsubdirfiles:
            if not os.path.exists(sesdir+'/'+file):
                shutil.move(f"{source}/{file}", sesdir)
        # Move directories in sub dir into ses dir
        for dI in os.listdir(source+'/'+sublabel):
            if not os.path.exists(sesdir+'/'+dI):
                shutil.move(f"{source+'/'+sublabel}/{dI}", sesdir)
        if os.path.exists(sesdir+'/'+seslabel):
            for dI in os.listdir(sesdir+'/'+seslabel):
                shutil.move(f"{sesdir+'/'+seslabel}/{dI}", sesdir)
            os.rmdir(sesdir+'/'+seslabel)
        # Rename all of the files with the sub label to include the ses label
        for path, subdirs, files in os.walk(sesdir):
            for name in files:
                if sublabel in name and not seslabel in name:
                    newname = name.replace(sublabel, sublabel+'_'+seslabel)
                    shutil.move(os.path.join(path, name), os.path.join(path, newname))
        # Delete the nested directory that is now empty
        os.rmdir(source+'/'+sublabel)
        os.rmdir(source)
