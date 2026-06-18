### This script combines the summary structural values into one csv (ANTsLongCT)
###
### Ellyn Butler
### March 29, 2021

import glob
import csv
import pandas as pd
from datetime import datetime


files = glob.glob('/project/ExtraLong/data/corticalThickness/antslongct4/sub*/ses*/*struc.csv')
df = pd.concat((pd.read_csv(f, header = 0) for f in files))
df.to_csv('/project/ExtraLong/data/corticalThickness/tabulated/antslong_struc_'+datetime.today().strftime('%Y-%m-%d')+'.csv', index=False)
