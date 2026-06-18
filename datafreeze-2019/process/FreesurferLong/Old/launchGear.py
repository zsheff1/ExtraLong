### Launch freesurfer longitudinal gear to CUBIC
###
### Ellyn Butler
### February 4, 2020 - February 5, 2020

import flywheel
import datetime


fw = flywheel.Client()
project = fw.projects.find_first("label=ExtraLong") #project.info says GRMPY

now = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M")

fmriprep = fw.lookup('gears/fmriprep-hpc/0.3.2_20.0.5') # Latest version as of April 10, 2020

analysis_label = 'FreesurferLong_{}_{}_{}'.format(now, fmriprep.gear.name,
    fmriprep.gear.version)

inputs = {"freesurfer_license": project.files[0]}
fs_data = inputs['freesurfer_license'].read().decode()

config_anatonly_longitudinal = {'longitudinal': True, 'anat_only': True,
    'FREESURFER_LICENSE': fs_data, 'bold2t1w_dof': 6}
    # April 10, 2020: last argument only necessary because there is currently an error in the manifest

# Run the gear on one subject
subjects_to_run = []
for subject in project.subjects():
    subjects_to_run.append(subject)
    if subject['code'] == 'sub-100088':
        subject_to_run = subject

_id = fmriprep.run(analysis_label=analysis_label,
                          config=config_anatonly_longitudinal, inputs=inputs, destination=subject_to_run)

jobs = fw.jobs.find('state=pending,gear_info.name="fmriprep-hpc",destination.type="analysis"', limit=50)

for job in fw.jobs.iter_find('state=pending'):
    print('Job: {}, Gear: {}'.format(job.id, job.gear_info.name))
