#!/usr/bin/env bash

set -euo pipefail

script_name=$(basename "${BASH_SOURCE[0]}")
script_stem="${script_name%.sh}"

project_labels=(
    "22q_Midline_834246"
    "MIND_856432"
    "SSBC_844685"
    "RSVP_855714"
)
heuristics=(
    "heuristic_22qmidline.py"
    "heuristic_mind.py"
    "heuristic_pbn.py"
    "heuristic_rsvp.py"
)

PROJECT_DIR="/project/ExtraLong"
SCRATCH_DIR="${PROJECT_DIR}/scratch"
BIDS_DIR="${SCRATCH_DIR}/bids"
HEURISTIC_DIR="${PROJECT_DIR}/code/curate/heuristics"
CONTAINER="${PROJECT_DIR}/code/containers/heudiconv_1.4.0.sif"
JOBSCRIPT_DIR="${PROJECT_DIR}/code/jobscripts/${script_stem}"
LOG_DIR="${PROJECT_DIR}/code/logs/${script_stem}"

if (( ${#project_labels[@]} != ${#heuristics[@]} )); then
    echo "project_labels and heuristics must have the same length" >&2
    exit 1
fi

mkdir -p "${JOBSCRIPT_DIR}" "${LOG_DIR}" "${BIDS_DIR}"

for i in "${!project_labels[@]}"; do
    project_label="${project_labels[$i]}"
    heuristic="${heuristics[$i]}"
    project_scratch="${SCRATCH_DIR}/${project_label}"

    for dir in ${project_scratch}/*/; do

        [[ "${dir}" =~ /([0-9]+)_([0-9]+)/ ]] || continue

        sub_raw="${BASH_REMATCH[1]}"
        ses_raw="${BASH_REMATCH[2]}"
        sub="$(printf '%06d' "${sub_raw}")"
        ses="$(printf '%05d' "${ses_raw}")"

        jobscript_path="${JOBSCRIPT_DIR}/${sub}_${ses}.sh"

        cat <<-EOF > "${jobscript_path}"
		#!/usr/bin/env bash
		#BSUB -J ${script_stem}_${sub}_${ses}
		#BSUB -o ${LOG_DIR}/${sub}_${ses}.o
		#BSUB -e ${LOG_DIR}/${sub}_${ses}.e

		mkdir -p /scratch/\$USER/\$LSB_JOBID
		trap 'echo "Cleaning /scratch/\$USER/\$LSB_JOBID"; rm -rf /scratch/\$USER/\$LSB_JOBID' EXIT

		module load apptainer

		apptainer run --containall \\
		    --bind "${project_scratch}:${project_scratch}:ro" \\
		    --bind "${BIDS_DIR}:${BIDS_DIR}" \\
		    --bind "${HEURISTIC_DIR}/${heuristic}:/heuristic.py:ro" \\
		    --bind "/scratch/\$USER/\$LSB_JOBID:/tmp" \\
		    --env TMPDIR=/tmp \\
		    "${CONTAINER}" \\
		    --files ${project_scratch}/${sub_raw}_${ses_raw}/*/*.dicom.zip \\
		    --grouping all \\
		    --heuristic /heuristic.py \\
		    --converter dcm2niix \\
		    --outdir "${BIDS_DIR}" \\
		    --bids \\
		    --subjects ${sub} \\
		    --ses ${ses} \\
		    --minmeta
		EOF

        chmod 775 "${jobscript_path}"
        bsub < "${jobscript_path}"

    done
done
