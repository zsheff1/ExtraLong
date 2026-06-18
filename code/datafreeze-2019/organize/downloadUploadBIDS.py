# # Moving Data to New Project
# 3 Important rules to using the SDK:
# 1. Remember the data model: everything is either an object, or an attachment to an object.
# 2. Objects are nested hierarchically.
# 3. Operating on objects is different from operating on their attachments.


import subprocess as sub
import os
import flywheel
import json
import shutil
import re
import time
import pandas as pd

fw = flywheel.Client()


#def initialise_subject_list(source_proj):
#    source = fw.projects.find_first('label="{}"'.format(source_proj))
#    subs = source.subjects()
#    return [x.label for x in subs]


def wait_timeout(proc, seconds):
    """
    This function waits for a process to finish, or raise exception after timeout. Use it to kill and restart fw-heudiconv if it hangs
    Returns: True if it's been running longer than <seconds>, False otherwise
    """
    start = time.time()
    end = start + seconds
    interval = min(seconds / 1000.0, .25)
    while True:
        result = proc.poll()
        if result is not None:
            return False
        if time.time() >= end:
            proc.terminate()
            return True
        time.sleep(interval)


def download_subject(subj_label, source_proj, dest_path, acqs, folders):
    '''
    This function runs fw-heudiconv-export on a subject, using the wait_timeout function to kill and restart if it hangs.
    Modify the command as necessary
    '''
    command = ['fw-heudiconv-export', '--proj', source_proj, '--subject', subj_label, '--path', dest_path, '--folders']
    command.extend(folders)
    while True:
        print("Trying fw-heudiconv...")
        p = sub.Popen(command, stdout=sub.PIPE, stdin=sub.PIPE, stderr=sub.PIPE, universal_newlines=True)
        p_is_hanging = wait_timeout(p, 120)
        if not p_is_hanging:
            break


def tidy(path):
    '''
    This function tidies the BIDS directory that was downloaded.
    In this case, we renamed every ses-<label>, kept only T1s, fmaps, and rest scans, and fixed IntendedFors accordingly
    '''
    # get names
    print("Tidying BIDS Directory...")
    fnames = [ os.path.join(parent, name) for (parent, subdirs, files) in os.walk('{}/bids_directory/'.format(path)) for name in files + subdirs ]
    #fnames2 = [f.replace("ses-1", "ses-PNC") for f in fnames]
    # copy all to new session label
    for n in range(len(fnames)):
        os.makedirs(fnames[n])
        #if not os.path.exists(fnames2[n]):
        #    if os.path.isdir(fnames[n]):
        #        os.makedirs(fnames2[n])
        #    else:
        #        shutil.copy2(fnames[n], fnames2[n])
    # delete old session label files
    #for f in fnames:
    #    if "ses-1" in f and os.path.exists(f):
    #        shutil.rmtree(f)
    # delete unwanted tasks, only keep rest
    for f in fnames2:
        if re.search(r"task-(?!rest)", f) is not None and os.path.isfile(f):
            os.remove(f)
    # fix json sidecars of fieldmaps to only have rest intendedfor
    for f in fnames2:
        if f.endswith('.json') and os.path.isfile(f):
            with open(f, 'r') as data:
                json_data = json.load(data)
            if 'IntendedFor' in json_data.keys():
                json_data['IntendedFor'] = [x.replace("ses-1", "ses-PNC") for x in json_data["IntendedFor"] if re.search(r"task-(?=rest)", x) is not None]
                with open(f, 'w') as fixed:
                    json.dump(json_data, fixed, indent = 4)


def upload_subject(path, dest_proj):
    #tidy(path) #optional of course
    print("Uploading subject data...")
    p2 = sub.Popen(['fw', 'import', 'bids', '--project', dest_proj, '{}/bids_directory/'.format(path), 'bbl'], stdout=sub.PIPE, stdin=sub.PIPE, stderr=sub.PIPE, universal_newlines=True)
    out, err = p2.communicate(input="yes\n")
    print(out)
    p3 = sub.Popen(['rm', '-rf', 'bids_directory/'], stdout=sub.PIPE, stdin=sub.PIPE, stderr=sub.PIPE, universal_newlines=True)


def main():
    projects = ["GRMPY_822831"]
        #TODO:,"PNC_LG_810336", ]
        #DONE: "AGGY_808689", "CONTE_815814", "GRMPY_822831", "MOTIVE","ONM_816275", "NODRA_816281","DAY2_808799", "SYRP_818621", "NEFF_818028", "FNDM1_810211", "FNDM2_810211", "PNC_CS_810336"
    for proj in projects:
        print("Gathering subject list for "+proj+"...\n")
        #subjects = pd.read_csv("/Users/butellyn/Documents/bids_curation/ExtraLong/longbblids_"+proj+".csv") # Create these for each project
        #subjects2 = subjects["bblid"].tolist()
        print("Downloading subject data...\n")
        subjects2=[86486, 95257]
        for subj in subjects2:
            print("\n=============================")
            print("Processing subject {}".format(subj))
            subj=str(subj)
            download_subject(subj, proj, '.', 'T1w', ['anat']) # you probably only want the t1s
            upload_subject('.', 'ExtraLong') # modify as necessary


if __name__ == '__main__':
    main()
