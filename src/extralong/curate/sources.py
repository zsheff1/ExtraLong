from pathlib import Path
import shutil
import subprocess
from zipfile import ZipFile

import pandas as pd
import flywheel

PATH_SCRIPT = Path("/") / "project" / "ExtraLong" / "code" / "curate" / "convert.sh"
PATH_OUT = Path("/") / "project" / "ExtraLong"
PATH_HEURISTICS = Path("/") / "project" / "ExtraLong" / "code" / "curate" / "heuristics"


def make_path_new(df, root):
    return pd.Series(
        [
            root
            / f"sub-{bblid:06d}"
            / f"ses-{scanid:05d}"
            / "anat"
            / f"sub-{bblid:06d}_ses-{scanid:05d}_T1w.nii.gz"
            for bblid, scanid in zip(df["bblid"], df["scanid"])
        ],
        index=df.index,
    )


class LocalSource:
    def __init__(self, imglook, root):
        self.imglook = imglook
        self.root = root

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
        files = self.sessions_to_files(merged, self.root)
        return files

    @staticmethod
    def download(files):
        for source, destination in zip(files["source"], files["destination"]):
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

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
    def sessions_to_files(sessions, root):
        files_nii = (
            sessions.copy()
            .rename(columns={"path": "source"})
            .assign(destination=lambda df: make_path_new(df, root))
        )
        files_json = files_nii.copy().assign(
            source=lambda df: df["source"].map(
                lambda p: p.with_suffix("").with_suffix(".json")
            ),
            destination=lambda df: df["destination"].map(
                lambda p: p.with_suffix("").with_suffix(".json")
            ),
        )
        files = (
            pd.concat([files_nii, files_json], axis=0)
            .loc[lambda df: df["source"].map(Path.exists), :]
            .sort_values(["bblid", "scanid", "destination"])
            .reset_index(drop=True)
        )
        return files


class FlywheelSource:
    def __init__(self, fw, imglook, images_local, root):
        self.fw = fw
        self.imglook = imglook
        self.images_local = images_local
        self.root = root

    def find(self, inputs):
        queries = [self.query(self.fw, labels) for labels, _ in inputs]
        cleaned = [
            self.clean(queried, cat, self.imglook)
            for queried, (_, cat) in zip(queries, inputs)
        ]
        merged = self.merge(cleaned, self.imglook, self.images_local)
        files = self.session_to_file(self.fw, merged, self.root)
        deduplicated = self.deduplicate(self.fw, files)
        nii_json = self.add_json(self.fw, deduplicated)
        return nii_json

    @staticmethod
    def download(fw, files):
        for acquisition_id, file_name, destination in files.loc[
            :, ["acquisition_id", "file_name", "destination"]
        ].itertuples(index=False, name=None):
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
    def session_to_file(fw, sessions, root):
        rows = []
        for bblid, scanid, session_id, destination in zip(
            sessions["bblid"],
            sessions["scanid"],
            sessions["session_id"],
            make_path_new(sessions, root),
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
        files = pd.DataFrame(
            rows,
            columns=["bblid", "scanid", "acquisition_id", "file_name", "destination"],
        )
        return files

    @staticmethod
    def deduplicate(fw, files_duplicated):
        files_single = files_duplicated.groupby("destination").filter(
            lambda g: len(g) == 1
        )
        files_multi = files_duplicated.groupby("destination").filter(
            lambda g: len(g) > 1
        )
        files_multi["acquisition_time"] = files_multi.apply(
            lambda row: next(
                file.info["AcquisitionTime"]
                for file in fw.get(row["acquisition_id"]).files
                if file.name == row["file_name"]
            ),
            axis=1,
        )
        files_multi = files_multi.loc[
            files_multi.groupby("destination")["acquisition_time"].idxmax(), :
        ].drop(columns=["acquisition_time"])
        files_deduplicated = (
            pd.concat([files_single, files_multi], axis=0)
            .sort_values("destination")
            .reset_index(drop=True)
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
        files_nii = files[
            ["bblid", "scanid", "acquisition_id", "file_name", "destination"]
        ]
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


def download_uncurated(
    remaining: pd.DataFrame,
    fw: flywheel.Client,
    dir_scratch: Path,
    protocol: str,
    project_label: str,
    heuristic: str = None,
    sample: bool = False,
) -> None:
    dir_tmp = dir_scratch / f"tmp_{project_label}"
    dir_inner = dir_tmp / "scitran" / "bbl" / project_label
    dir_final = dir_scratch / project_label
    dir_tmp.mkdir(parents=True, exist_ok=True)
    dir_final.mkdir(parents=True, exist_ok=True)
    remaining_subset = (
        remaining.loc[remaining["protocol"].eq(protocol), :]
        .astype({"bblid": "Int64", "scanid": "Int64"})
        .astype({"bblid": "string", "scanid": "string"})
        .assign(
            sub_ses=lambda df: df["bblid"] + "_" + df["scanid"],
            session_label=lambda df: df["sourceid"].fillna(df["sub_ses"]),
        )
        .loc[:, ["bblid", "scanid", "session_label", "sub_ses"]]
    )
    if sample:
        remaining_subset = remaining_subset.sample(n=3, random_state=42)
    for bblid, scanid, session_label, sub_ses in remaining_subset.itertuples(
        index=False, name=None
    ):
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
                raise RuntimeError(
                    f"Expected directory structure violated: {str(dir_inner / candidate_label)}"
                )
        shutil.move(path_old, path_new)
        subprocess.run(
            [
                str(PATH_SCRIPT),
                "--input",
                str(path_new),
                "--output",
                str(PATH_OUT),
                "--heuristic",
                str(PATH_HEURISTICS / heuristic),
                "--subject",
                str(bblid).zfill(6),
                "--session",
                str(scanid).zfill(5),
            ],
            check=True,
        )
    shutil.rmtree(dir_tmp)
