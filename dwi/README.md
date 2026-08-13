# Diffusion-Weighted Imaging Workflow
This workflow preprocesses diffusion-weighted MRI data with QSIPrep and derives diffusion tensor measures for both regional and voxelwise analyses. QSIPrep outputs are reoriented and padded for compatibility with FSL, after which diffusion tensors are estimated using `dtifit` and converted into DTI-TK tensor images. Quality control measures are calculated from the diffusion data, including volume counts and b=0 temporal signal-to-noise ratio (tSNR). A representative set of tensor images is selected across predefined age and sex bins and used to construct a study-specific DTI-TK population template. All subject-session tensor images are then registered to this template using rigid, affine, and diffeomorphic tensor-based registration.. The registered tensors are then used to derive template-space fractional anisotropy (FA), axial diffusivity (AD), radial diffusivity (RD), and mean diffusivity (MD) maps for each subject-session.

The registered diffusion metrics are subsequently prepared for complementary region-wise and voxelwise analyses. JHU ICBM white matter atlases are registered to the study-specific template and separated into individual tract and label masks, which are used to extract regional diffusion measurements for each subject-session pair. In parallel, subject-level diffusion maps are merged into 4D volumes and processed using the FSL tract-based spatial statistics (TBSS) framework to generate a common white matter skeleton and skeletonized FA, AD, MD, and RD images. A final quality control step adapted from the ENIGMA DTI pipeline summarizes each scan's mean projection distance to the common FA skeleton.
## [`01_qsiprep.sh`](01_qsiprep.sh)
Generates and submits LSF jobs to preprocess diffusion-weighted MRI data using QSIPrep. The script identifies all subjects with available DWI data and submits one participant-level job per subject using an Apptainer QSIPrep container. Processing is restricted to diffusion data and uses the configured output resolution and parallelization settings.

**Output:**
  - Preprocessed QSIPrep diffusion derivatives in the configured DWI output directory
  - LSF job scripts in `code/jobscripts/dwi/01_qsiprep/`
  - Job logs in `code/logs/dwi/01_qsiprep/`
## [`02_qsiprep_to_fsl.sh`](02_qsiprep_to_fsl.sh)
Generates and submits LSF jobs to prepare QSIPrep diffusion outputs for downstream FSL processing. For each subject-session pair with preprocessed diffusion data, the script reorients the diffusion image and brain mask to RPI orientation and pads both images using AFNI utilities.

**Output:**
  - RPI-oriented diffusion images: `derivatives/dwi/sub-*/ses-*/dwi/*_space-ACPC_desc-rpi_dwi.nii.gz`
  - RPI-oriented brain masks: `derivatives/dwi/sub-*/ses-*/dwi/*_space-ACPC_desc-rpi_mask.nii.gz`
  - Padded diffusion images: `derivatives/dwi/sub-*/ses-*/dwi/*_space-ACPC_desc-pad_dwi.nii.gz`
  - Padded brain masks: `derivatives/dwi/sub-*/ses-*/dwi/*_space-ACPC_desc-pad_mask.nii.gz`
  - LSF job scripts in `code/jobscripts/dwi/02_qsiprep_to_fsl/`
  - Job logs in `code/logs/dwi/02_qsiprep_to_fsl/`
## [`03_dtifit.sh`](03_dtifit.sh)
Generates and submits LSF jobs to fit a diffusion tensor model to each padded diffusion image using FSL dtifit. For each subject-session pair, the script uses the diffusion image, brain mask, and corresponding b-values and b-vectors to estimate diffusion tensor metrics for downstream registration and analysis.

**Output:**
  - Diffusion tensor parameter maps in `derivatives/dwi/sub-*/ses-*/dwi/`, including fractional anisotropy (FA), mean diffusivity (MD), eigenvalue, and eigenvector maps
  - LSF job scripts in `code/jobscripts/dwi/03_dtifit/`
  - Job logs in `code/logs/dwi/03_dtifit/`
## [`04_fsl_to_dtitk.sh`](04_fsl_to_dtitk.sh)
Generates and submits LSF jobs to prepare diffusion tensor images for DTI-TK registration. For each subject-session pair with completed tensor fitting, the script converts the FSL eigenvalue and eigenvector outputs into a DTI-TK tensor volume, scales the tensors, enforces positive-definite tensors, and standardizes the image origin for downstream tensor-based registration.

**Output:**
  - DTI-TK tensor images: `derivatives/dwi/sub-*/ses-*/dwi/sub-*_ses-*.nii.gz`
  - LSF job scripts in `code/jobscripts/dwi/04_fsl_to_dtitk/`
  - Job logs in `code/logs/dwi/04_fsl_to_dtitk/`
## [`05_qc_volumes_tsnr.sh`](05_qc_volumes_tsnr.sh)
Computes diffusion MRI quality control metrics for each subject-session pair. The script records the number of volumes in each preprocessed diffusion image and calculates the temporal signal-to-noise ratio (tSNR) of the b=0 images from the raw diffusion data, compiling both measures into CSV tables for downstream quality assessment.

**Output:**
  - Diffusion volume counts: `derivatives/dwi/qc/volumes.csv`
  - b=0 temporal signal-to-noise ratios: `derivatives/dwi/qc/tsnr_b0.csv`
## [`06_template_select.sh`](06_template_select.sh)
Prepares diffusion images for construction of the DTI-TK population template using the selections defined in `selection.csv`. For each template bin, the script either copies a predefined DTI-TK tensor image directly into the template build directory or, when multiple candidate images are available, submits an LSF job to preprocess and register their FA maps using the FSL TBSS workflow for template selection.

