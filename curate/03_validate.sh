#!/usr/bin/env bash

set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
code_root=$(cd -- "${script_dir}/.." && pwd)

source "${code_root}/config/project.env"

script_name=$(basename "${BASH_SOURCE[0]}")
script_stem="${script_name%.sh}"
script_root=$(basename "${script_dir}")

JOBSCRIPT_DIR="${JOBSCRIPT_ROOT}/${script_root}"
LOG_DIR="${LOG_ROOT}/${script_root}/${script_stem}"

CONFIG="${CODE_DIR}/curate/assets/bids_validator_config.json"
CONTAINER="${CODE_DIR}/containers/bids_validator_3.0.1.sif"

mkdir -p "${JOBSCRIPT_DIR}" "${LOG_DIR}"

jobscript_path="${JOBSCRIPT_DIR}/${script_stem}.sh"

cat <<-EOF > "${jobscript_path}"
#!/usr/bin/env bash
#BSUB -J ${script_stem}
#BSUB -o ${LOG_DIR}/${script_stem}.o
#BSUB -e ${LOG_DIR}/${script_stem}.e

module load apptainer

apptainer run --cleanenv \\
-B "${PROJECT_DIR}:${PROJECT_DIR}:ro" \\
-B "${CONFIG}:/bids_validator_config.json:ro" \\
${CONTAINER} \\
    ${PROJECT_DIR} \\
    --config /bids_validator_config.json \\
    --json \\
    --verbose \\
    --ignoreNiftiHeaders \\
| jq . \\
> ${LOG_DIR}/${script_stem}.json
EOF

chmod 755 "${jobscript_path}"
bsub < "${jobscript_path}"
