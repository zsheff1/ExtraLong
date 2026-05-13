### This script creates columns for bblid and seslabel in each of the
### freesurfer output csvs
###
### Ellyn Butler
### September 15, 2020 - October 15, 2020

import pandas as pd
from os import listdir
from os.path import isfile, join
import sys

subCol = sys.argv[1]
outputdir = sys.argv[2]
onlyfiles = [f for f in listdir(outputdir) if isfile(join(outputdir, f))]
onlyfiles = [f for f in onlyfiles if 'quality' not in f and 'csv' in f]

def createIdCols(file):
    bblid = file.split('_')[0].split('-')[1]
    seslabel = file.split('_')[1].split('-')[1]
    df = pd.read_csv(outputdir+file)
    if 'sub' in df.iloc[0,0]:
        df = df.drop(labels=df.columns[0], axis=1)
    df[subCol] = bblid
    df['seslabel'] = seslabel
    cols = df.columns.tolist()
    cols = cols[-1:] + cols[:-1]
    cols = cols[-1:] + cols[:-1]
    df = df[cols]
    df.to_csv(outputdir+file, index=False)

for file in onlyfiles:
    createIdCols(file)
