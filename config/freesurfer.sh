DESCRIPTION="freesurfer"

PROJECT_DIR="/project/ExtraLong"
DATA_DIR="${PROJECT_DIR}/derivatives/${DESCRIPTION}"
SUBJECTSFILE="${DATA_DIR}/subjectsfile.txt"

JOBSCRIPT_DIR="${PROJECT_DIR}/code/jobscripts/${DESCRIPTION}"
LOG_DIR="${PROJECT_DIR}/code/logs/${DESCRIPTION}"

CONTAINER="/appl/containers/freesurfer_8.2.0.sif"
LICENSE="${PROJECT_DIR}/code/${DESCRIPTION}/license.txt"

TABULATE_SUBREGIONS="${PROJECT_DIR}/code/${DESCRIPTION}/tabulate_subregions.py"

NTHREADS=4