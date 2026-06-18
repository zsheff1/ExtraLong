
source /appl/freesurfer-7.1.1/SetUpFreeSurfer.sh 
project=/project/ExtraLong
SUBJECTS_DIR=${project}/data/freesurferLongitudinal

cd ${project}/data/bids_directory

echo "fsid fsid-base Scan-Date" > $SUBJECTS_DIR/qdec/qdec_table.dat

subjList=$(ls ${project}/data/bids_directory | grep "sub")

for subj in $subjList;do

SessionList=`ls ${project}/data/bids_directory/${subj}`
	for session in $SessionList;do
		fsid=${subj}/${session}
		subjNum=$(echo "$subj" | sed 's/sub\-//')
		fsid_base="Template-${subjNum}"
		Scan_Date=$(jq .AcquisitionDateTime ${project}/data/bids_directory/$subj/$session/anat/*.json)
		echo "$fsid $fsid_base $Scan_Date" >> $SUBJECTS_DIR/qdec/qdec_table.dat
	 done
 done
 
asegstats2table --qdec-long /$SUBJECTS_DIR/qdec/qdec_table.dat --skip --stats aseg.stats --tablefile $project/data/freesurferLongitudinal/qdec/freesurferLongitudinal_aseg.table.txt
 
