#!/usr/bin/env python3

import json
from pathlib import Path
from zipfile import ZipFile
import shutil

import flywheel
import pandas as pd

from curate.sources import LocalSource, FlywheelSource

# TODO: BIDS heuristic: PBN, MIND, 22q_Midline, RSVP

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
if remaining.shape[0] == 0: # if all files were found, download the dataset
    LocalSource.download(files_local)
    FlywheelSource.download(fw, files_flywheel[["acquisition_id", "file_name", "destination"]])
elif remaining.shape[0]: # if not all files were found, download a sample dataset
    LocalSource.download(files_local.sample(n=20, random_state=42))
    FlywheelSource.download(
        fw,
        files_flywheel[["acquisition_id", "file_name", "destination"]].sample(
            n=20, random_state=42
        ),
    )

## SCRATCH
remaining_configs = [
    {
        "protocol": "856432 - MIND",
        "project_label": "MIND_856432",
    },
    {
        "protocol": "844685 - PBN",
        "project_label": "SSBC_844685",
    },
    {
        "protocol": "855714 - RSVP",
        "project_label": "RSVP_855714",
    },
    {
        "protocol": "834246 - 22qmidline",
        "project_label": "22q_Midline_834246",
    },
]

def download_non_bids(
    remaining: pd.DataFrame,
    fw: flywheel.Client,
    protocol: str,
    project_label: str,
    sample: bool = False
) -> None:
    dir_scratch = PATH_PROJECT / "scratch"
    dir_tmp = dir_scratch / f"tmp_{project_label}"
    dir_inner = dir_tmp / "scitran" / "bbl" / project_label
    dir_final = dir_scratch / project_label
    dir_tmp.mkdir(parents=True, exist_ok=True)
    dir_final.mkdir(parents=True, exist_ok=True)
    remaining_subset = (
        remaining
        .loc[remaining["protocol"].eq(protocol), :]
        .astype({"bblid": "Int64", "scanid": "Int64"})
        .astype({"bblid": "string", "scanid": "string"})
        .assign(
            sub_ses=lambda df: df["bblid"] + "_" + df["scanid"],
            session_label=lambda df: df["sourceid"].fillna(df["sub_ses"])
        )
        .loc[:, ["session_label", "sub_ses"]]
    )
    if sample:
        remaining_subset = remaining_subset.sample(n=3, random_state=42)
    for session_label, sub_ses in remaining_subset.itertuples(index=False, name=None):
        candidate_labels = [session_label, session_label.replace("_", "/")]
        for candidate_label in candidate_labels:
            lookup_path = f"bbl/{project_label}/{candidate_label}"
            try:
                session = fw.lookup(lookup_path)
                break
            except flywheel.rest.ApiException as error:
                if error.status != 404:
                    raise
        else:
            print(f"Session not found: {', '.join(candidate_labels)}")
            continue
        destination = dir_tmp / f"{sub_ses}.zip"
        fw.download_zip(session, str(destination))
        with ZipFile(destination, "r") as zip_file:
            zip_file.extractall(dir_tmp)
        path_new = dir_final / sub_ses
        if "/" in candidate_label:
            path_old = dir_inner / candidate_label
        else:
            paths_old = list((dir_inner / candidate_label).iterdir())
            if len(paths_old) == 1:
                path_old = paths_old[0]
            else:
                raise RuntimeError(f"Expected directory structure violated: {str(dir_inner / candidate_label)}")
        shutil.move(path_old, path_new)
    shutil.rmtree(dir_tmp)

for remaining_config in remaining_configs:
    download_non_bids(remaining, fw, **remaining_config, sample=True)
