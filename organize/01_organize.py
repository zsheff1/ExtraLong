#!/usr/bin/env python3

import json
import logging
from pathlib import Path

from extralong.organize import SubjectsSessions, FreeSurferCleaner
from extralong.config import load_project_paths

# set paths
paths = load_project_paths()

DIR_CONFIG = paths["CONFIG_DIR"]
PATH_CONFIG = DIR_CONFIG / "organize.json"

PATH_LOG = paths["LOG_ROOT"] / Path(__file__).parent.name / f"{Path(__file__).stem}.log"

# set up logging
PATH_LOG.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    datefmt="%Y-%m-%dT%H:%M:%S%z",
    filename=PATH_LOG,
    format="%(asctime)s %(levelname)s %(name)s %(funcName)s %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

# read config
logger.info("reading input config")
with open(PATH_CONFIG) as f:
    config = json.load(f)

references = {key: Path(value) for key, value in config["references"].items()}
out_dir = Path(config["out_dir"])
inputs = [
    {key: Path(value) if key == "path" else value for key, value in input.items()}
    for input in config["inputs"]
]

# imaging data
logger.info("creating subjects_sessions table")
subjects_sessions = SubjectsSessions.create(references=references)
logger.info("creating imaging_data table")
imaging_data = FreeSurferCleaner.clean(
    inputs=inputs, reference=subjects_sessions, lobes=references["lobes"]
)

exports = [
    {"path": out_dir / "subjects_sessions.csv", "data": subjects_sessions},
    {"path": out_dir / "imaging_data.csv", "data": imaging_data},
]

logger.debug("creating output directory")
out_dir.mkdir(exist_ok=True, parents=True)

logger.info("exporting data tables")
for export in exports:
    path = export["path"]
    data = export["data"]
    logger.debug(f"exporting table to {path}")
    data.to_csv(path, index=False)
