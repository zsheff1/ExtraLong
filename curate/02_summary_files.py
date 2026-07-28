from pathlib import Path
import shutil

import pandas as pd
import numpy as np

from extralong.curate import Scans

path_project = Path("/") / "project" / "ExtraLong"
path_code = path_project / "code"
path_data = path_code / "data"
path_sidecars = path_code / "curate" / "sidecars"
path_imglook = path_data / "imglook.csv"
path_demo = path_data / "subject.csv"

# build data
sub_ses = pd.DataFrame(
    [(path.parent.name, path.name) for path in path_project.glob("sub-*/ses-*")],
    columns=["participant_id", "session_id"],
)

imglook = (
    pd.read_csv(path_imglook)
    .astype({"BBLID": "Int64", "SCANID": "Int64"})
    .assign(
        doscan=lambda df: pd.to_datetime(df["DOSCAN"]),
        participant_id=lambda df: "sub-" + df["BBLID"].astype(str).str.zfill(6),
        session_id=lambda df: "ses-" + df["SCANID"].astype(str).str.zfill(5),
    )
    .loc[:, ["participant_id", "session_id", "doscan"]]
)

demo = (
    pd.read_csv(path_demo)
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
scans_instance = Scans(data, path_project)

participants = (
    data.loc[:, ["participant_id", "sex", "race", "ethnic", "handedness"]]
    .drop_duplicates()
    .reset_index(drop=True)
)

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
old_summary_files = (
    list(path_project.glob("participants.tsv"))
    + list(path_project.glob("participants.json"))
    + list(path_project.glob("sub-*/sub-*_sessions.tsv"))
    + list(path_project.glob("sessions.json"))
    + list(path_project.glob("sub-*/ses-*/sub-*_ses-*_scans.tsv"))
    + list(path_project.glob("scans.json"))
)

for summary_file in old_summary_files:
    summary_file.unlink(missing_ok=True)

# write summary files
participants.to_csv(path_project / "participants.tsv", sep="\t", index=False)

for session in sessions:
    participant_id = session.get("participant_id")
    path = path_project / participant_id / f"{participant_id}_sessions.tsv"
    df = session.get("df")
    df.to_csv(path, sep="\t", index=False)

for scan in scans:
    participant_id = scan.get("participant_id")
    session_id = scan.get("session_id")
    path = (
        path_project
        / participant_id
        / session_id
        / f"{participant_id}_{session_id}_scans.tsv"
    )
    df = scan.get("df")
    if df.empty:
        continue
    df.to_csv(path, sep="\t", index=False)

# write sidecars
for level in ["participants", "sessions", "scans"]:
    shutil.copy2(path_sidecars / f"{level}.json", path_project / f"{level}.json")
