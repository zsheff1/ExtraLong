'''
Heuristic to curate MIND_ T1w scans.
'''

##################### Create keys for each acquisition type ####################

def create_key(template, outtype=('nii.gz',), annotation_classes=None):
    if template is None or not template:
        raise ValueError('Template must be a valid format string')
    return template, outtype, annotation_classes

t1w = create_key('sub-{subject}/{session}/anat/sub-{subject}_{session}_T1w')

############################ Define heuristic rules ############################

def infotodict(seqinfo):
    """Heuristic evaluator for determining which runs belong where
    allowed template fields - follow python string module:
    item: index within category
    subject: participant id
    seqitem: run number during scanning
    subindex: sub index within group
    """
    
    # Info dictionary to map series_id's to correct key
    info = {
        t1w: []
    }

    for s in seqinfo:
        if (s.protocol_name == "MPRAGE_P2_1mm") and (not s.is_derived):
            info[t1w].append(s.series_id)

    return info

################## Hardcode required params in MetadataExtras ##################

POPULATE_INTENDED_FOR_OPTS = {
    'matching_parameters': 'ModalityAcquisitionLabel',
    'criterion': 'Closest'
}