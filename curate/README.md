# BIDS Curation Workflow
This workflow collects T1w structural MRI images for the PNC Extra Long dataset and organizes them into a BIDS dataset. Expected scans are identified from `imglook.csv`, matched to available images on `bblsub2` and Flywheel, and then copied or downloaded with their corresponding JSON sidecars. Scans which are not in BIDS format on Flywheel are downloaded as session archives and curated locally.
## [`01_build_dataset.py`](01_build_dataset.py)
Identifies the expected scans by querying `imglook.csv` for PNC `bblid`s. Scans are excluded in the context of ineligible participants, invalid scans, images from clinical trials, and images collected on 7T scanners. The script searches configured local datasets using `LocalSource`, then searches configured Flywheel projects using `FlywheelSource` for scans that were not found locally. These scans are placed into a common BIDS directory structure. This script is meant to update the previous Extra Long 2021 Data Freeze and does not add new sessions to the dataset acquired before 2021-06-30.

Subject and session identifiers are standardized to six-digit `bblid` and five-digit `scanid`, respectively. When multiple T1w images are available for the same session in Flywheel, the most recently acquired image is retained. Corresponding JSON sidecars are included when available. Scans which are not in BIDS format on Flywheel are downloaded as session archives in `scratch/` and a job is submitted to convert them to BIDS format using HeuDiConv 1.4.0 in an isolated Apptainer container. Projects are processed with project-specific heuristics.

**Output:**
- T1w images: `sub-*/ses-*/anat/sub-*_ses-*_T1w.nii.gz`
- T1w JSON sidecars: `sub-*/ses-*/anat/sub-*_ses-*_T1w.json`

## [`02_summary_files.py`](02_summary_files.py)
Generates BIDS participant-, session-, and scan-level summary files for the curated dataset. The script identifies all subject-session directories, joins them with demographic data from `subject.csv` and scan dates from `imglook.csv`, and calculates age at each session in completed months. Participant-level demographic variables include sex, race, ethnicity, and handedness, with unavailable values recorded as `n/a`.

For each participant, the script creates a sessions file containing the session identifier and age. For each session, it updates the scans file to include all NIfTI images present in the dataset. When acquisition times are missing, they are recovered from the corresponding JSON sidecars when possible. Acquisition dates are anonymized using an assumed date of birth of 1900-01-01 and the participant's age at the session, while preserving the original acquisition time. Existing summary files are removed before the updated TSV files are written, and predefined JSON sidecars are copied into the dataset root.

**Output:**
- Participants Summary File: `participants.tsv`
- Participants Sidecar: `participants.json`
- Sessions Summary Files: `sub-*/sub-*_sessions.tsv`
- Sessions Sidecar: `sessions.json`
- Scans Summary Files: `sub-*/ses-*/sub-*_ses-*_scans.tsv`
- Scans Sidecar `scans.json`

## [`03_validate.sh`](03_validate.sh)
Validates the curated BIDS dataset using the BIDS Validator. Validation settings are defined in `code/curate/assets/bids_validator_config.json`, and the results are saved as a machine-readable JSON report with corresponding standard output and error logs. NIfTI header validation is skipped.

**Output:**
- BIDS Validator report: `code/logs/curate/03_validate/03_validate.json`
