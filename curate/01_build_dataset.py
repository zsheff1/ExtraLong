#!/usr/bin/env python3

import json
import logging
from pathlib import Path

import flywheel
import pandas as pd

from extralong.curate import LocalSource, FlywheelSource, download_uncurated
from extralong.config import load_project_paths

# Set constants
EXCLUDED_PROTOCOLS = [
    "842909 - TRANSCENDS_D1",
    "843329 - LongGluCEST",
    "843818 - 7t_glucest_age",
    "849188 - PRONET",
    "854294 - hyperfine_pilot",
    "855194 - SFARI_Penn",
    "855446 - cerebellothalamic_7t",
]

LAST_DATAFREEZE = pd.to_datetime("2021-06-30")

STEM = Path(__file__).stem

# Set paths
paths = load_project_paths()

PATH_PROJECT = paths["PROJECT_DIR"]
PATH_CODE = paths["CODE_DIR"]
PATH_CODE_DATA = paths["DATA_DIR"]
PATH_SCRATCH = paths["SCRATCH_DIR"]
DIR_CONFIG = paths["CONFIG_DIR"]

PATH_API = Path("~").expanduser() / "flywheel_api_key.txt"

PATH_IMGLOOK = PATH_CODE_DATA / "imglook.csv"
PATH_DXPMR7 = PATH_CODE_DATA / "n9498_diagnosis_dxpmr7_20170509.csv"
PATH_CONFIG = DIR_CONFIG / "curate.json"

PATH_LOG = paths["LOG_ROOT"] / Path(__file__).parent.name / STEM / f"{STEM}.log"

# set up logging
PATH_LOG.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    datefmt="%Y-%m-%dT%H:%M:%S%z",
    filename=PATH_LOG,
    format="%(asctime)s %(name)s %(funcName)s %(levelname)s %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

# Read inputs and API key
logger.info("read inputs")
logger.debug("reading input config")
with open(PATH_CONFIG, "r") as f:
    config = json.load(f)

logger.debug("reading flywheel API key")
with open(PATH_API, "r") as file:
    api_key = file.read()

# Format paths
logger.debug("convert config local input paths from str to Path")
config["inputs_local"] = [
    {**d, "path": Path(d["path"])} for d in config["inputs_local"]
]

# instantiate flywheel client
logger.info("instantiating flywheel client")
fw = flywheel.Client(api_key)

# Determine expected scans from imglook
logger.info("determine expected scans")
n9498 = pd.read_csv(
    PATH_DXPMR7,
    usecols=["bblid"],
    dtype={"bblid": "Int64"},
).squeeze()

imglook = (
    pd.read_csv(
        PATH_IMGLOOK,
        usecols=["BBLID", "SCANID", "PROTOCOL", "SOURCEID", "DOSCAN", "SCANSTAT"],
        dtype={"BBLID": "Int64", "PROTOCOL": str, "SCANID": "Int64", "SCANSTAT": str},
        parse_dates=["DOSCAN"],
    )
    .rename(columns=str.lower)
    .loc[
        lambda df: df["bblid"].isin(n9498)
        & ~df["scanstat"].str.contains(r"IS5\w?", na=False)
        & ~df["protocol"].isin(EXCLUDED_PROTOCOLS),
        ["bblid", "scanid", "protocol", "sourceid", "doscan"],
    ]
    .sort_values(["bblid", "scanid"])
    .reset_index(drop=True)
)

# Find scans locally available on bblsub2
logger.info("find local scans")
logger.debug("instantiate LocalSource")
local_source = LocalSource(imglook, PATH_PROJECT)
logger.debug("finding local files")
files_local = local_source.find(config["inputs_local"])

# Find scans remotely available on flywheel
logger.info("find scans on flywheel")
logger.debug("instantiate FlywheelSource")
flywheel_source = FlywheelSource(fw, imglook, files_local, PATH_PROJECT)
logger.debug("find flywheel files")
files_flywheel = flywheel_source.find(config["inputs_flywheel"])

# Summarize remaining
logger.info("summarize scans that have been found")
files_found = (
    pd.concat([files_local, files_flywheel])
    .sort_values(["bblid", "scanid"])
    .reset_index(drop=True)
)

remaining = (
    pd.merge(imglook, files_found, on=["bblid", "scanid"], how="left", indicator=True)
    .loc[
        lambda df: (df["_merge"].eq("left_only") & df["doscan"].gt(LAST_DATAFREEZE)),
        ["bblid", "scanid", "protocol", "sourceid", "doscan"],
    ]
    .reset_index(drop=True)
)

remaining_summary = (
    remaining["protocol"].value_counts().rename_axis("protocol").reset_index(name="n")
)

# Download scans
logger.info("copying local scans")
LocalSource.download(files_local)
logger.info("download flywheel scans")
FlywheelSource.download(fw, files_flywheel)
if remaining.shape[0] > 0:
    logger.info("downloading uncurated scans")
    for input in config["inputs_uncurated"]:
        download_uncurated(remaining, fw, PATH_SCRATCH, STEM, **input)
