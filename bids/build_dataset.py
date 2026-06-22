from pathlib import Path

import flywheel
import pandas as pd

# Set constants
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
PROJECT_LABEL_3 = "SSBC_844685"

PATH_PROJECT = Path("/") / "project" / "ExtraLong"
PATH_CODE_DATA = PATH_PROJECT / "code" / "data"
PATH_API = Path("~").expanduser() / "flywheel_api_key.txt"
PATH_IMGLOOK = PATH_CODE_DATA / "imglook.csv"
PATH_DXPMR7 = PATH_CODE_DATA / "n9498_diagnosis_dxpmr7_20170509.csv"

LAST_DATAFREEZE = pd.to_datetime("2021-06-30")

EXCLUDED_PROTOCOLS = [
    "842909 - TRANSCENDS_D1",
    "849188 - PRONET",
    "854294 - hyperfine_pilot",
    "855194 - SFARI_Penn",
    "855446 - cerebellothalamic_7t",
]


# Define functions and classes
def make_path_new(df):
    return [
        PATH_PROJECT / f"sub-{bblid:06d}" / f"ses-{scanid:05d}"
        for bblid, scanid in zip(df["bblid"], df["scanid"])
    ]


class bblsubClass:
    @classmethod
    def driver(cls, inputs):
        queried = [
            cls.query(input.get("path"), input.get("glob", "sub-*/ses-*"))
            for input in inputs
        ]
        filtered = [
            cls.filter(
                data, input.get("strategy"), input.get("protocol"), input.get("session")
            )
            for data, input in zip(queried, inputs)
        ]
        merged = cls.merge(filtered, [input.get("path") for input in inputs])
        return merged

    @staticmethod
    def query(path, glob):
        paths = path.glob(glob)
        queried = pd.DataFrame({"path": list(paths)})
        queried["bblid"] = (
            queried["path"]
            .map(lambda p: p.parent.name)
            .str.extract(r"sub-(\d+)")
            .astype("Int64")
        )
        queried["session"] = (
            queried["path"].map(lambda p: p.name).str.extract(r"ses-(\w+)")
        )
        return queried

    @staticmethod
    def filter(queried, strategy, protocol, session):
        if protocol is None:
            protocol_imglook = imglook.copy()
        else:
            if isinstance(protocol, str):
                protocol = [protocol]
            protocol_imglook = imglook.loc[imglook["protocol"].isin(protocol), :].copy()
        if strategy == "many_to_one":
            queried = queried.loc[queried["session"] == session, :].reset_index(
                drop=True
            )
            _on = "bblid"
        elif strategy == "many_to_many":
            queried["order"] = (
                queried.sort_values(["bblid", "session"]).groupby("bblid").cumcount()
                + 1
            )
            protocol_imglook["order"] = (
                protocol_imglook.sort_values(["bblid", "doscan"])
                .groupby("bblid")
                .cumcount()
                + 1
            )
            _on = ["bblid", "order"]
        elif strategy == "full":
            queried = queried.rename(columns={"session": "scanid"}).astype(
                {"scanid": "Int64"}
            )
            _on = ["bblid", "scanid"]
        filtered = (
            pd.merge(
                queried, protocol_imglook, on=_on, how="inner", validate="one_to_one"
            )
            .loc[:, ["bblid", "scanid", "path"]]
            .sort_values(["bblid", "scanid"])
            .reset_index(drop=True)
        )
        return filtered

    @staticmethod
    def merge(filtered, paths):
        PATH_EXTRALONG = Path("/") / "project" / "ExtraLong" / "sourcedata"
        standalone = pd.concat(
            [data for data, path in zip(filtered, paths) if path != PATH_EXTRALONG]
        )
        extralong = next(
            data for data, path in zip(filtered, paths) if path == PATH_EXTRALONG
        )
        extralong_only = (
            pd.merge(
                extralong,
                standalone[["bblid", "scanid"]].drop_duplicates(),
                on=["bblid", "scanid"],
                how="left",
                indicator=True,
            )
            .query("_merge=='left_only'")
            .drop(columns="_merge")
        )
        merged = (
            pd.concat([standalone, extralong_only])
            .sort_values(["bblid", "scanid"])
            .reset_index(drop=True)
        )
        return merged


