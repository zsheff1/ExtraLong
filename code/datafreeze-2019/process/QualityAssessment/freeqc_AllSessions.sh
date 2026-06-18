# The following code calculates quality control values for every longitudinal session in the freesurferLongitudinal directory. Note that euler values and holes are calculated using cross-sectional files since the long.template files do not contain information on holes or euler number (the freesurfer pipeline attempts to set euler number = 2 so reporting euler number after longitudinal processing is pointless).  
project=/project/ExtraLong
inputDir=${project}/data/freesurferLongitudinal
outputDir=${project}/data/qualityAssessment

echo "fsid Session Scan_Date euler_lh euler_rh holes_lh holes_rh euler_total holes_total cnr_graycsf_lh cnr_graycsf_rh cnr_graywhite_lh cnr_graywhite_rh" >> ${outputDir}/AllSessions_quality.csv
SubjList=`ls ${inputDir} | grep "sub"`

for subj in $SubjList;do 
	Sessions=`ls ${inputDir}/${subj} | grep "ses" | grep -v "Template"`
	subjNum=`echo $subj | cut -d "-" -f 2`
	for session in $Sessions; do
		ID=`echo $subj | cut -d "-" -f 2`		 
		Session=`echo $session`
		Scan_Date=$(jq .AcquisitionDateTime ${project}/data/bids_directory/$subj/$session/anat/*.json)
		euler_holes=`grep -A 2 "Computing euler" ${project}/data/freesurferLongitudinal/${subj}/${session}/scripts/recon-all.log | sed 's/[[:alpha:]]//g' | sed 's/[.=,]//g'` 
		euler_lh=`echo $euler_holes |cut -d " " -f 1`
		euler_rh=`echo $euler_holes |cut -d " " -f 2`
		holes_lh=`echo $euler_holes |cut -d " " -f 3`
		holes_rh=`echo $euler_holes |cut -d " " -f 4`
		euler_total=`expr ${euler_lh} + ${euler_rh}`
		holes_total=`expr ${holes_lh} + ${holes_rh}`
		cnr=`SURFER_FRONTDOOR=1 mri_cnr ${inputDir}/${subj}/${session}/surf ${inputDir}/${subj}/${session}/mri/norm.mgz`
		cnr_graycsf_lh=`echo $cnr | cut -d "," -f 4 | sed 's/lh.*//g' | cut -d "=" -f 2`
		cnr_graycsf_rh=`echo $cnr | cut -d "," -f 7 | sed 's/rh.*//g' | cut -d "=" -f 2`
		cnr_graywhite_lh=`echo $cnr | cut -d "," -f 3 | cut -d "=" -f 3`
		cnr_graywhite_rh=`echo $cnr | cut -d "," -f 6 | cut -d "=" -f 3`
		echo $ID $Session $Scan_Date $euler_lh $euler_rh $holes_lh $holes_rh $euler_total $holes_total $cnr_graycsf_lh $cnr_graycsf_rh $cnr_graywhite_lh $cnr_graywhite_rh >> ${outputDir}/AllSessions_quality.csv
 	done 
done 
		  
