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

mkdir -p "${JOBSCRIPT_DIR}" "${LOG_DIR}"

jobscript_path="${JOBSCRIPT_DIR}/${script_stem}.sh"

cat <<-EOF > "${jobscript_path}"
#!/usr/bin/env bash
#BSUB -J ${script_stem}
#BSUB -o ${LOG_DIR}/${script_stem}.o
#BSUB -e ${LOG_DIR}/${script_stem}.e

module load apptainer

apptainer run --cleanenv \\
-B ${PROJECT_DIR}:${PROJECT_DIR}:ro \\
-B ${CODE_DIR}:${CODE_DIR}:ro \\
${EXECUTABLE} \\
${PROJECT_DIR} \\
--config ${CODE_DIR}/curate/assets/bids_validator_config.json \\
--json \\
--verbose \\
--ignoreNiftiHeaders > ${LOG_DIR}/${script_stem}.json
EOF

chmod 755 "${jobscript_path}"
bsub < "${jobscript_path}"
