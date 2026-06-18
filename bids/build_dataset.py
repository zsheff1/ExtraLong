from pathlib import Path

import flywheel
import pandas as pd

# Set Constants
PROJECT_LABELS_1 = [
    "22q_Midline_834246",
    "7T_GluCEST_Age_843818",
    "EFR01",
    "LongGluCEST_843329",
    "MOTIVE",
]
PROJECT_LABELS_2 = [
    "MIND_856432",
    "RSVP_855714",
]
PROJECT_LABEL_PBN = "SSBC_844685"

PATH_PROJECT = Path("/") / "project" / "ExtraLong"
PATH_CODE_DATA = PATH_PROJECT / "code" / "data"
PATH_API = Path("~").expanduser() / "flywheel_api_key.txt"
PATH_IMGLOOK = PATH_CODE_DATA / "imglook.csv"
PATH_DXPMR7 = PATH_CODE_DATA / "n9498_diagnosis_dxpmr7_20170509.csv"

LAST_DATAFREEZE = pd.to_datetime("2021-07-01")

COLUMNS_FLYWHEEL = [
    "project_id",
    "subject_id",
    "session_id",
    "project_label",
    "subject_label",
    "session_label",
]
COLUMNS_OUTPUT = ["bblid", "scanid", "path_old", "path_new"]
COLUMNS_IMGLOOK = ["bblid", "scanid", "protocol", "sourceid", "doscan"]

# Define functions
def make_path_new(df):
    return [
        Path("/project/ExtraLong") / f"sub-{bblid:06d}" / f"ses-{scanid:05d}"
        for bblid, scanid in zip(df["bblid"], df["scanid"])
    ]

def query_bblsub2(path, strategy, protocol=None, glob="sub-*/ses-*", session=None):
    paths = path.glob(glob)
    scans = (
        pd.DataFrame({"path": list(paths)})
        .assign(
            bblid=lambda df: df["path"]
            .map(lambda p: p.parent.name)
            .str.extract(r"sub-(\d+)"),
            session=lambda df: df["path"]
            .map(lambda p: p.name)
            .str.extract(r"ses-(\w+)"),
        )
        .astype({"bblid": "Int64"})
        .sort_values(["bblid", "session"])
        .reset_index(drop=True)
    )
    if strategy in ["many_to_one", "many_to_many"]:
        if isinstance(protocol, str):
            protocol = [protocol]
        protocol_imglook = imglook.loc[imglook["protocol"].isin(protocol), :].copy()
    else:
        protocol_imglook = imglook.copy()
    if strategy == "many_to_one":
        scans = scans.loc[scans["session"] == session, :].reset_index(drop=True)
        _on = "bblid"
    elif strategy == "many_to_many":
        scans["order"] = (
            scans.sort_values(["bblid", "session"]).groupby("bblid").cumcount() + 1
        )
        protocol_imglook["order"] = (
            protocol_imglook.sort_values(["bblid", "doscan"])
            .groupby("bblid")
            .cumcount()
            + 1
        )
        _on = ["bblid", "order"]
    elif strategy == "full":
        scans = scans.rename(columns={"session": "scanid"}).astype({"scanid": "Int64"})
        _on = ["bblid", "scanid"]
    output = (
        pd.merge(scans, protocol_imglook, on=_on, how="inner", validate="one_to_one")
        .assign(path_new=make_path_new)
        .rename(columns={"path": "path_old"})
        .loc[:, COLUMNS_OUTPUT]
        .sort_values(["bblid", "scanid"])
        .reset_index(drop=True)
    )
    return output

def query_flywheel(fw, project_labels, group="bbl"):
    if isinstance(project_labels, str):
        project_labels = [project_labels]
    for project_label in project_labels:
        project = fw.lookup(f"{group}/{project_label}")
        project_id = project.id
        for subject in project.subjects():
            subject_id = subject.id
            subject_label = subject.label
            for session in subject.sessions():
                session_id = session.id
                session_label = session.label
                yield (
                    project_id,
                    subject_id,
                    session_id,
                    project_label,
                    subject_label,
                    session_label,
                )

# Connect to flywheel
with open(PATH_API, "r") as file:
    api_key = file.read()

fw = flywheel.Client(api_key)

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
        & ~df["protocol"].isin([
            "842909 - TRANSCENDS_D1",
            "849188 - PRONET",
            "854294 - hyperfine_pilot",
            "855194 - SFARI_Penn",
            "855446 - cerebellothalamic_7t",
        ]),
        COLUMNS_IMGLOOK,
    ]
    .sort_values(["bblid", "scanid"])
    .reset_index(drop=True)
)

