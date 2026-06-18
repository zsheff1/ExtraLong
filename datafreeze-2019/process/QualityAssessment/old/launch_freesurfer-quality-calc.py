### This script attaches freesurfer output from fMRIPrep runs as an object
### in the config of a freesurfer-quality-calc run
###
### Ellyn Butler
### May 4, 2020 - May 5, 2020... August 18, 2020

import flywheel
import datetime
import pytz

fw = flywheel.Client()
proj = fw.lookup('bbl/ExtraLong')
sessions = proj.sessions()
sessions = [fw.get(x.id) for x in sessions]

#sessions[0].analyses[0]
#sessions[4].files[2].name

[(x.gear_info, x.job.state) for x in sessions[0].analyses] # check fmriprep

# This function loops through the analyses of a session, checks if `fmriprep`
# ran successfully, and returns the most recent successful `fmriprep` analysis.
def get_latest_fmriprep_correctversion(session, fmriprepVersion):
    if session.analyses:
        timezone = pytz.timezone("UTC")
        init_date = datetime.datetime(2018, 1, 1)
        latest_date = timezone.localize(init_date)
        latest_run = None

        for analysis in session.analyses:
            gear_name = analysis.gear_info['name']
            state = analysis.job.state
            date = analysis.created
            anal = analysis.label
            if 'fmriprep' in gear_name and date > latest_date and state =='complete' and fmriprepVersion in anal:
                latest_date = date
                latest_run = analysis

        if latest_run is not None:
            fmriprep_out = [x for x in latest_run.files if 'fmriprep' in x.name and x.mimetype == 'application/zip'][0]
            fmriprep_out
            return(fmriprep_out)
        else:
            return None
    else:
        return None


# get freesurfer zip
#def get_freesurferfile(session):
#    for analysis in session.analyses:
#        for thisfile in analysis.files:
#            if thisfile.name.endswith('.zip') and thisfile.name.startswith('fmriprep'): #Look at analysis label version instead
#                freesurferfile = thisfile
#        else:
#            freesurferfile =  None
#    return freesurferfile

#session = sessions[7]
#session.analyses[2].files[1].name

d = get_latest_fmriprep_correctversion(sessions[7], '0.3.4_20.0.5')

#d = get_freesurferfile(sessions[7])

# Now, we fetch freesurfer-quality-calc
fqc = fw.lookup('gears/freesurfer-quality-calc')
#eg = sessions[0]

#xcp.run(analysis_label=\"XCP_SDK_CBF_{}\".format(datetime.datetime.now()), destination=eg, inputs=myinput, config=myconfig)
#returns the jobID
fqc_runs = {}
for i, x in enumerate(sessions):
    ses = fw.get(x.id)
    #struc = get_latest_struct(ses)
    fmriprep = get_latest_fmriprep_correctversion(ses, '0.3.4_20.0.5')

    if  fmriprep:
        myinput = {
            'fmriprepdir': fmriprep,
            'session_label': ses.label
        }
        jobid = xcp.run(analysis_label="freesurfer-quality-calc_{}".format(datetime.datetime.now()), destination=ses, inputs=myinput)
        fqc_runs[ses.label] = jobid
    else:
        fqc_runs[ses.label] = None



    #import templateflow.api as tf
    #[str(tf.get('fsLR', space='fsaverage', suffix='sphere', hemi=hemi, density='164k'))
    #        for hemi in 'LR']
    #import templateflow.api as tf
    #[str(tf.get('fsLR', space='fsaverage', suffix='sphere', hemi=hemi, density='164k'))
    #        for hemi in 'LR']
    #[str(tf.get('fsLR', space='fsaverage', suffix='midthickness', hemi=hemi, density='164k'))
    #        for hemi in 'LR']
    #str(brain_mask)

















#
