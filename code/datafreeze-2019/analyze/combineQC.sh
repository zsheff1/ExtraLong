project=/project/ExtraLong
output_dir=${project}/data

subjList=`ls ${project}/data/freeqcLongitudinal|grep "sub"|cut -d "-" -f 2` 

for subj in $subjList; do
	QC_csv=$project/data/freeqcLongitudinal/"sub-${subj}"/Template/"sub-${subj}_ses-Template_quality".csv
	cp $QC_csv /$output_dir/Template_Quality_AllSubjects/"sub-${subj}_ses-Template_quality".csv
done

awk 'FNR==1 && NR!=1{next;}{print}' /$output_dir/Template_Quality_AllSubjects/|grep "sub"|*.csv >> Template_Quality_AllSubjects.csv