# What's available on bblsub2?
image_bblsub2_evol = query_bblsub2(
    path=Path("/") / "project" / "bbl_gur_evolpsy",
    strategy="many_to_one",
    protocol="833922 - EvolPsy",
    session="EVOL1",
)

image_bblsub2_pnc = query_bblsub2(
    path=Path("/") / "project" / "bbl_gur_pnc" / "data",
    strategy="many_to_many",
    protocol=[
        "810336 - Big GO",
        "810336 - GO3 FOLLOW UP",
        "810336 - Go2 Supplement",
        "810336 - Go3",
    ],
    glob="*/bids_directory/sub-*/ses-*",
)

image_bblsub2_extralong = query_bblsub2(
    path=PATH_PROJECT / "sourcedata",
    strategy="full",
)

bblsub2_standalone = (
    pd.concat([image_bblsub2_evol, image_bblsub2_pnc])
    .sort_values(["bblid", "scanid"])
    .reset_index(drop=True)
)

image_bblsub2_extralong = (
    pd.merge(
        bblsub2_standalone,
        image_bblsub2_extralong,
        on=["bblid", "scanid"],
        how="right",
        indicator=True,
    )
    .query("_merge=='right_only'")
    .rename(columns={"path_old_y": "path_old", "path_new_y": "path_new"})
    .loc[:, COLUMNS_OUTPUT]
    .reset_index(drop=True)
)

images_bblsub2 = (
    pd.concat([bblsub2_standalone, image_bblsub2_extralong])
    .sort_values(["bblid", "scanid"])
    .reset_index(drop=True)
)

# What's available on flywheel
image_flywheel_1 = (
    pd.DataFrame.from_records(
        query_flywheel(fw, PROJECT_LABELS_1), columns=COLUMNS_FLYWHEEL
    )
    .loc[
        lambda df: (
            df["subject_label"].str.match(r"^\d+$")
            & df["session_label"].str.match(r"^\d+$")
        ),
        :,
    ]
    .astype({"subject_label": "Int64", "session_label": "Int64"})
    .reset_index(drop=True)
)
image_flywheel_1 = (
    pd.merge(
        imglook,
        image_flywheel_1,
        left_on=["bblid", "scanid"],
        right_on=["subject_label", "session_label"],
        how="inner",
    )
    .rename(columns={"session_id": "path_old"})
    .assign(path_new=make_path_new)
    .loc[:, COLUMNS_OUTPUT]
)

image_flywheel_2 = (
    pd.DataFrame.from_records(
        query_flywheel(fw, PROJECT_LABELS_2), columns=COLUMNS_FLYWHEEL
    )
    .loc[
        lambda df: df["subject_label"].str.contains(r"\d+_\d+"),
        :
    ]
    .drop(columns=["session_label"])
)
image_flywheel_2[["bblid", "scanid"]] = image_flywheel_2["subject_label"].str.split("_", expand=True)
image_flywheel_2 = (
    image_flywheel_2
    .rename(columns={"session_id": "path_old"})
    .astype({"bblid": "Int64", "scanid": "Int64"})
    .assign(path_new=make_path_new)
    .loc[:, COLUMNS_OUTPUT]
)

image_flywheel_pbn = (
    pd.DataFrame.from_records(
        query_flywheel(fw, PROJECT_LABEL_PBN), columns=COLUMNS_FLYWHEEL
    )
    .loc[
        lambda df: (
            ~df["subject_label"].str.contains(r"(?i)PILOT")
            & df["subject_label"].str.contains(r"PE\d+_\d+")
        ),
        :,
    ]
    .merge(
        imglook,
        left_on="subject_label",
        right_on="sourceid",
        how="inner"
    )
    .rename(columns={"session_id": "path_old"})
    .assign(path_new=make_path_new)
    .loc[:, COLUMNS_OUTPUT]
)

image_flywheel = (
    pd.concat([image_flywheel_1, image_flywheel_2, image_flywheel_pbn])
    .merge(
        images_bblsub2,
        on=["bblid", "scanid"],
        how="outer",
        indicator=True,
    )
    .rename(columns={"path_old_x": "path_old", "path_new_x": "path_new"})
    .loc[lambda df: df["_merge"].eq("left_only"), COLUMNS_OUTPUT]
    .sort_values(["bblid", "scanid"])
    .reset_index(drop=True)
)

# combine all found images
images_found = (
    pd.concat([images_bblsub2, image_flywheel])
    .sort_values(["bblid", "scanid"])
    .reset_index(drop=True)
)
