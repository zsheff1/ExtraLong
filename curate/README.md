# BIDS Curation Workflow
This workflow collects T1w structural MRI images for the PNC Extra Long dataset and organizes them into a BIDS dataset. Expected scans are identified from `imglook.csv`, matched to available images on `bblsub2` and Flywheel, and then copied or downloaded with their corresponding JSON sidecars. Scans which are not in BIDS format on Flywheel are downloaded as session archives and curated locally.
## `01_build_dataset.py`
Identifies the expected scans by querying `imglook.csv` for PNC `bblid`s. Scans are excluded in the context of ineligible participants, invalid scans, images from clinical trials, and images collected on 7T scanners. The script searches configured local datasets using `LocalSource`, then searches configured Flywheel projects using `FlywheelSource` for scans that were not found locally. These scans are placed into a common BIDS directory structure. This script is meant to update the previous Extra Long 2021 Data Freeze and does not add new sessions to the dataset acquired before 2021-06-30.

Subject and session identifiers are standardized to six-digit `bblid` and five-digit `scanid`, respectively. When multiple T1w images are available for the same session in Flywheel, the most recently acquired image is retained. Corresponding JSON sidecars are included when available. Scans which are not in BIDS format on Flywheel are downloaded as session archives in `scratch/` for later BIDS conversion.

**Output:**
- T1w images: `sub-*/ses-*/anat/sub-*_ses-*_T1w.nii.gz`
- T1w JSON sidecars: `sub-*/ses-*/anat/sub-*_ses-*_T1w.json`
- Non-BIDS Flywheel sessions: `scratch/{project_label}/{bblid}_{scanid}/`
## `02_curate.sh`
Generates and submits LSF jobs to convert downloaded DICOM archives into a BIDS dataset using HeuDiConv 1.4.0. The script processes four source projects (22q Midline, MIND, PBN, RSVP) with project-specific heuristics, discovers each subject-session directory, standardizes subject and session identifiers using zero padding, and runs each conversion in an isolated Apptainer container.

**Output:**
- T1w images: `sub-*/ses-*/anat/sub-*_ses-*_T1w.nii.gz`
- T1w JSON sidecars: `sub-*/ses-*/anat/sub-*_ses-*_T1w.json`