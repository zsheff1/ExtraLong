### This script creates a csv of subject and session identifiers currently in ExtraLong
###
### Ellyn Butler
### October 17, 2019

import flywheel
import json
import array
import numpy as np
import pandas as pd
from datetime import date

client = flywheel.Client()

bblids = {"bblid":[], "seslabel":[]}

proj = client.projects.find_first("label=ExtraLong")
for subj in proj.subjects():
    for session in subj.sessions():
        bblids["bblid"].append(subj.label.split('-')[1])
        bblids["seslabel"].append(session.label.split('-')[1])

bblids2 = pd.DataFrame.from_dict(bblids)


filename = '/Users/butellyn/Documents/bids_curation/ExtraLong/ExtraLong_' + date.today().strftime("%m-%d-%Y") + '.csv'
bblids2.to_csv(filename, index=False)
