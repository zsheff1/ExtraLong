#!/bin/bash
#BSUB -o /project/bbl_gur_evolpsy/code/logs/dwi/tbss/enigma_qc.o
#BSUB -e /project/bbl_gur_evolpsy/code/logs/dwi/tbss/enigma_qc.e
#BSUB -J enigma_qc

# Emma Sprooten for ENIGMA-DTI
# run in a new directory eg. Proj_Dist/
# create a text file containing paths to your masked FA maps
# output in Proj_Dist.txt

module load fsl/6.0.3

###### USER INPUTS ###############
## insert main folder where you ran TBSS
## just above "stats/" and "FA/"
maindir="/project/bbl_gur_evolpsy/derivatives/dwi/"
list=`find $maindir -wholename "${maindir}sub-*/ses-*/dwi/sub-*_ses-*_diffeo_fa.nii.gz"`

cd ${maindir}

## insert full path to mean_FA, skeleton mask and distance map
## based on ENIGMA-DTI protocol this should be:
mean_FA="/project/bbl_gur_evolpsy/derivatives/dwi/stats/mean_FA.nii.gz"
mask="/project/bbl_gur_evolpsy/derivatives/dwi/stats/mean_FA_skeleton_mask.nii.gz"
dst_map="/project/bbl_gur_evolpsy/derivatives/dwi/stats/mean_FA_skeleton_mask_dst.nii.gz"

##############
### from here it should be working without further adjustments

rm -f /project/bbl_gur_evolpsy/derivatives/dwi/stats/Proj_Dist.txt
echo "ID" "Mean_Squared" "Max_Squared" >> /project/bbl_gur_evolpsy/derivatives/dwi/stats/Proj_Dist.txt


## for each FA map
    for FAmap in ${list}   
    do
	base=`echo $FAmap | awk 'BEGIN {FS="/"}; {print $NF}' | awk 'BEGIN {FS="_"}; {print $1"_"$2}'`
        dst_out="dst_vals_"$base""

	# get Proj Dist images
        tbss_skeleton -d -i $mean_FA -p 0.2 $dst_map $FSLDIR/data/standard/LowerCingulum_1mm $FAmap $dst_out

	#X direction
	Xout=""squared_X_"$base"
	file=""$dst_out"_search_X.nii.gz"
	fslmaths $file -mul $file $Xout

	#Y direction
	Yout=""squared_Y_"$base"
	file=""$dst_out"_search_Y.nii.gz"
	fslmaths $file -mul $file $Yout

	#Z direction
        Zout=""squared_Z_"$base"
        file=""$dst_out"_search_Z.nii.gz"
	fslmaths $file -mul $file $Zout

	#Overall displacement
	Tout="Total_ProjDist_"$base""
	fslmaths $Xout -add $Yout -add $Zout $Tout

	# store extracted distances
	mean=`fslstats -t $Tout -k $mask -m`  
	max=`fslstats -t $Tout -R | awk '{print $2}'`
        echo "$base $mean $max" >> /project/bbl_gur_evolpsy/derivatives/dwi/stats/Proj_Dist.txt

        # remove X Y Z images
        ## comment out for debugging
        rm ./dst_vals_*.nii.gz
        rm ./squared_*.nii.gz
		rm ./Total_ProjDist_*.nii.gz

	echo "file $Tout done"
    done