**Output:**
  - Preselected DTI-TK tensor images in the template build directory
  - TBSS template-selection outputs for candidate images in the template selection directory
  - LSF job scripts in `code/jobscripts/dwi/06_template_select/`
  - Job logs in `code/logs/dwi/06_template_select/`
## [`07_template_build.sh`](07_template_build.sh)
Builds the DTI-TK population template from the images selected by [`06_template_select.sh`](06_template_select.sh). The script collects the selected tensor image from each template bin, compiles the resulting images into a subject list, and submits a single LSF job to bootstrap the tensor template using DTI-TK.

**Output:**
  - DTI-TK population template: `derivatives/dwi/template/template.nii.gz`
  - Template brain mask: `derivatives/dwi/template/template_mask.nii.gz`
  - List of tensor images used to build the template
  - LSF job script in `code/jobscripts/dwi/07_template_build.sh`
  - Job logs in `code/logs/dwi/07_template_build/`
## [`08_registration.sh`](08_registration.sh)
Generates and submits LSF jobs to register each subject-session diffusion tensor image to the DTI-TK population template. The script performs rigid, affine, and diffeomorphic tensor-based registration, warps each tensor image into template space, and derives template-space fractional anisotropy (FA), axial diffusivity (AD), radial diffusivity (RD), and mean diffusivity (MD) maps for downstream analysis.

**Output:**
  - Template-space diffusion tensor images: `derivatives/dwi/sub-*/ses-*/dwi/sub-*_ses-*_diffeo.nii.gz`
  - Template-space FA, AD, RD, and MD maps in `derivatives/dwi/sub-*/ses-*/dwi/`
  - LSF job scripts in `code/jobscripts/dwi/08_registration/`
  - Job logs in `code/logs/dwi/08_registration/`
## [`09_merge.sh`](09_merge.sh)
Generates and submits a single LSF job to prepare template-space diffusion metrics for voxelwise and region-wise analyses. The script compiles all registered tensor images, computes a mean diffusion tensor and corresponding mean FA image, creates an FA-based analysis mask, and merges the template-space axial diffusivity (AD), fractional anisotropy (FA), mean diffusivity (MD), and radial diffusivity (RD) maps across subjects into separate 4D volumes.

**Output:**
  - List of registered tensor images: `derivatives/dwi/stats/subs.txt`
  - Mean diffusion tensor: `derivatives/dwi/stats/mean_tensor.nii.gz`
  - Mean FA image and analysis mask: `derivatives/dwi/stats/mean_FA.nii.gz` and `mean_FA_mask.nii.gz`
  - Merged 4D diffusion metric images: `derivatives/dwi/stats/all_{AD,FA,MD,RD}.nii.gz`
  - LSF job script in `code/jobscripts/dwi/09_merge.sh`
  - Job logs in `code/logs/dwi/09_merge/`
## [`10_roi_generate.sh`](10_roi_generate.sh)
Generates and submits a single LSF job to create region-of-interest (ROI) masks in the DTI-TK population template space. The script registers the JHU ICBM FA atlas to the population mean FA image using rigid, affine, and nonlinear ANTs registration, applies the resulting transforms to the JHU white matter tract and label atlases, and separates the transformed atlases into individual binary ROI masks for downstream regional analyses.

**Output:**
  - JHU atlas images transformed to population template space in the configured atlas directory
  - Individual binary tract and label ROI masks in the configured ROI directory
  - LSF job script in `code/jobscripts/dwi/10_roi_generate.sh`
  - Job logs in `code/logs/dwi/10_roi_generate/`
## [`11_roi_extract.sh`](11_roi_extract.sh)
Generates and submits LSF jobs to extract region-wise diffusion metrics from the template-space images for each subject-session pair. The script computes the mean axial diffusivity (AD), fractional anisotropy (FA), mean diffusivity (MD), and radial diffusivity (RD) within each tract and label ROI generated from the JHU atlases, and writes the measurements to subject-session CSV files for downstream analysis.

**Output:**
  - Region-wise diffusion measurements in `derivatives/dwi/stats/roi/sub-*_ses-*.csv`
  - LSF job scripts in `code/jobscripts/dwi/11_roi_extract/`
  - Job logs in `code/logs/dwi/11_roi_extract/`
## [`12_tbss.sh`](12_tbss.sh)
Generates and submits a single LSF job to prepare template-space diffusion metrics for tract-based spatial statistics (TBSS). The script creates the mean FA skeleton, projects the merged FA data onto the skeleton using the configured FA threshold, and applies the same projection to the axial diffusivity (AD), mean diffusivity (MD), and radial diffusivity (RD) images for downstream voxelwise analysis.

**Output:**
  - Mean FA skeleton and associated TBSS projection files in `derivatives/dwi/stats/`
  - Skeletonized images: `derivatives/dwi/stats/all_{AD,FA,MD,RD}_skeletonised.nii.gz`
  - LSF job script in `code/jobscripts/dwi/12_tbss.sh`
  - Job logs in `code/logs/dwi/12_tbss/`
## [`13_qc_proj_dist.sh`](13_qc_proj_dist.sh)
Computes an ENIGMA-based TBSS quality control metric for each subject-session pair by measuring the mean projection distance between each template-space FA image and the mean FA skeleton. Adapted from the ENIGMA DTI quality control pipeline, the script uses the TBSS distance map and skeleton mask to summarize how far subject-level FA values must be projected onto the common white matter skeleton, providing a measure of registration and skeleton alignment quality.

**Output:**
  - Mean projection distances: `derivatives/dwi/qc/proj_dist.csv`
