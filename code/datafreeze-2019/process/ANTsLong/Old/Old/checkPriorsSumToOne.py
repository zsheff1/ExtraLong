### This script check that priors sum to 1 in every voxel that is brain
### (i.e., all voxels should sum to 0 or 1)
###
### Ellyn Butler
### February 3, 2021

import nibabel as nib
import numpy as np
import pandas as pd
import os
from copy import deepcopy
import matplotlib.pyplot as plt

# List the available aseg images
basedir = '/Users/butellyn/Documents/ExtraLong/data/groupTemplates/versionEleven/'

gmcort = nib.load(basedir+'GMCortical_NormalizedtoExtraLongTemplate_averageMask.nii.gz').get_fdata()
wmcort = nib.load(basedir+'WMCortical_NormalizedtoExtraLongTemplate_averageMask.nii.gz').get_fdata()
csf = nib.load(basedir+'CSF_NormalizedtoExtraLongTemplate_averageMask.nii.gz').get_fdata()
gmdeep = nib.load(basedir+'GMDeep_NormalizedtoExtraLongTemplate_averageMask.nii.gz').get_fdata()
bstem = nib.load(basedir+'Brainstem_NormalizedtoExtraLongTemplate_averageMask.nii.gz').get_fdata()
cereb = nib.load(basedir+'Cerebellum_NormalizedtoExtraLongTemplate_averageMask.nii.gz').get_fdata()


sum_priors = gmcort+wmcort+csf+gmdeep+bstem+cereb
len(np.unique(sum_priors))#Oops... Not all zero and 1

# How far off from 0 and 1?
#np.histogram(sum_priors)

np.amax(sum_priors) # 1
np.amin(sum_priors) # 0

# Check that all of the masks that comprise the priors are binary
masks = [mask for mask in os.listdir(basedir) if '_mask.nii.gz' in mask]

for mask in masks:
    img = nib.load(basedir+mask).get_fdata()
    print(mask+' '+str(np.amax(img)))
    print(mask+' '+str(np.amin(img)))

# Did the warping to the standard space cause the non-binariness? Yes
# If so, binarize the warped images and then average them

# Check add up to 1 now that fixed
np.unique(np.round(sum_priors, decimals=2))

# They aren't... maybe non 0 or 1's are on the boundary of brain and background
# Write out image to check this
img = nib.load(basedir+'GMCortical_NormalizedtoExtraLongTemplate_averageMask.nii.gz')
img = nib.Nifti1Image(sum_priors, affine=img.affine)
img.to_filename(basedir+'/sumpriors.nii.gz') #EEEK. Major space problem














#
