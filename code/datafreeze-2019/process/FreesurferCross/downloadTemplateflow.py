### This script downloads images from templateflow that are necessary for running
### fMRIPrep on PMACS
###
### Ellyn Butler
### October 27, 2020

from templateflow import api as tfapi

tfapi.TF_S3_ROOT = 'http://templateflow.s3.amazonaws.com'

tfapi.get('MNI152NLin6Asym', atlas=None, resolution=[1, 2],
    desc=None, extension=['.nii', '.nii.gz'])
tfapi.get('MNI152NLin6Asym', atlas=None, resolution=[1, 2],
    desc='brain', extension=['.nii', '.nii.gz'])
tfapi.get('MNI152NLin2009cAsym', atlas=None, extension=['.nii', '.nii.gz'])
tfapi.get('OASIS30ANTs', extension=['.nii', '.nii.gz'])
tfapi.get('fsaverage', density='164k', desc='std', suffix='sphere')
tfapi.get('fsaverage', density='164k', desc='vaavg', suffix='midthickness')
tfapi.get('fsLR', density='32k')
tfapi.get('MNI152NLin6Asym', resolution=2, atlas='HCP', suffix='dseg')
