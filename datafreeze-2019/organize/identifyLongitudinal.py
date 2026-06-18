### NOTICE: Only to be done once all duplicate scans within a session have been cleared
### from BIDS and raw niftis have been deleted (but not raw dicoms, obviously)
### Purpose: Loop through all projects that recruited from PNC, identify number of sessions
### per bblid, and if there is more than one, add that bblid to a list for that project
###
### Ellyn Butler
### September 16, 2019 - October 1, 2019

import subprocess as sub
import os
import flywheel
import json
import shutil
import re
import time
import array
import numpy as np
import pandas as pd

client = flywheel.Client()
studies = ["AGGY_808689", "CONTE_815814", "GRMPY_822831", "MOTIVE",
    "ONM_816275", "PNC_CS_810336", "PNC_LG_810336", "SYRP_818621",
    "FNDM1_810211", "FNDM2_810211", "NEFF_818028", "NODRA_816281",
    "DAY2_808799"]

bblids = {} # <bblid>:<path to raw T1w image that exists in BIDS>

for study in studies:
    labelstr = "label=" + study
    proj = client.projects.find_first(labelstr)
    for subj in proj.subjects():
        if subj['label'] not in bblids.keys():
            bblids[subj['label']] = []
        # List with BIDS names
        sessions = subj.sessions()
        for session in sessions:
            for acq in session.acquisitions():
                for i in range(0, len(acq.files)):
                    if len(acq.files[i]['info']) > 0:
                        if acq.files[i]['info']['BIDS']:
                            if acq.files[i]['info']['BIDS'] != 'NA':
                                if 'Filename' in acq.files[i]['info']['BIDS'].keys():
                                    mod = acq.files[i]['info']['BIDS']['Filename'].split("_")[-1].split(".")[0]
                                    if mod == "T1w": #use BIDS file name
                                        if [study, session.label] not in bblids[subj['label']]:
                                            bblids[subj['label']].append([study, session.label])

# Identify Longitudinal Cohort
longitudinal = {}
for bblid in bblids.keys():
    if len(bblids[bblid]) > 1:
        longitudinal[bblid] = bblids[bblid]

for study in studies:
    studylist = []
    for lkey in longitudinal.keys():
        for minilist in longitudinal[lkey]:
            if study == minilist[0]:
                studylist.append(str(lkey))
    long_df = pd.DataFrame.from_dict(studylist)
    long_df = long_df.rename(columns={0:"bblid"})
    filename = "/Users/butellyn/Documents/bids_curation/ExtraLong/longbblids_"+study+".csv"
    long_df.to_csv(filename, index=False)


# Copy T1w acquisitions from Longitudinal Cohort NOTE: not working yet
#extralong = client.projects.find_first('label=ExtraLong')
#for bblid in longitudinal.keys():
#    subject = client.add_subject(flywheel.Subject(project=extralong, label=str(bblid)))
#    for acq in longitudinal[bblid]:
#        acquisition = client.get(acq)
#        #scanid = acquisition.parents['session']['label']
#        scanid = client.get(acquisition.parents['session'])['label']
#        session = extralong.subject.add_session(label=str(scanid))






for acq in session.acquisitions():
    for i in range(0, len(acq.files)):
        if len(acq.files[i]['info']) > 0:
            if acq.files[i]['info']['BIDS']:
                if acq.files[i]['info']['BIDS'] != 'NA':
                    if 'Filename' in acq.files[i]['info']['BIDS'].keys():
                        mod = acq.files[i]['info']['BIDS']['Filename'].split("_")[-1].split(".")[0]
                        if mod == "T1w": #use BIDS file name
                            break
