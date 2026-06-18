### This script identifies sessions that have more than one T1w image
###
### Ellyn Butler
### September 30, 2019


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

zeroissue = {"strippedSubject":[], "subject":[], "subjectid":[], "session":[], "sessionid":[], "numacquisitions":[], "zero":[], "count":[]}
proj = client.projects.find_first("label=PNC_LG_810336")
subjlabels = []
subjlabels_withzero = []
for subject in proj.subjects():
    subjlabels.append(subject.label.lstrip('0'))
    subjlabels_withzero.append(subject.label)
for subject in proj.subjects():
    for session in subject.sessions():
        zeroissue["strippedSubject"].append(subject.label.lstrip('0'))
        zeroissue["subject"].append(subject.label)
        zeroissue["subjectid"].append(subject.id)
        zeroissue["session"].append(session.label)
        zeroissue["sessionid"].append(session.id)
        zeroissue["numacquisitions"].append(len(session.acquisitions()))
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
zero_df = zero_df[zero_df.zero == "yes"]
zero_df = zero_df[zero_df.count > 1]
zero_df = zero_df.sort_values(by=['strippedSubject'])
zero_df.to_csv(r'/Users/butellyn/Documents/fwheudiconv/ExtraLong/duplicateSubjects_PNC_LG_810336.csv', index=False)



# Fairly confident that all of the subjects in this dataframe with a prepended
# 0 are duplicate data. Delete these subjects
subjectstodelete = []
for i in zero_df.subject:
    if i[0] == '0':
        subjectstodelete.append(i)


#for subject in proj.subjects():
#    if subject.label in subjectstodelete:
#        subject.delete() ### Not working
