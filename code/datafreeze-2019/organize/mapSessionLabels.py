### This script creates a csv to map different session labels to one another
### in ExtraLong
###
### Ellyn Butler
### October 8, 2019 - October 16, 2019

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
from datetime import date

client = flywheel.Client()
studies = ["AGGY_808689", "CONTE_815814", "GRMPY_822831", "MOTIVE",
    "ONM_816275", "PNC_CS_810336", "PNC_LG_810336", "SYRP_818621",
    "FNDM1_810211", "FNDM2_810211", "NEFF_818028", "NODRA_816281",
    "DAY2_808799"]

longitudinal = {"study":[], "bblid":[], "scanid":[], "seslabel":[]}
sublabellist = []
for study in studies:
    long_df = pd.read_csv("/Users/butellyn/Documents/bids_curation/ExtraLong/longbblids_"+study+".csv") #October 9: somehow these got written over yesterday
    labelstr = "label=" + study
    proj = client.projects.find_first(labelstr)
    longdflist = long_df["bblid"].to_list()
    for j in range(len(longdflist)):
        longdflist[j] = str(longdflist[j])
    for subj in proj.subjects():
        subj_label = subj.label
        if subj_label in longdflist:
            sublabellist.append(subj_label)
            for session in subj.sessions():
                for acq in session.acquisitions():
                    for i in range(0, len(acq.files)):
                        if len(acq.files[i]['info']) > 0:
                            if 'BIDS' in acq.files[i]['info'].keys():
                                if acq.files[i]['info']['BIDS'] != 'NA':
                                    if 'Filename' in acq.files[i]['info']['BIDS'].keys():
                                        mod = acq.files[i]['info']['BIDS']['Filename'].split("_")[-1].split(".")[0]
                                        if mod == "T1w": #use BIDS file name
                                            longitudinal["study"].append(study)
                                            longitudinal["bblid"].append(acq.files[i]['info']['BIDS']['Filename'].split("_")[0].split("-")[1])
                                            longitudinal["scanid"].append(session.label)
                                            longitudinal["seslabel"].append(acq.files[i]['info']['BIDS']['Filename'].split("_")[1].split("-")[1])

# Create pandas dataframe
longitudinal2 = pd.DataFrame.from_dict(longitudinal)

longitudinal2 = longitudinal2.drop_duplicates()

filename = '/Users/butellyn/Documents/bids_curation/ExtraLong/scanid_to_seslabel_' + date.today().strftime("%m-%d-%Y") + '.csv'
longitudinal2.to_csv(filename, index=False)
