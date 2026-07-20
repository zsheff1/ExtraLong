from pathlib import Path
from shutil import copy2

import flywheel
import pandas as pd

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


# Define functions and classes
def make_path_new(df):
    return pd.Series(
        [
            PATH_PROJECT
            / f"sub-{bblid:06d}"
            / f"ses-{scanid:05d}"
            / "anat"
            / f"sub-{bblid:06d}_ses-{scanid:05d}_T1w.nii.gz"
            for bblid, scanid in zip(df["bblid"], df["scanid"])
        ],
        index=df.index,
    )

class LocalSource:
    def __init__(self, imglook):
        self.imglook = imglook
    def find(self, inputs):
        queried = [
            self.query(
                input.get("path"), input.get("glob", "sub-*/ses-*/anat/*_T1w.nii.gz")
            )
            for input in inputs
        ]
        cleaned = [
            self.clean(
                data,
                input.get("strategy"),
                input.get("protocol"),
                input.get("session"),
                self.imglook,
            )
            for data, input in zip(queried, inputs)
        ]
        merged = self.merge(cleaned, [input.get("path") for input in inputs])
        files = self.sessions_to_files(merged)
        return files
    @staticmethod
    def download(files):
        for source, destination in zip(files["source"], files["destination"]):
            destination.parent.mkdir(parents=True, exist_ok=True)
            copy2(source, destination)
    @staticmethod
    def query(path, glob):
        paths = path.glob(glob)
        queried = pd.DataFrame({"path": list(paths)})
        queried["bblid"] = (
            queried["path"]
            .map(lambda p: p.name)
            .str.extract(r"sub-(\d+)")
            .astype("Int64")
        )
        queried["session"] = (
            queried["path"].map(lambda p: p.name).str.extract(r"ses-([A-Za-z0-9]+)")
        )
        return queried
    @staticmethod
    def clean(queried, strategy, protocol, session, imglook):
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
        cleaned = (
            pd.merge(
                queried, protocol_imglook, on=_on, how="inner", validate="one_to_one"
            )
            .loc[:, ["bblid", "scanid", "path"]]
            .sort_values(["bblid", "scanid"])
            .reset_index(drop=True)
        )
        return cleaned
    @staticmethod
    def merge(cleaned, paths):
        PATH_EXTRALONG = Path("/") / "project" / "ExtraLong" / "sourcedata"
        standalone = pd.concat(
            [data for data, path in zip(cleaned, paths) if path != PATH_EXTRALONG]
        )
        extralong = next(
            data for data, path in zip(cleaned, paths) if path == PATH_EXTRALONG
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
    @staticmethod
    def sessions_to_files(sessions):
        files_nii = (
            sessions
            .copy()
            .rename(columns={"path": "source"})
            .assign(destination=lambda df: make_path_new(df))
        )
        files_json = (
            files_nii
            .copy()
            .assign(
                source = lambda df: df["source"].map(lambda p: p.with_suffix("").with_suffix(".json")),
                destination = lambda df: df["destination"].map(lambda p: p.with_suffix("").with_suffix(".json"))
            )
        )
        files = (
            pd.concat([files_nii, files_json], axis=0)
            .loc[lambda df: df["source"].map(Path.exists), :]
            .sort_values(["bblid", "scanid", "destination"])
            .reset_index(drop=True)
        )
        return files


class FlywheelSource:
    def __init__(self, fw, imglook, images_local):
        self.fw = fw
        self.imglook = imglook
        self.images_local = images_local
    def find(self, inputs):
        queries = [self.query(self.fw, labels) for labels, _ in inputs]
        cleaned = [
            self.clean(queried, cat, self.imglook)
            for queried, (_, cat) in zip(queries, inputs)
        ]
        merged = self.merge(cleaned, self.imglook, self.images_local)
        files = self.session_to_file(self.fw, merged)
        deduplicated = self.deduplicate(files)
        nii_json = self.add_json(self.fw, deduplicated)
        return nii_json
    @staticmethod
    def download(fw, files):
        for acquisition_id, file_name, destination in files.itertuples(
            index=False, name=None
        ):
            acquisition = fw.get_acquisition(acquisition_id)
            destination.parent.mkdir(parents=True, exist_ok=True)
            acquisition.download_file(file_name, destination)
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
    def clean(queried, cat, imglook):
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
    def merge(cleans, imglook, images_local):
        return (
            pd.concat(cleans)
            .merge(
                imglook[["bblid", "scanid"]].drop_duplicates(),
                on=["bblid", "scanid"],
                how="inner",
            )
            .merge(
                images_local[["bblid", "scanid"]].drop_duplicates(),
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
    @staticmethod
    def session_to_file(fw, sessions):
        rows = []
        for bblid, scanid, session_id, destination in zip(
            sessions["bblid"], sessions["scanid"], sessions["session_id"], make_path_new(sessions)
        ):
            session = fw.get_session(session_id)
            for acquisition in session.acquisitions():
                for file in acquisition.files:
                    if "BIDS" not in file.info:
                        continue
                    if "Filename" not in file.info["BIDS"]:
                        continue
                    if "T1w.nii.gz" not in file.info["BIDS"]["Filename"]:
                        continue
                    rows.append((bblid, scanid, acquisition.id, file.name, destination))
        files = pd.DataFrame(rows, columns=["bblid", "scanid", "acquisition_id", "file_name", "destination"])
        return (files)
    @staticmethod
    def deduplicate(files_duplicated):
        files_single = files_duplicated.groupby("destination").filter(lambda g: len(g) == 1)
        files_multi = files_duplicated.groupby("destination").filter(lambda g: len(g) > 1)
        files_multi["acquisition_time"] = files_multi.apply(
            lambda row: next(
                file.info["AcquisitionTime"]
                for file in fw.get(row["acquisition_id"]).files
                if file.name == row["file_name"]
            ),
            axis=1,
        )
        files_multi = files_multi.loc[files_multi.groupby("destination")["acquisition_time"].idxmax(), :].drop(
            columns=["acquisition_time"]
        )
        files_deduplicated = (
            pd.concat([files_single, files_multi], axis=0).sort_values("destination").reset_index(drop=True)
        )
        return files_deduplicated
    @classmethod
    def add_json(cls, fw, files):
        files["json_file"] = files.apply(
            lambda row: cls.find_json_sidecar(
                fw,
                row["acquisition_id"],
                row["file_name"],
            ),
            axis=1,
        )
        files_nii = files[["bblid", "scanid", "acquisition_id", "file_name", "destination"]]
        files_json = (
            files[["bblid", "scanid", "acquisition_id", "json_file", "destination"]]
            .rename(columns={"json_file": "file_name"})
            .loc[lambda df: df["file_name"].notna()]
        )
        files_json["destination"] = files_json["destination"].map(
            lambda p: Path(p).with_suffix("").with_suffix(".json")
        )
        files = (
            pd.concat([files_nii, files_json], axis=0)
            .sort_values("destination")
            .reset_index(drop=True)
        )
        return files
    @staticmethod
    def find_json_sidecar(fw, acquisition_id, nii_name):
            acq = fw.get(acquisition_id)
            json_name = str(Path(nii_name).with_suffix("").with_suffix(".json"))
            match = next(
                (f.name for f in acq.files if f.name == json_name),
                None,
            )
            return match


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

local_source = LocalSource(imglook)

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

flywheel_source = FlywheelSource(fw, imglook, files_local)

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
