#!/usr/bin/env python3

import json
from pathlib import Path

import flywheel
import pandas as pd

from curate.src.curate import LocalSource, FlywheelSource, download_uncurated

# Set constants
PATH_PROJECT = Path("/") / "project" / "ExtraLong"
PATH_CODE_DATA = PATH_PROJECT / "code" / "data"
PATH_API = Path("~").expanduser() / "flywheel_api_key.txt"
PATH_IMGLOOK = PATH_CODE_DATA / "imglook.csv"
PATH_DXPMR7 = PATH_CODE_DATA / "n9498_diagnosis_dxpmr7_20170509.csv"
PATH_CONFIG = PATH_PROJECT / "code" / "curate" / "config.json"

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

# Read inputs and API key
with open(PATH_CONFIG, "r") as f:
    config = json.load(f)

with open(PATH_API, "r") as file:
    api_key = file.read()

# Format paths
config["inputs_local"] = [
    {**d, "path": Path(d["path"])} for d in config["inputs_local"]
]

# instantiate flywheel client
fw = flywheel.Client(api_key)

# Determine expected scans from imglook
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
local_source = LocalSource(imglook, PATH_PROJECT)
files_local = local_source.find(config["inputs_local"])

# Find scans remotely available on flywheel
flywheel_source = FlywheelSource(fw, imglook, files_local, PATH_PROJECT)
files_flywheel = flywheel_source.find(config["inputs_flywheel"])

# Summarize remaining
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
LocalSource.download(files_local.sample(n=3, random_state=42))
FlywheelSource.download(fw, files_flywheel.sample(n=3, random_state=42))
if remaining.shape[0] > 0:
    for input in config["inputs_uncurated"]:
        download_uncurated(
            remaining, fw, PATH_PROJECT / "scratch", **input, sample=True
        )
