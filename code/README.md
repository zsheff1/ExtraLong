# Extra Long

This repository stores all necessary scripts to identify to the sample of participants who have been seen at least twice across a variety of developmental projects at the Brain Behavior Laboratory, copy that data into a Flywheel project, and ultimately process and analyze said data.

The processing steps are as follows:
1. Run all subjects through fMRIPrep's (v20.0.5) implementation of Freesurfer (v6.0.1) to obtain quality metrics ('freeqc').
2. Inspect distributions of quality metrics, and use previously conducted hand-validation, to determine if scans should be included in the next processing step.
3. Construct single subject templates for all subjects with more than one scan remaining (antssst).
4. Run the ANTs Longitudinal Cortical Thickness pipeline (antslongcort).
5. Warp the Mind Boggle brains to the single subject templates and segment the individual scans to obtain structural metrics in the DKT atlas (antslongdkt).
