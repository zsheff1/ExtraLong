from pathlib import Path

import flywheel
import pandas as pd

from curate.sources import LocalSource, FlywheelSource

# TODO: what to do about projects that aren't BIDS'ified? PBN flywheel, MIND local

# Set constants
PATH_PROJECT = Path("/") / "project" / "ExtraLong"
PATH_CODE_DATA = PATH_PROJECT / "code" / "data"
PATH_API = Path("~").expanduser() / "flywheel_api_key.txt"
PATH_IMGLOOK = PATH_CODE_DATA / "imglook.csv"
PATH_DXPMR7 = PATH_CODE_DATA / "n9498_diagnosis_dxpmr7_20170509.csv"

PROJECT_LABELS_1 = [
    "22q_Midline_834246",
    "EFR01",
    "MOTIVE",
]
PROJECT_LABELS_2 = [
    "MIND_856432",
    "RSVP_855714",
]
PROJECT_LABEL_3 = "SSBC_844685"

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

# What's expected from imglook?
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

# What's available on bblsub2?
inputs_local = [
    {
        "path": Path("/") / "project" / "bbl_gur_evolpsy",
        "strategy": "many_to_one",
        "protocol": "833922 - EvolPsy",
        "session": "EVOL1",
    },
    {
        "path": Path("/") / "project" / "bbl_gur_pnc" / "data",
        "strategy": "many_to_many",
        "protocol": [
            "810336 - Big GO",
            "810336 - GO3 FOLLOW UP",
            "810336 - Go2 Supplement",
            "810336 - Go3",
        ],
        "glob": "*/bids_directory/sub-*/ses-*/anat/*_T1w.nii.gz",
    },
    {
        "path": PATH_PROJECT / "sourcedata",
        "strategy": "full",
    },
]

local_source = LocalSource(imglook, PATH_PROJECT)

files_local = local_source.find(inputs_local)

LocalSource.download(files_local.sample(n=20, random_state=42))

# What's available on flywheel?
with open(PATH_API, "r") as file:
    api_key = file.read()

fw = flywheel.Client(api_key)

inputs_flywheel = [
    [PROJECT_LABELS_1, 1],
    [PROJECT_LABELS_2, 2],
    [PROJECT_LABEL_3, 3],
]

flywheel_source = FlywheelSource(fw, imglook, files_local, PATH_PROJECT)

files_flywheel = flywheel_source.find(inputs_flywheel)

FlywheelSource.download(fw, files_flywheel.sample(n=20, random_state=42))

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
