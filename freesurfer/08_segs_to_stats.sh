#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
code_root=$(cd -- "${script_dir}/.." && pwd)

source "${code_root}/config/project.env"
source "${code_root}/config/freesurfer.sh"

script_name=$(basename "${BASH_SOURCE[0]}")
script_stem="${script_name%.sh}"

mkdir -p "${JOBSCRIPT_DIR}/${script_stem}" "${LOG_DIR}/${script_stem}"

while read -r sub_ses; do

    [[ "${sub_ses}" =~ (sub-[0-9]{6})_(ses-[0-9]{5}) ]]

    sub="${BASH_REMATCH[1]}"
    ses="${BASH_REMATCH[2]}"

    jobscript_path="${JOBSCRIPT_DIR}/${script_stem}/${sub}_${ses}.sh"

    cat <<-EOF > "${jobscript_path}"
	#!/usr/bin/env bash
	#BSUB -J ${script_stem}_${sub}_${ses}
	#BSUB -o ${LOG_DIR}/${script_stem}/${sub}_${ses}.o
	#BSUB -e ${LOG_DIR}/${script_stem}/${sub}_${ses}.e

	module load apptainer

	apptainer exec --containall \\
	    --bind "${FREESURFER_DATA_DIR}:/data_dir" \\
	    --bind "${LICENSE}:/license.txt:ro" \\
	    --env FS_LICENSE=/license.txt \\
	    --env SUBJECTS_DIR=/data_dir \\
	    --env SURFER_FRONTDOOR=1 \\
	    "${CONTAINER}" \\
	    bash -c '
	    for hemi in lh rh; do
	        [[ -f /data_dir/${sub_ses}/surf/\${hemi}.pial_lgi ]] || continue
	        mri_segstats \\
	        --annot ${sub_ses} \${hemi} aparc \\
	        --i /data_dir/${sub_ses}/surf/\${hemi}.pial_lgi \\
	        --sum /data_dir/${sub_ses}/stats/\${hemi}.aparc.pial_lgi.stats
	    done
	    '
	EOF

    chmod 775 "${jobscript_path}"
    bsub < "${jobscript_path}"
done < "${SUBJECTSFILE}"
