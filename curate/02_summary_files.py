#!/usr/bin/env python3

import logging
from pathlib import Path
import shutil

import pandas as pd
import numpy as np

from extralong.curate import Scans
from extralong.config import load_project_paths

# set paths
paths = load_project_paths()

PATH_PROJECT = paths["PROJECT_DIR"]
PATH_CODE = paths["CODE_DIR"]
PATH_DATA = paths["DATA_DIR"]

PATH_ASSETS = Path(__file__).parent / "assets"

PATH_IMGLOOK = PATH_DATA / "imglook.csv"
PATH_DEMO = PATH_DATA / "subject.csv"

PATH_LOG = paths["LOG_ROOT"] / Path(__file__).parent.name / f"{Path(__file__).stem}.log"

# set up logging
PATH_LOG.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    datefmt="%Y-%m-%dT%H:%M:%S%z",
    filename=PATH_LOG,
    format="%(asctime)s %(levelname)s %(name)s %(funcName)s %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

# build data
logger.info("combine data from BIDS, imglook, and demographics")
logger.debug("read and manipulate BIDS structure info")
sub_ses = pd.DataFrame(
    [(path.parent.name, path.name) for path in PATH_PROJECT.glob("sub-*/ses-*")],
    columns=["participant_id", "session_id"],
)

logger.debug("read and manipulate imglook")
imglook = (
    pd.read_csv(PATH_IMGLOOK)
    .astype({"BBLID": "Int64", "SCANID": "Int64"})
    .assign(
        doscan=lambda df: pd.to_datetime(df["DOSCAN"]),
        participant_id=lambda df: "sub-" + df["BBLID"].astype(str).str.zfill(6),
        session_id=lambda df: "ses-" + df["SCANID"].astype(str).str.zfill(5),
    )
    .loc[:, ["participant_id", "session_id", "doscan"]]
)

logger.debug("read and manipulate demographics")
demo = (
    pd.read_csv(PATH_DEMO)
    .assign(
        participant_id=lambda df: "sub-"
        + df["BBLID"].astype("Int64").astype(str).str.zfill(6)
    )
    .loc[lambda df: df["participant_id"].isin(sub_ses["participant_id"]), :]
    .sort_values("participant_id")
    .reset_index(drop=True)
    .assign(
        dobirth=lambda df: pd.to_datetime(df["DOBIRTH"]),
        sex=lambda df: np.select(
            [df["SEX"].eq(1.0), df["SEX"].eq(2.0)], ["male", "female"], default="n/a"
        ),
        race=lambda df: np.select(
            [
                df["RACE"].eq(1.0),
                df["RACE"].eq(2.0),
                df["RACE"].eq(3.0),
                df["RACE"].eq(4.0),
                df["RACE"].eq(5.0),
                df["RACE"].eq(6.0),
            ],
            [
                "white",
                "black",
                "native_american",
                "asian",
                "biracial",
                "hawaiian_pacific_islander",
            ],
            default="n/a",
        ),
        ethnic=lambda df: np.select(
            [
                df["ETHNIC"].eq(1.0),
                df["ETHNIC"].eq(2.0),
            ],
            ["hispanic", "not_hispanic"],
            default="n/a",
        ),
        handedness=lambda df: np.select(
            [df["HAND"].eq(1.0), df["HAND"].eq(2.0), df["HAND"].eq(3.0)],
            ["right", "left", "ambidextrous"],
            default="n/a",
        ),
    )
    .loc[:, ["participant_id", "sex", "dobirth", "race", "ethnic", "handedness"]]
)

logger.debug("combine and manipulate data")
data = (
    sub_ses.merge(demo, how="left", on="participant_id")
    .merge(imglook, how="left", on=["participant_id", "session_id"])
    .assign(
        age=lambda df: (
            (df["doscan"].dt.year - df["dobirth"].dt.year) * 12
            + (df["doscan"].dt.month - df["dobirth"].dt.month)
            - (df["doscan"].dt.day < df["dobirth"].dt.day)
        )
    )
    .sort_values(["participant_id", "session_id"])
)

# generate summary files content
logger.info("generate content for participants.tsv")
participants = (
    data.loc[:, ["participant_id", "sex", "race", "ethnic", "handedness"]]
    .drop_duplicates()
    .reset_index(drop=True)
)

logger.info("generate content for sub-{}/sub-{}_sessions.tsv")
sessions = (
    {
        "participant_id": participant_id,
        "df": (
            data.loc[
                lambda df: df["participant_id"].eq(participant_id),
                ["session_id", "age"],
            ].reset_index(drop=True)
        ),
    }
    for participant_id in data["participant_id"].unique()
)

logger.info("generate content for sub-{}/ses-{}/sub-{}_ses-{}_scans.tsv")
logger.debug("instantiate Scans class")
scans_instance = Scans(data, PATH_PROJECT)
logger.debug("call Scans.method()")
scans = (
    {
        "participant_id": participant_id,
        "session_id": session_id,
        "df": scans_instance.method(participant_id, session_id),
    }
    for participant_id, session_id in data[["participant_id", "session_id"]].itertuples(
        index=False
    )
)

# delete old summary files
logger.info("delete old summary files")
old_summary_files = (
    list(PATH_PROJECT.glob("participants.tsv"))
    + list(PATH_PROJECT.glob("participants.json"))
    + list(PATH_PROJECT.glob("sub-*/sub-*_sessions.tsv"))
    + list(PATH_PROJECT.glob("sessions.json"))
    + list(PATH_PROJECT.glob("sub-*/ses-*/sub-*_ses-*_scans.tsv"))
    + list(PATH_PROJECT.glob("scans.json"))
)

for summary_file in old_summary_files:
    summary_file.unlink(missing_ok=True)

# write summary files
logger.info("write participants.tsv")
participants.to_csv(PATH_PROJECT / "participants.tsv", sep="\t", index=False)

logger.info("write sub-{}/sub-{}_sessions.tsv")
for session in sessions:
    participant_id = session.get("participant_id")
    path = PATH_PROJECT / participant_id / f"{participant_id}_sessions.tsv"
    df = session.get("df")
    df.to_csv(path, sep="\t", index=False)

logger.info("write sub-{}/ses-{}/sub-{}_ses-{}_scans.tsv")
for scan in scans:
    participant_id = scan.get("participant_id")
    session_id = scan.get("session_id")
    path = (
        PATH_PROJECT
        / participant_id
        / session_id
        / f"{participant_id}_{session_id}_scans.tsv"
    )
    df = scan.get("df")
    if df.empty:
        continue
    df.to_csv(path, sep="\t", index=False)

# write sidecars
logger.info(f"copy sidecars from {str(PATH_ASSETS)}")
for level in ["participants", "sessions", "scans"]:
    shutil.copy2(PATH_ASSETS / f"sidecar_{level}.json", PATH_PROJECT / f"{level}.json")
