### This script assesses and records findings for the SSTs that still look bad
### using antssst v3 (directory antssst2), and were picked to be part of the
### group template (set 1).
###
### Ellyn Butler
### December 7, 2020

library('neurobase')

# sub-93517 -> a little fuzzy
# 1. How does session 1 look? Tiniest bit of ringing, and a bit fuzzy
img1 = readNIfTI2('~/Documents/ExtraLong/data/freesurferCrossSectional/fmriprep/sub-93517/ses-10932/anat/sub-93517_ses-10932_desc-preproc_T1w.nii.gz')
# 2. How does session 2 look? Tiniest bit fuzzy
img2 = readNIfTI2('~/Documents/ExtraLong/data/freesurferCrossSectional/fmriprep/sub-93517/ses-PNC1/anat/sub-93517_ses-PNC1_desc-preproc_T1w.nii.gz')
# 3. Similar distributions? ~~~~NO~~~~
mean(img1) # 3185.95
sd(img1) # 4331.906
mean(img2) # 501.5639
sd(img2) # 705.0514
# 4. Same study? No
# 5. Same person? Seems likely (visually compared images)


# sub-101299 -> fuzzy
# 1. How does session 1 look? Very good
img1 = readNIfTI2('~/Documents/ExtraLong/data/freesurferCrossSectional/fmriprep/sub-101299/ses-PNC1/anat/sub-101299_ses-PNC1_desc-preproc_T1w.nii.gz')
# 2. How does session 2 look? Tiny bit of ringing
img2 = readNIfTI2('~/Documents/ExtraLong/data/freesurferCrossSectional/fmriprep/sub-101299/ses-PNC2/anat/sub-101299_ses-PNC2_desc-preproc_T1w.nii.gz')
# 3. Similar distributions? Yes
mean(img1) # 649.5652
sd(img1) # 939.223
mean(img2) # 747.8899
sd(img2) # 996.1454
# 4. Same study? Yes (PNC)
# 5. Same person? Seems likely (visually compared images)

# sub-113340 -> skulls aren’t lining up
# 1. How does session 1 look? Good
img1 = readNIfTI2('~/Documents/ExtraLong/data/freesurferCrossSectional/fmriprep/sub-113340/ses-PNC1/anat/sub-113340_ses-PNC1_desc-preproc_T1w.nii.gz')
# 2. How does session 2 look? Good
img2 = readNIfTI2('~/Documents/ExtraLong/data/freesurferCrossSectional/fmriprep/sub-113340/ses-PNC2/anat/sub-113340_ses-PNC2_desc-preproc_T1w.nii.gz')
# 3. Similar distributions? Kind of
mean(img1) # 995.7405
sd(img1) # 1496.122
mean(img2) # 1211.232
sd(img2) # 1854.129
# 4. Same study? Yes (PNC)
# 5. Same person? Seems likely, odd shape to skull (visually compared images)

# sub-122732 -> skulls aren’t lining up... NOT CLEAR WHY SO BAD (only guess is bc skull is chopped at top)
# 1. How does session 1 look? Good
img1 = readNIfTI2('~/Documents/ExtraLong/data/freesurferCrossSectional/fmriprep/sub-122732/ses-PNC1/anat/sub-122732_ses-PNC1_desc-preproc_T1w.nii.gz')
# 2. How does session 2 look? Good, but top of skull cut off
img2 = readNIfTI2('~/Documents/ExtraLong/data/freesurferCrossSectional/fmriprep/sub-122732/ses-PNC2/anat/sub-122732_ses-PNC2_desc-preproc_T1w.nii.gz')
# 3. Similar distributions? Yes
mean(img1) # 623.0283
sd(img1) # 786.5469
mean(img2) # 684.5334
sd(img2) # 835.0052
# 4. Same study? Yes (PNC)
# 5. Same person? Seems likely (visually compared images)

# sub-87346 -> good, some ringing
# 1. How does session 1 look? Mild ringing
img1 = readNIfTI2('~/Documents/ExtraLong/data/freesurferCrossSectional/fmriprep/sub-87346/ses-10597/anat/sub-87346_ses-10597_desc-preproc_T1w.nii.gz')
# 2. How does session 2 look? Good
img2 = readNIfTI2('~/Documents/ExtraLong/data/freesurferCrossSectional/fmriprep/sub-87346/ses-PNC1/anat/sub-87346_ses-PNC1_desc-preproc_T1w.nii.gz')
# 3. Similar distributions? ~~~~NO~~~~
mean(img1) # 4034.148
sd(img1) # 5690.425
mean(img2) # 811.2403
sd(img2) #1189.354
# 4. Same study? No
# 5. Same person? Seems likely, both have giant ventricles for a young person (visually compared images)

# sub-91717 -> fuzzy
# 1. How does session 1 look? A tiny bit of ringing
img1 = readNIfTI2('~/Documents/ExtraLong/data/freesurferCrossSectional/fmriprep/sub-91717/ses-PNC1/anat/sub-91717_ses-PNC1_desc-preproc_T1w.nii.gz')
# 2. How does session 2 look? A little bit of ringing
img2 = readNIfTI2('~/Documents/ExtraLong/data/freesurferCrossSectional/fmriprep/sub-91717/ses-10878/anat/sub-91717_ses-10878_desc-preproc_T1w.nii.gz')
# 3. Similar distributions? ~~~~NO~~~~
mean(img1) # 576.7668
sd(img1) # 776.0688
mean(img2) # 5462.183
sd(img2) # 7048.39
# 4. Same study? No
# 5. Same person? Seems likely, ventricles similar shape (visually compared images)

# sub-94144 -> good, but fuzzy spots
# 1. How does session 1 look? Good
img1 = readNIfTI2('~/Documents/ExtraLong/data/freesurferCrossSectional/fmriprep/sub-94144/ses-PNC1/anat/sub-94144_ses-PNC1_desc-preproc_T1w.nii.gz')
# 2. How does session 2 look? Some ringing in inferior frontal cortex
img2 = readNIfTI2('~/Documents/ExtraLong/data/freesurferCrossSectional/fmriprep/sub-94144/ses-PNC2/anat/sub-94144_ses-PNC2_desc-preproc_T1w.nii.gz')
# 3. Similar distributions? Yes
mean(img1) # 1241.663
sd(img1) # 1611.486
mean(img2) # 1195.297
sd(img2) # 1441.367
# 4. Same study? Yes (PNC)
# 5. Same person? Seems likely (visually compared images)

# sub-98425 -> gyri not quite lining up
# 1. How does session 1 look? Brain good, but skull a tiny bit warped
img1 = readNIfTI2('~/Documents/ExtraLong/data/freesurferCrossSectional/fmriprep/sub-98425/ses-PNC1/anat/sub-98425_ses-PNC1_desc-preproc_T1w.nii.gz')
# 2. How does session 2 look? Brain good, but skull warped
img2 = readNIfTI2('~/Documents/ExtraLong/data/freesurferCrossSectional/fmriprep/sub-98425/ses-PNC2/anat/sub-98425_ses-PNC2_desc-preproc_T1w.nii.gz')
# 3. Similar distributions?
mean(img1) # 567.6044
sd(img1) # 833.9948
mean(img2) # 763.9429
sd(img2) # 1165.418
# 4. Same study? Yes
# 5. Same person? Seems likely (visually compared images)


######################## EXCLUDE ALL FROM NEXT TEMPLATE ########################
