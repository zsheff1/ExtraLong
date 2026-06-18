### This script creates a csv of flywheel meta data pertaining to scanning
### parameters.
###
### Ellyn Butler
### June 2, 2020


import flywheel
import datetime
import pandas as pd


fw = flywheel.Client()
project = fw.projects.find_first("label=ExtraLong") #project.info says GRMPY

params = {'bblid':[], 'seslabel':[], 'EchoTime':[], 'RepetitionTime':[],
    'FlipAngle':[], 'InPlanePhaseEncodingDirectionDICOM':[],
    'ManufacturersModelName':[], 'ProtocolName':[], 'SliceThickness':[]}
problems = []
for ses in project.sessions():
    bblid = ses['info']['BIDS']['Subject']
    seslabel = ses['info']['BIDS']['Label']
    acq = ses.acquisitions()
    if len(acq) < 2:
        metadata = fw.get(acq[0]['_id'])
        metainfo = metadata['files'][0]['info']
        if bblid not in params:
            if 'EchoTime' in metainfo:
                params['bblid'].append(bblid)
                params['seslabel'].append(seslabel)
                params['EchoTime'].append(metainfo['EchoTime'])
                params['RepetitionTime'].append(metainfo['RepetitionTime'])
                params['FlipAngle'].append(metainfo['FlipAngle'])
                params['InPlanePhaseEncodingDirectionDICOM'].append(metainfo['InPlanePhaseEncodingDirectionDICOM'])
                params['ManufacturersModelName'].append(metainfo['ManufacturersModelName'])
                params['ProtocolName'].append(metainfo['ProtocolName'])
                params['SliceThickness'].append(metainfo['SliceThickness'])
            else:
                problems.append([bblid, acq[0]['_id']])
    else:
        break

params_data = pd.DataFrame.from_dict(params)
pd.DataFrame.to_csv(params_data, '~/Documents/ExtraLong/data/acquisitionInfo/parameters.csv')


#    'ReceiveCoilName':metainfo['ReceiveCoilName'],
