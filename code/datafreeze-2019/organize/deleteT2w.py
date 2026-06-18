### This script deletes T2w data from Extra Long (made it in accidentally)
###
### Ellyn Butler
### October 25, 2019 - October 28, 2019

import flywheel
import json
import array
import numpy as np
import pandas as pd
from datetime import date

client = flywheel.Client()

proj = client.projects.find_first("label=ExtraLong")

t2w_acqid = []
for session in proj.sessions():
    for acq in session.acquisitions():
        for i in range(0, len(acq.files)):
            if "T2w" in acq.label:
                t2w_acqid.append(acq.id)

for t2wfile in t2w_acqid[1:]:
    client.delete_acquisition(t2wfile)
