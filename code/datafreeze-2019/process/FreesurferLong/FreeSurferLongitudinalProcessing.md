# Longitudinal Processing with FreeSurfer 7.1.1

For more information see: 
https://surfer.nmr.mgh.harvard.edu/fswiki/LongitudinalProcessing

## **Workflow for Longitudinal Processing**

### 1. For each _session/timepoint_, cross-sectionally process using default recon-all.

```
  recon-all -s <tpNid> -i path_to_tpN_dcm -all
```
Provide:  
▪ `tpNid`: session_id for time point _N_  
▪ `path_to_tpN_dcm`: path to T1w scan from time point _N_

_This is accomplished by the first script, `run_cross_sectional.sh`_  
<br> 
### 2. For each _subject_, create unbiased template from average of all sessions/time point using -base flag.
```
  recon-all -base <templateid> -tp <tp1id> -tp <tp2id> ... -all
```
Provide:\
    ▪ `templateid`: name of new average template to be created for this subject\
    ▪ `tpNid`: session_id for timepoint _N_. Pass in all tpids 1 ... _N_ for the subject. 

_This is accomplished by the second script, `run_template_creation.sh`_  
<br>

### 3. For each _session/timepoint_, longitudinally process with respect to the subject's average template using -long flag.
```
  recon-all -long <tpNid> <templateid> -all
```
Provide:  
▪ `tpNid`: session_id for timepoint _N_  
▪ `templateid`: name of average template for the subject, created in previous step.

_This is accomplished by the third script, `run_longitudinal.sh`_

## **QC on Longitudinally-Processed Data**
 _**Goal**: Assess the quality of the single-subject templates._
### 4. For each subject, run `FreeQC` on the average template (SST) created in step two of the longitudinal processing stream.
```
SINGULARITYENV_SURFER_FRONTDOOR=1 \
    singularity run --writable-tmpfs --cleanenv \
    -B <path_to_Template-*_dir>:/input/data \
    -B <path_to_license>:/opt/freesurfer/license.txt \
    -B <path_to_subj_output_dir>:/output \
    <path_to_image_dir>/freeqc_0.0.14.sif \
    --subject <subj_label> --session ses-Template
```
_FreeQC jobs are launched by the script, `run_freeqc_on_templates.sh`_
