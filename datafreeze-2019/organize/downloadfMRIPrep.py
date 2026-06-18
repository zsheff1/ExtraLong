### This script downloads, unzips, and establishes a directory structure for
### all fmriprep output.
###
### Ellyn Butler
### October 7, 2020 - October 9, 2020

import subprocess as sub
import os
import flywheel
import json
import shutil
import re
import time
import pandas as pd
import pytz
import datetime
import zipfile
import numpy as np



#outdir = '/Users/butellyn/Documents/ExtraLong/data/freesurferCrossSectional/'
outdir = '/project/ExtraLong/data/freesurferCrossSectional/' # Path on PMACS

fw = flywheel.Client()
proj = fw.lookup('bbl/ExtraLong')
subjects = proj.subjects()


# This function loops through the analyses of a session, checks if `fmriprep`
# ran successfully, and returns the most recent successful `fmriprep` analysis.
def get_latest_fmriprep_correctversion(session, fmriprepVersion):
    if session.analyses:
        timezone = pytz.timezone("UTC")
        init_date = datetime.datetime(2018, 1, 1)
        latest_date = timezone.localize(init_date)
        latest_run = None
        for analysis in session.analyses:
            gear_name = analysis.gear_info['name']
            state = analysis.job.state
            date = analysis.created
            anal = analysis.label
            if 'fmriprep' in gear_name and date > latest_date and state =='complete' and fmriprepVersion in anal:
                latest_date = date
                latest_run = analysis
        if latest_run is not None:
            return(latest_run)
        else:
            return None
    else:
        return None

################################################################################
if not os.path.exists(outdir+'fmriprep'):
    os.mkdir(outdir+'fmriprep')
if not os.path.exists(outdir+'freesurfer'):
    os.mkdir(outdir+'freesurfer')


for subj in subjects: ######### Will take a lot of time for a lot of subjects!
    sublabel = subj['label']
    if not os.path.exists(outdir+'fmriprep/'+sublabel):
        os.mkdir(outdir+'fmriprep/'+sublabel)
    if not os.path.exists(outdir+'freesurfer/'+sublabel):
        os.mkdir(outdir+'freesurfer/'+sublabel)
    for ses in subj.sessions():
        ses = ses.reload()
        d = get_latest_fmriprep_correctversion(ses, '0.3.4_20.0.5')
        # Get file name
        seslabel = ses['label']
        try:
            filename = [s for s in d['job']['saved_files'] if 'fmriprep_sub-' in s]
            filename = filename[0]
            # Check if the fmriprep and freesurfer dirs are already in the ses dir
            if not os.path.exists(outdir+'fmriprep/'+sublabel+'/'+seslabel):
                d.download_file(filename, outdir+filename)
                # Unzip files
                with zipfile.ZipFile(outdir+filename,"r") as zip_ref:
                    zip_ref.extractall(outdir)
                # Get rid of id directory and zip
                iddir = [dI for dI in os.listdir(outdir) if os.path.isdir(os.path.join(outdir, dI))]
                iddir = np.setdiff1d(iddir, ['fmriprep', 'freesurfer'])[0]
                for processeddir in ['fmriprep', 'freesurfer']:
                    source = outdir+iddir+'/'+processeddir
                    files = os.listdir(source) #######
                    notsubdirfiles = []
                    for dI in os.listdir(outdir+iddir+'/'+processeddir):
                        if os.path.isdir(os.path.join(outdir+iddir+'/'+processeddir, dI)) and 'sub-' in dI:
                            subdir = dI
                        else:
                            notsubdirfiles.append(dI)
                    # Move contents of session-specific fmriprep dir to a session directory
                    # within the fmriprep-created subject directory.
                    sesdir = outdir+iddir+'/'+processeddir+'/'+sublabel+'/'+seslabel
                    if not os.path.exists(source+'/'+sublabel+'/'+seslabel):
                        os.mkdir(source+'/'+sublabel+'/'+seslabel)
                    for file in notsubdirfiles:
                        if not os.path.exists(sesdir+'/'+file):
                            shutil.move(f"{source}/{file}", sesdir)
                    # Move directories in sub dir into ses dir
                    for dI in os.listdir(outdir+iddir+'/'+processeddir+'/'+sublabel):
                        if not 'ses-' in dI:
                            if not os.path.exists(sesdir+'/'+dI):
                                shutil.move(f"{source+'/'+sublabel}/{dI}", sesdir)
                    # Rename all of the files with the sub label to include the ses label
                    for path, subdirs, files in os.walk(sesdir):
                        for name in files:
                            if sublabel in name and not seslabel in name:
                                newname = name.replace(sublabel, sublabel+'_'+seslabel)
                                shutil.move(os.path.join(path, name), os.path.join(path, newname))
                    # Move this sub*/ses* directory into the fmriprep directory that I created
                    subdir = outdir+iddir+'/'+processeddir+'/'+sublabel
                    if not os.path.exists(outdir+processeddir+'/'+sublabel):
                        shutil.move(subdir, outdir+processeddir)
                    else:
                        # Move the contents of ses dir into the fmriprep ses dir
                        shutil.move(sesdir, outdir+processeddir+'/'+sublabel)
                        os.rmdir(source+'/'+sublabel)
                    # Delete the directory with the analysis ID as the name
                    os.rmdir(source)
                os.remove(outdir+filename)
                os.rmdir(outdir+iddir)
        except TypeError:
            print(sublabel+' '+seslabel)