class FlywheelClass:
    @classmethod
    def driver(cls, inputs, fw):
        queries = [cls.query(fw, labels) for labels, _ in inputs]
        cleaned = [
            cls.clean(queried, cat) for queried, (_, cat) in zip(queries, inputs)
        ]
        merged = cls.merge_filter(cleaned)
        return merged

    @staticmethod
    def query(fw, project_labels, group="bbl"):
        if isinstance(project_labels, str):
            project_labels = [project_labels]
        queried = pd.DataFrame.from_records(
            (
                (subject.label, session.label, session.id)
                for project_label in project_labels
                for project in [fw.lookup(f"{group}/{project_label}")]
                for subject in project.subjects()
                for session in subject.sessions()
            ),
            columns=["subject_label", "session_label", "session_id"],
        )
        return queried

    @staticmethod
    def clean(queried, cat):
        if cat == 1:
            filtered = queried.loc[
                queried["subject_label"].str.match(r"^\d+$")
                & queried["session_label"].str.match(r"^\d+$"),
                :,
            ]
        elif cat == 2:
            filtered = queried.loc[queried["subject_label"].str.contains(r"\d+_\d+"), :]
        elif cat == 3:
            filtered = queried.loc[
                queried["subject_label"].str.contains(r"PE\d+_\d+"), :
            ]
        if cat == 1:
            labeled = filtered.rename(
                columns={"subject_label": "bblid", "session_label": "scanid"}
            )
        elif cat == 2:
            labeled = filtered.copy()
            labeled[["bblid", "scanid"]] = labeled["subject_label"].str.split(
                "_", expand=True
            )
        elif cat == 3:
            labeled = pd.merge(
                filtered,
                imglook,
                left_on="subject_label",
                right_on="sourceid",
                how="inner",
            )
        cleaned = labeled.loc[:, ["bblid", "scanid", "session_id"]].astype(
            {"bblid": "Int64", "scanid": "Int64"}
        )
        return cleaned

    @staticmethod
    def merge_filter(cleans):
        return (
            pd.concat(cleans)
            .merge(
                imglook[["bblid", "scanid"]].drop_duplicates(),
                on=["bblid", "scanid"],
                how="inner",
            )
            .merge(
                images_bblsub2[["bblid", "scanid"]].drop_duplicates(),
                on=["bblid", "scanid"],
                how="left",
                indicator=True,
            )
            .loc[
                lambda df: df["_merge"].eq("left_only"),
                ["bblid", "scanid", "session_id"],
            ]
            .sort_values(["bblid", "scanid"])
            .reset_index(drop=True)
        )


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
inputs_bblsub2 = [
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
        "glob": "*/bids_directory/sub-*/ses-*",
    },
    {
        "path": PATH_PROJECT / "sourcedata",
        "strategy": "full",
    },
]

images_bblsub2 = bblsubClass.driver(inputs_bblsub2)

# What's available on flywheel?
with open(PATH_API, "r") as file:
    api_key = file.read()

fw = flywheel.Client(api_key)

inputs_flywheel = [
    [PROJECT_LABELS_1, 1],
    [PROJECT_LABELS_2, 2],
    [PROJECT_LABEL_3, 3],
]

images_flywheel = FlywheelClass.driver(inputs_flywheel, fw)

# Summarize remaining
images_found = (
    pd.concat([images_bblsub2, images_flywheel])
    .sort_values(["bblid", "scanid"])
    .reset_index(drop=True)
)

remaining = (
    pd.merge(imglook, images_found, on=["bblid", "scanid"], how="left", indicator=True)
    .loc[
        lambda df: (df["_merge"].eq("left_only") & df["doscan"].gt(LAST_DATAFREEZE)),
        ["bblid", "scanid", "protocol", "sourceid", "doscan"],
    ]
    .reset_index(drop=True)
)

remaining_summary = (
    remaining["protocol"].value_counts().rename_axis("protocol").reset_index(name="n")
)
