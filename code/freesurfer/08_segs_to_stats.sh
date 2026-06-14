#!/usr/bin/env bash

DATA_DIR="/project/ExtraLong/derivatives/freesurfer"
JOBSCRIPT_DIR="/project/ExtraLong/code/jobscripts/freesurfer/08_segs_to_stats"
LOG_DIR="/project/ExtraLong/code/logs/freesurfer/08_segs_to_stats"
CONTAINER="/appl/containers/freesurfer_8.2.0.sif"
LICENSE="/project/ExtraLong/code/freesurfer/license.txt"
SUBJECTSFILE="${DATA_DIR}/subjectsfile.txt"

mkdir -p "${JOBSCRIPT_DIR}" "${LOG_DIR}"

while read -r sub_ses; do

    [[ "${sub_ses}" =~ (sub-[0-9]{6})_(ses-[0-9]{5}) ]]

    sub="${BASH_REMATCH[1]}"
    ses="${BASH_REMATCH[2]}"

    jobscript_path="${JOBSCRIPT_DIR}/${sub}_${ses}.sh"

    cat <<-EOF > "${jobscript_path}"
	#!/usr/bin/env bash
	#BSUB -J segs_to_stats_${sub}_${ses}
	#BSUB -o ${LOG_DIR}/${sub}_${ses}.o
	#BSUB -e ${LOG_DIR}/${sub}_${ses}.e

	module load apptainer

	apptainer exec --cleanenv \\
	    --bind "${DATA_DIR}:/data_dir" \\
	    --bind "${LICENSE}:/license.txt:ro" \\
	    --env FS_LICENSE=/license.txt \\
	    --env SUBJECTS_DIR=/data_dir \\
	    --env SURFER_FRONTDOOR=1 \\
	    "${CONTAINER}" \\
	    bash -c '
	    for hemi in lh rh; do
	        mri_segstats \\
	        --annot ${sub_ses} \${hemi} aparc \\
	        --i \${hemi}.pial_lgi \\
	        --sum \${hemi}.aparc.pial_lgi.stats
	    done
	    '
	EOF

    chmod 775 "${jobscript_path}"
    bsub < "${jobscript_path}"
done < "${SUBJECTSFILE}"
