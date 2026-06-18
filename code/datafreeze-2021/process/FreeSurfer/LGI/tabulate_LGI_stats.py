### This script combines each type of freeqc output into a csv
###

import os
import glob
import csv
import pandas as pd
from datetime import datetime


datatypes = ['lh.aparc.pial_lgi_clean','rh.aparc.pial_lgi_clean']

base_dir = '/project/ExtraLong/data/datafreeze-2021'
freeqc_dir = base_dir + '/FreeQC/Longitudinal'
output_dir = base_dir + '/TabulatedQC/Longitudinal'

if not os.path.exists(output_dir):
    os.mkdir(output_dir)

for datatype in datatypes:
    files = glob.glob(freeqc_dir + '/sub*/ses*/*' + datatype + '.csv')
    df = pd.concat((pd.read_csv(f, header = 0) for f in files))
    #if 'bblid' not in df.columns:
    #    df = df.rename(columns={'/scripts/idcols.py':'bblid'})
    df.to_csv(output_dir + '/' + datatype + '_' + datetime.today().strftime('%Y-%m-%d') + '.csv', index=False)
