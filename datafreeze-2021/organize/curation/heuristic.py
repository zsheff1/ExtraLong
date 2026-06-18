# File:     heuristic.py
# Date:     09/14/2021
# Desc:     BIDS curation heuristic for ExtraLong 2021.

import os
import string

#################################################################################
###############   Step 1: Create keys for each acquisition type   ###############
#################################################################################
projects = {
    "DAY2",
    "FNDM",
    "NEFF",
    "CONTE",
    "NODRA",
    "ONM",
    "SYRP",
    "AGGY",
    "MOTIVE",
    "GRMPY",
    "22QMID",
    "PNC",
    "EONSX",
    "EVOL"
}

def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return template, outtype, annotation_classes

keys = {}

for proj in projects:
    keys[proj] = create_key(
        "sub-{subject}/ses-{session}/anat/sub-{subject}_ses-{session}_acq-" + proj + "_T1w")

################################################################################# 
#######  Step 2: Define rules to map scans (based on their metadata) to  ########
#######  the correct BIDS filename (specified by keys you just created)  ########
#################################################################################

def infotodict(seqinfo):
    """Heuristic evaluator for determining which runs belong where
    allowed template fields - follow python string module:
    item: index within category
    subject: participant id
    seqitem: run number during scanning
    subindex: sub index within group
    """

    info = {}
    for proj in projects:
        info[keys[proj]] = []

    # Iterate through all scans in ExtraLong 2021 on Flywheel
    for s in seqinfo:
        proj = s.study_description
        info[keys[proj]].append(s.series_id)

    return info

################################################################################# 
#######  Step 3:   ########
#################################################################################

