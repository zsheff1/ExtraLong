### This script identifies sessions that have more than one T1w image
###
### Ellyn Butler
### September 10, 2019 - September 19, 2019


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
    # CONTE_815814 bblid 13473 messed up (also has a session under 013473)
    # GRMPY_822831 has many subjects with the label "unknown"

    # Run on Reward2018 and MOTIVE once Session labels are fixed: "Reward2018":[], "MOTIVE":[],
    # Reward2018: "FNDM1_810211":[], "FNDM2_810211":[], "NODRA_816281":[]
    # Part of GRMPY: "EONSX_810366":[]

##### Make csv of subjects and sessions in PNC_CS_810336
proj = client.projects.find_first("label=PNC_CS_810336")
bblidscanid = {"subject":[], "session":[]}
for subject in proj.subjects():
    if len(subject.sessions()) != 0:
        for session in subject.sessions():
                bblidscanid["subject"].append(subject.label)
                bblidscanid["session"].append(session.label)

bblidscanid_df = pd.DataFrame.from_dict(bblidscanid)
bblidscanid_df.to_csv(r'/Users/butellyn/Documents/fwheudiconv/PNC_CS_810336/n1600_flywheel.csv', index=False)

##### DUPLICATE SUBJECTS: Identify subjects who are in a project twice, possibly
##### with and without a preceding 0
for study in studies:
    zeroissue = {"study":[], "subject":[], "subjectid":[], "zero":[], "count":[]}
    labelstr = "label=" + study
    proj = client.projects.find_first(labelstr)
    subjlabels = []
    subjlabels_withzero = []
    for subject in proj.subjects():
        subjlabels.append(subject.label.lstrip('0'))
        subjlabels_withzero.append(subject.label)
    for subject in proj.subjects():
        if subject.label.lstrip('0') not in zeroissue["subject"]:
            zeroissue["study"].append(study)
            zeroissue["subject"].append(subject.label.lstrip('0'))
            zeroissue["subjectid"].append(subject.id)
            num = subjlabels.count(subject.label.lstrip('0'))
            zeroissue["count"].append(num)
            versions = [i for i in subjlabels_withzero if subject.label in i]
            zeropresent = []
            for version in versions:
                if version[0] == '0':
                    zeropresent.append("yes")
                else:
                    zeropresent.append("no")
            if "yes" in zeropresent:
                zeroissue["zero"].append("yes")
            else:
                zeroissue["zero"].append("no")
        # Possibility: change the subjectid to the version with less data (?),
        # or if that doesn't exist, the one with a preceding 0
    zero_df = pd.DataFrame.from_dict(zeroissue)
    zero_df.count = pd.to_numeric(zero_df["count"])
    zero_df = zero_df[zero_df.count > 1]
    globals()["zero_" + study] = zero_df
    if len(zero_df.index) > 0:
        filename = '/Users/butellyn/Documents/fwheudiconv/ExtraLong/zero_' + study + '.csv'
        zero_df.to_csv(filename, index=False)


##### SUBJECTS WITH ZERO SESSIONS IN FLYWHEEL
nosessions = {"study":[], "subject":[], "subjectid":[]}
for study in studies:
    labelstr = "label=" + study
    proj = client.projects.find_first(labelstr)
    for subject in proj.subjects():
        if len(subject.sessions()) == 0:
            nosessions["study"].append(study)
            nosessions["subject"].append(subject.label)
            nosessions["subjectid"].append(subject.id)

nosessions_df = pd.DataFrame.from_dict(nosessions)

nosessions_df.to_csv(r'/Users/butellyn/Documents/fwheudiconv/ExtraLong/nosessions.csv', index=False)

##### SESSIONS WITH ZERO ACQUISITIONS IN FLYWHEEL
for study in studies:
    noacquisitions = {"study":[], "subject":[], "subjectid":[], "session":[], "sessionid":[]}
    labelstr = "label=" + study
    proj = client.projects.find_first(labelstr)
    for subject in proj.subjects():
        if len(subject.sessions()) != 0:
            for session in subject.sessions():
                if len(session.acquisitions()) == 0:
                    noacquisitions["study"].append(study)
                    noacquisitions["subject"].append(subject.label)
                    noacquisitions["subjectid"].append(subject.id)
                    noacquisitions["session"].append(session.label)
                    noacquisitions["sessionid"].append(session.id)
    noacquisitions_df = pd.DataFrame.from_dict(noacquisitions)
    if len(noacquisitions_df.index) > 0:
        filename = '/Users/butellyn/Documents/fwheudiconv/ExtraLong/noacquisitions_' + study + '.csv'
        noacquisitions_df.to_csv(filename, index=False)

##### STRIP ZEROS #October 1, 2019: ADD IN TRY EXCEPT
for study in ["PNC_LG_810336"]:
    labelstr = "label=" + study
    proj = client.projects.find_first(labelstr)
    for subject in proj.subjects():
        subject.update({'label':subject.label.lstrip('0')}) # This works
    for session in proj.sessions():
        # Strip 0s at the front of session
        session.update({'label':session.label.lstrip('0')}) # This works... but very slow

##### CREATE DATAFRAME OF DUPLICATE T1W IMAGES
duplicates = {"study":[], "bblid":[], "scanid":[], "bidsname":[], "origname":[], "id":[], "use":[]}
for study in studies:
    labelstr = "label=" + study
    proj = client.projects.find_first(labelstr)
    for session in proj.sessions():
        # List with BIDS names
        for acq in session.acquisitions():
            for i in range(0, len(acq.files)):
                if len(acq.files[i]['info']) > 0:
                    if acq.files[i]['info']['BIDS']:
                        if acq.files[i]['info']['BIDS'] != 'NA':
                            if 'Filename' in acq.files[i]['info']['BIDS'].keys():
                                mod = acq.files[i]['info']['BIDS']['Filename'].split("_")[-1].split(".")[0]
                                if mod == "T1w": #use BIDS file name
                                    duplicates["study"].append(study)
                                    duplicates["bblid"].append(acq.files[i]['info']['BIDS']['Filename'].split("_")[0].split("-")[1])
                                    duplicates["scanid"].append(session.label)
                                    duplicates["bidsname"].append(acq.files[i]['info']['BIDS']['Filename'])
                                    duplicates["origname"].append(acq.files[i]['name'])
                                    duplicates["id"].append(acq.id)
                                    duplicates["use"].append("TBD")


# Create pandas dataframe
duplicates2 = pd.DataFrame.from_dict(duplicates)

# Keep scanids that are not unique
duplicates2["duplicated"] = duplicates2.duplicated("scanid", False)
duplicates2 = duplicates2[duplicates2["duplicated"] == True]

# Get rid of "duplicated" column
duplicates2 = duplicates2.drop(columns="duplicated")

# Write dataframe to csv
duplicates2.to_csv(r'/Users/butellyn/Documents/fwheudiconv/ExtraLong/duplicates.csv', index=False)
