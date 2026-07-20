# FreeSurfer 8.2.0 Workflow
This workflow performs cross-sectional and longitudinal structural MRI processing using FreeSurfer 8.2.0. T1-weighted anatomical images are first processed independently with `recon-all`, after which subject-specific longitudinal base templates are created for participants with multiple sessions and used to generate longitudinal reconstructions. The workflow then computes quality control metrics, hippocampal and amygdala subregion segmentations, local gyrification index (LGI) maps, and regional summary statistics before compiling all measurements into tabular outputs for downstream statistical analysis.
## `01_cross_sectional.sh`
Generates and submits LSF jobs to run FreeSurfer cross-sectional processing (`recon-all -all`) for every T1-weighted anatomical image in the BIDS dataset. The script automatically discovers all `sub-*/ses-*/anat/*T1w.nii.gz` images, creates a job script for each subject-session pair, and submits it to the cluster using an Apptainer FreeSurfer 8.2.0 container.

**Output:**
- Cross-sectional FreeSurfer reconstructions: `derivatives/freesurfer/sub-*_ses-*/`
- LSF job scripts in `code/jobscripts/freesurfer/01_cross_sectional/`
- Job logs in `code/logs/freesurfer/01_cross_sectional/`
## `02_create_template.sh`
Generates and submits LSF jobs to create FreeSurfer longitudinal base templates for subjects with multiple cross-sectional sessions. The script identifies subjects with more than one `sub-*_ses-*` FreeSurfer directory, builds the list of timepoints, and submits a `recon-all -base` job for each subject using an Apptainer FreeSurfer 8.2.0 container.

**Output:**
- Longitudinal base templates: `derivatives/freesurfer/sub-*/`
- LSF job scripts in `code/jobscripts/freesurfer/02_create_template/`
- Job logs in `code/logs/freesurfer/02_create_template/`
## `03_longitudinal.sh`
Generates and submits LSF jobs to run FreeSurfer longitudinal processing (`recon-all -long`) for each cross-sectional session using its corresponding subject-specific base template. The script identifies all base templates and associated cross-sectional reconstructions, then submits one longitudinal processing job per subject-session pair using an Apptainer FreeSurfer 8.2.0 container.

**Output:**
- Longitudinal FreeSurfer reconstructions: `derivatives/freesurfer/sub-*_ses-*.long.sub-*`
- LSF job scripts in `code/jobscripts/freesurfer/03_longitudinal/`
- Job logs in `code/logs/freesurfer/03_longitudinal/`
## `04_write_subjectsfile.sh`
Creates a `subjectsfile.txt` containing the FreeSurfer subject directories to include in downstream analyses. The script preferentially includes longitudinal reconstructions (`sub-*_ses-*.long.sub-*`) when a corresponding base template exists and falls back to cross-sectional reconstructions for subjects with only a single session.

**Output:**
- `derivatives/freesurfer/subjectsfile.txt`
## `05_euler_number.sh`
Generates and submits a single LSF job to compute Euler numbers for each cross-sectional FreeSurfer reconstruction. The script runs `mris_euler_number` on each hemisphere’s `orig.nofix` surface and writes the results to a CSV table.

**Output:**
- `derivatives/freesurfer/tables/euler_number.csv`
## `06_hippocampus_amygdala.sh`
Generates and submits LSF jobs to run FreeSurfer hippocampus and amygdala subregion segmentation. The script uses `subjectsfile.txt` to run `segment_subregions`, processing either longitudinal base templates for multi-session subjects or cross-sectional reconstructions for single-session subjects.

**Output:**
- Hippocampus and amygdala subregion segmentation outputs in `derivatives/freesurfer/{subject}/mri/`
- LSF job scripts in `code/jobscripts/freesurfer/06_hippocampus_amygdala/`
- Job logs in `code/logs/freesurfer/06_hippocampus_amygdala/`
## `07_local_gyrification_index.sh`
Generates and submits LSF jobs to compute the local gyrification index (LGI) for each FreeSurfer reconstruction. The script uses `subjectsfile.txt` to run `recon-all -localGI` on longitudinal reconstructions for multi-session subjects or cross-sectional reconstructions for single-session subjects.

**Output:**
- Local gyrification index maps: `derivatives/freesurfer/{subject}/surf/{hemisphere}.pial_lgi`
- LSF job scripts in `code/jobscripts/freesurfer/07_local_gyrification_index/`
- Job logs in `code/logs/freesurfer/07_local_gyrification_index/`
## `08_segs_to_stats.sh`
Generates and submits LSF jobs to summarize local gyrification index (LGI) maps into region-wise statistics. The script uses `mri_segstats` to compute average LGI values for each cortical region defined by the Desikan–Killiany atlas and writes the results to FreeSurfer `.stats` files for each subject.

**Output:**
- Regional LGI statistics in `derivatives/freesurfer/{subject}/stats/{hemisphere}.aparc.pial_lgi.stats`
- LSF job scripts in `code/jobscripts/freesurfer/08_segs_to_stats/`
- Job logs in `code/logs/freesurfer/08_segs_to_stats/`
## `09_stats_to_tables.sh`
Generates and submits a single LSF job to compile FreeSurfer outputs into tabular files for downstream analysis. The script extracts cortical, subcortical, white matter, local gyrification index (LGI), and hippocampal/amygdala subregion measurements from all subjects listed in `subjectsfile.txt`.

**Output:**
- Tabulated FreeSurfer measurements in `derivatives/freesurfer/tables/`, including cortical (`aparc`), subcortical (`aseg`), white matter (`wmparc`), local gyrification index (LGI), and hippocampal/amygdala subregion summary tables.
