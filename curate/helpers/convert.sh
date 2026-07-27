#!/usr/bin/env bash

set -euo pipefail

script_name=$(basename "${BASH_SOURCE[0]}")
script_stem="${script_name%.sh}"

PROJECT_DIR="/project/ExtraLong"
CONTAINER="${PROJECT_DIR}/code/containers/heudiconv_1.4.0.sif"
JOBSCRIPT_DIR="${PROJECT_DIR}/code/jobscripts/${script_stem}"
LOG_DIR="${PROJECT_DIR}/code/logs/${script_stem}"

input=""
output=""
heuristic=""
sub=""
ses=""

options=$(getopt \
    --options i:o:h:s:S: \
    --longoptions input:,output:,heuristic:,subject:,session: \
    --name "$0" \
    -- "$@"
) || exit 64

eval set -- "$options"

while true; do
    case "$1" in
        -i|--input)
            input="$2"
            shift 2
            ;;
        -o|--output)
            output="$2"
            shift 2
            ;;
        -h|--heuristic)
            heuristic="$2"
            shift 2
            ;;
        -s|--subject)
            sub="$2"
            shift 2
            ;;
        -S|--session)
            ses="$2"
            shift 2
            ;;
        --)
            shift
            break
            ;;
        *)
            echo "Unexpected argument: $1" >&2
            exit 64
            ;;
    esac
done

if [[ -z "${input}" || -z "${output}" || -z "${heuristic}" || -z "${sub}" || -z "${ses}" ]]; then
    cat >&2 <<EOF
Usage:
  $0 --input DIR --output DIR --heuristic FILE --subject ID --session ID

Required arguments:
  -i, --input       Input directory
  -o, --output      Output directory
  -h, --heuristic   HeuDiConv heuristic file
  -s, --subject     Six-digit subject ID
  -S, --session     Five-digit session ID
EOF
    exit 64
fi

if [[ ! -d "$input" ]]; then
    echo "Input directory does not exist: ${input}" >&2
    exit 66
fi

if [[ ! -f "${heuristic}" ]]; then
    echo "Heuristic does not exist: ${heuristic}" >&2
    exit 66
fi

if [[ ! "${sub}" =~ ^[0-9]{6}$ ]]; then
    echo "Invalid subject ID: ${sub}" >&2
    exit 64
fi

if [[ ! "${ses}" =~ ^[0-9]{5}$ ]]; then
    echo "Invalid subject ID: ${sub}" >&2
    exit 64
fi

mkdir -p "${JOBSCRIPT_DIR}" "${LOG_DIR}" "${output}"

jobscript_path="${JOBSCRIPT_DIR}/${sub}_${ses}.sh"

cat <<-EOF > "${jobscript_path}"
#!/usr/bin/env bash
#BSUB -J ${script_stem}_sub-${sub}_ses-${ses}
#BSUB -o ${LOG_DIR}/sub-${sub}_ses-${ses}.o
#BSUB -e ${LOG_DIR}/sub-${sub}_ses-${ses}.e

set -euo pipefail

scratch_dir="/scratch/\$USER/\$LSB_JOBID"

mkdir -p "\$scratch_dir"
trap 'echo "Cleaning \$scratch_dir"; rm -rf \$scratch_dir' EXIT

module load apptainer

apptainer run --containall \\
    --bind "${PROJECT_DIR}:${PROJECT_DIR}" \\
    --bind "${heuristic}:/heuristic.py:ro" \\
    --bind "\$scratch_dir:/tmp" \\
    --env TMPDIR=/tmp \\
    "${CONTAINER}" \\
    --files ${input}/*/*.dicom.zip \\
    --grouping all \\
    --heuristic /heuristic.py \\
    --converter dcm2niix \\
    --outdir "${output}" \\
    --bids \\
    --subjects ${sub} \\
    --ses ${ses} \\
    --minmeta
EOF

chmod 775 "${jobscript_path}"
bsub < "${jobscript_path}"
