#!/usr/bin/env python3

import os
import pandas as pd
import re
import glob
import xmltodict
import logging

# Paths
INPUT_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi/stats/roi'
STATS_DIR = '/project/bbl_gur_evolpsy/derivatives/dwi/stats'
LOG = '/project/bbl_gur_evolpsy/code/logs/dwi/roi/roi_concat.log'
FSL_ATLAS_DIR = '/appl/fsl-6.0.3/data/atlases'

METRICS = ['ad', 'fa', 'md', 'rd']

ROI_PATTERN = re.compile(r'(labels|tracts)_\d{2}')
SUB_SES_PATTERN = re.compile(r'sub-\d+_ses-\w+\d')
METRIC_PATTERN = re.compile(r'(ad|fa|md|rd)(?=.txt)')

logging.basicConfig(
    datefmt = '%Y-%m-%dT%H:%M:%S%z',
    filename = LOG,
    format = '%(asctime)s %(levelname)s %(message)s',
    level = logging.DEBUG
)

# define value cleaner functions
logging.debug('defining values cleaner functions')
def labels_values_cleaner(value):
    value = value.lower()
    value = value.replace('(column and body of fornix)', 'column body')
    value = value.replace('(cres)', 'cres')
    value = value.replace('(cingulate gyrus)', 'cingulate gyrus')
    value = value.replace('(hippocampus)', 'hippocampus')
    value = re.sub(r'\([^)]*\)', '', value)
    value = value.replace('/', '')
    value = value.replace('limb of', '')
    value = value.replace('part of', '')
    value = value.replace('-', ' ')
    value = value.replace('  ', ' ')
    value = value.strip()
    value = value.replace(' ', '_')
    return value

def tracts_values_cleaner(value):
    value = value.lower()
    value = value.replace('part', '')
    value = value.replace('-', ' ')
    value = value.replace('(', '')
    value = value.replace(')', '')
    value = value.replace('  ', ' ')
    value = value.strip()
    value = value.replace(' ', '_')
    return value

logging.info('reading data')
combined_dict = {}
for raw_file in glob.glob(os.path.join(INPUT_DIR, '*')):
    sub_ses = SUB_SES_PATTERN.search(raw_file).group(0)
    metric = METRIC_PATTERN.search(raw_file).group(0)
    logging.debug(f'reading data for {sub_ses}_{metric}')
    if sub_ses not in combined_dict:
        combined_dict[sub_ses] = {}
    with open(raw_file) as file:
        for line in file:
            key_raw, value_raw = line.strip().split(':', 1)
            key = f'{ROI_PATTERN.search(key_raw).group(0)}_{metric}'
            value = float(value_raw.strip())
            combined_dict[sub_ses][key] = value

df = pd.DataFrame.from_dict(combined_dict, orient='index')
df = df.reset_index().rename(columns={'index': 'sub_ses'})

# break df into tracts and labels, rename columns, output to stats/ dir
logging.debug('splitting data by atlas')
for atlas_type, key_offset, value_cleaner in zip(['labels', 'tracts'], [0, 1], [labels_values_cleaner, tracts_values_cleaner]):
    logging.info(f'for {atlas_type}')
    sidecar_path = os.path.join(FSL_ATLAS_DIR, f'JHU-{atlas_type}.xml')
    logging.debug(f'reading atlas sidecar at {sidecar_path}')
    with open(sidecar_path) as file:
        atlas_sidecar = xmltodict.parse(file.read())
    for metric in METRICS:
        logging.debug('generating mapping to rename data columns')
        mapping = {
            f"{atlas_type}_{str(int(roi['@index'])+key_offset).zfill(2)}_{metric}":
            f"{value_cleaner(roi['#text'])}"
            for roi in atlas_sidecar['atlas']['data']['label']
        }
        logging.debug(f'generating index of columns for {atlas_type} data')
        col_idx = [(bool(re.search(atlas_type, column)) and bool(re.search(metric, column))) or bool(re.search('sub_ses', column)) for column in df.columns]
        logging.debug(f'subsetting and renaming {atlas_type} data')
        output = df.iloc[:, col_idx].rename(columns = mapping)
        output_path = os.path.join(STATS_DIR, f'dwi-roi_metric-{metric}_space-jhu-{atlas_type}.csv')
        logging.info(f'writing {atlas_type} data to {output_path}')
        output.to_csv(output_path, sep=',', index=False, header=True)
