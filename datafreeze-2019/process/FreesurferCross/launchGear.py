### Launch freesurfer longitudinal gear to CUBIC
###
### Ellyn Butler
### April 22, 2020 - July 1, 2020

import flywheel
import datetime


fw = flywheel.Client()
project = fw.projects.find_first("label=ExtraLong") #project.info says GRMPY

now = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M")

fmriprep = fw.lookup('gears/fmriprep-hpc/0.3.4_20.0.5') # Latest version as of April 27, 2020

analysis_label = 'FreesurferCross_{}_{}_{}'.format(now, fmriprep.gear.name,
    fmriprep.gear.version)

inputs = {"freesurfer_license": project.files[0]}
fs_data = inputs['freesurfer_license'].read().decode() # May not be necessary

config_anatonly_cross = {'longitudinal': False, 'anat_only': True,
    'FREESURFER_LICENSE': fs_data, 'bold2t1w_dof': 6}
    # April 10, 2020: last argument only necessary because there is currently an
    # error in the way the manifest is being parsed

analysis_ids = []
fails = []
sessions_to_run = project.sessions()

sessions_to_run = sessions_to_run[2200:2341]
#0:200, 200:400, 400:600, 600:800, 800:1000, 1000:1200, 1200:1400, 1400:1600, 1600:1800, 1800:2200

for ses in sessions_to_run:
    try:
        _id = fmriprep.run(analysis_label=analysis_label,
            config=config_anatonly_cross, inputs=inputs, destination=ses)
        analysis_ids.append(_id)
    except Exception as e:
        print(e)
        fails.append(ses)

#jobs = fw.jobs.find('state=pending,gear_info.name="fmriprep-hpc",destination.type="analysis"', limit=200)

jobs = fw.get_current_user_jobs(gear='fmriprep-hpc')
jobs['stats']


######## Find sessions with no complete fmripreps version 0.3.4_20.0.5 #######

# sessions_to_run[0]... no analyses 'Label': 'PNC2', 'Subject': '86486'
project = fw.lookup('bbl/ExtraLong')
gear_name = 'fmriprep-hpc'
gear_version = '0.3.4_20.0.5'
sessions_to_reprocess = []
for s in project.sessions.iter():
    s = s.reload()   # reload is required to load the analyses attached to the session
    match_found = False
    for a in s.analyses:
        if a.gear_info.name == gear_name and a.gear_info.version == gear_version and a.job.state == 'complete':
            match_found = True
            break
    if not match_found:
        sessions_to_reprocess.append(s)

analysis_ids = []
fails = []
for ses in sessions_to_reprocess:
    try:
        _id = fmriprep.run(analysis_label=analysis_label,
            config=config_anatonly_cross, inputs=inputs, destination=ses)
        analysis_ids.append(_id)
    except Exception as e:
        print(e)
        fails.append(ses)

######## Get analysis id for a failed job
failedjobs = {}
jobs['jobs'][200]
for job in jobs['jobs']:
    if job['gear_info']['version'] == '0.3.4_20.0.5' and job['state'] == 'failed':
        for file in job['saved_files']:
            if 'ses-PNC1' in file and 'nii.gz' in file:
                failedjobs[file] = job['_id']
                break
