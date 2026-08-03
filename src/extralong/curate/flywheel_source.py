import logging
from pathlib import Path
import time

import pandas as pd
import flywheel
import requests

from .make_path_new import make_path_new

logger = logging.getLogger(__name__)


class FlywheelSource:
    """Locate, reconcile, and download imaging files stored on Flywheel.

    Flywheel projects are queried for sessions, matched to records in an imaging lookup table, filtered to exclude images already available locally, and converted into NIfTI and JSON file-transfer records.

    Attributes:
        fw: Authenticated Flywheel client.
        imglook: Imaging lookup table containing subject and scan metadata.
        images_local: Locally available imaging sessions used to exclude duplicate downloads.
        root: Root directory under which destination paths are constructed.
    """

    def __init__(
        self,
        fw: flywheel.Client,
        imglook: pd.DataFrame,
        images_local: pd.DataFrame,
        root: Path,
    ) -> None:
        """Initialize a Flywheel imaging source.

        Args:
            fw: Authenticated Flywheel client.
            imglook: Imaging lookup table used to map Flywheel labels to subject and scan identifiers.
            images_local: DataFrame containing subject and scan combinations already available from local sources.
            root: Root directory for standardized destination files.
        """
        self.fw = fw
        self.imglook = imglook
        self.images_local = images_local
        self.root = root

        logger.debug(
            f"Initialized FlywheelSource with {len(imglook)} imglook rows, {len(images_local)} local image rows, and root {root}"
        )

    def find(self, inputs: list[list[list[str] | str | int]]) -> pd.DataFrame:
        """Locate downloadable imaging files across Flywheel projects.

        Each configured Flywheel source is queried and cleaned according to its labeling category. The resulting sessions are matched to the imaging lookup table, filtered against locally available images, resolved to NIfTI files, deduplicated, and expanded to include available JSON sidecars.

        Args:
            inputs: Flywheel source configurations. Each entry contains a project label or list of project labels and an integer labeling category.

        Returns:
            A DataFrame containing subject and scan identifiers, Flywheel acquisition identifiers, source filenames, and standardized destination paths for NIfTI and JSON files.
        """

        logger.info(
            f"Finding Flywheel imaging files from {len(inputs)} configured sources"
        )

        queries = [self.query(self.fw, labels) for labels, _ in inputs]
        logger.info(
            f"Flywheel queries returned {sum(len(queried) for queried in queries)} sessions"
        )

        cleaned = [
            self.clean(queried, cat, self.imglook)
            for queried, (_, cat) in zip(queries, inputs)
        ]
        logger.info(
            f"Flywheel label cleaning retained {sum(len(data) for data in cleaned)} sessions"
        )

        merged = self.merge(cleaned, self.imglook, self.images_local)
        logger.info(
            f"Retained {len(merged)} Flywheel sessions after excluding unmatched and locally available images"
        )

        files = self.session_to_file(self.fw, merged, self.root)
        logger.info(
            f"Resolved {len(files)} candidate T1-weighted files from {len(merged)} Flywheel sessions"
        )

        deduplicated = self.deduplicate(self.fw, files)
        logger.info(
            f"Deduplication retained {len(deduplicated)} of {len(files)} candidate NIfTI files"
        )

        nii_json = self.add_json(self.fw, deduplicated)
        logger.info(
            f"Prepared {len(nii_json)} Flywheel file transfers, including {len(nii_json) - len(deduplicated)} JSON sidecars"
        )

        return nii_json

    @staticmethod
    def download(fw: flywheel.Client, files: pd.DataFrame, attempts: int = 5) -> None:
        """Download Flywheel files to their destination paths.

        Missing destination directories are created automatically before each file is downloaded.

        Args:
            fw: Authenticated Flywheel client.
            files: DataFrame containing ``acquisition_id``, ``file_name``, and ``destination`` columns.
        """
        logger.info(f"Downloading {len(files)} files from Flywheel")

        for acquisition_id, file_name, destination in files.loc[
            :, ["acquisition_id", "file_name", "destination"]
        ].itertuples(index=False, name=None):
            logger.debug(
                f"Downloading {file_name} from acquisition {acquisition_id} to {destination}"
            )

            acquisition = fw.get_acquisition(acquisition_id)
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            for attempt in range(1, attempts + 1):
                try:
                    acquisition.download_file(file_name, destination)
                    return
                except requests.exceptions.ConnectionError:
                    if attempt == attempts:
                        logger.exception(f"Download failed for {file_name} after {attempts} attempts")
                        raise

                    delay = 2 ** attempt
                    logger.warning(f"Download failed for {file_name}; retrying in {delay} seconds (attempt {attempt}/{attempts})")

                    destination.unlink(missing_ok=True)
                    time.sleep(delay)

        logger.info(f"Finished downloading {len(files)} files from Flywheel")

    @staticmethod
    def query(
        fw: flywheel.Client, project_labels: str | list[str], group: str = "bbl"
    ) -> pd.DataFrame:
        """Query Flywheel projects for their subjects and sessions.

        Args:
            fw: Authenticated Flywheel client.
            project_labels: Flywheel project label or labels to query.
            group: Flywheel group containing the projects.

        Returns:
            A DataFrame containing ``subject_label``, ``session_label``, and ``session_id`` for every session found in the requested projects.
        """
        if isinstance(project_labels, str):
            project_labels = [project_labels]

        logger.info(
            f"Querying {len(project_labels)} Flywheel projects in group {group}: {', '.join(project_labels)}"
        )

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
        logger.info(
            f"Found {len(queried)} sessions in Flywheel projects: {', '.join(project_labels)}"
        )

        return queried

    @staticmethod
    def clean(queried: pd.DataFrame, cat: int, imglook: pd.DataFrame) -> pd.DataFrame:
        """Convert Flywheel labels into subject and scan identifiers.

        The interpretation of Flywheel labels depends on ``cat``:
            - Category 1 expects numeric subject and session labels.
            - Category 2 expects the subject and scan identifiers to be combined in the subject label and separated by an underscore.
            - Category 3 expects a ``PE`` source identifier that can be matched to the imaging lookup table.

        Args:
            queried: DataFrame returned by :meth:`query`.
            cat: Integer identifying the Flywheel labeling convention.
            imglook: Imaging lookup table containing ``sourceid``, ``bblid``, and ``scanid`` mappings.

        Returns:
            A DataFrame containing ``bblid``, ``scanid``, and ``session_id``. Subject and scan identifiers use pandas nullable integer dtypes.
        """
        logger.debug(
            f"Cleaning {len(queried)} Flywheel sessions using label category {cat}"
        )

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

        logger.debug(
            f"Label category {cat} retained {len(filtered)} of {len(queried)} queried sessions"
        )

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

        logger.info(
            f"Cleaned {len(cleaned)} Flywheel sessions using label category {cat}"
        )

        return cleaned

    @staticmethod
    def merge(
        cleans: list[pd.DataFrame], imglook: pd.DataFrame, images_local: pd.DataFrame
    ) -> pd.DataFrame:
        """Combine Flywheel sessions and exclude unavailable or local images.

        The cleaned Flywheel session tables are concatenated and restricted to subject and scan combinations present in the imaging lookup table. Images already available from local sources are then removed.

        Args:
            cleans: Cleaned Flywheel session DataFrames.
            imglook: Imaging lookup table defining valid subject and scan combinations.
            images_local: DataFrame containing subject and scan combinations already available locally.

        Returns:
            A sorted DataFrame containing ``bblid``, ``scanid``, and ``session_id`` for sessions that should be downloaded from Flywheel.
        """
        logger.info(f"Merging {len(cleans)} cleaned Flywheel session tables")

        combined = pd.concat(cleans)

        logger.debug(
            f"Concatenated cleaned Flywheel tables contain {len(combined)} session rows"
        )

        matched = combined.merge(
            imglook[["bblid", "scanid"]].drop_duplicates(),
            on=["bblid", "scanid"],
            how="inner",
        )

        logger.debug(
            f"Imaging lookup matching retained {len(matched)} of {len(combined)} Flywheel session rows"
        )

        merged = (
            matched.merge(
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

        logger.info(
            f"Excluded {len(matched) - len(merged)} sessions already available locally; {len(merged)} remain for Flywheel retrieval"
        )

        return merged

    @staticmethod
    def session_to_file(
        fw: flywheel.Client, sessions: pd.DataFrame, root: Path
    ) -> pd.DataFrame:
        """Resolve Flywheel sessions to candidate T1-weighted NIfTI files.

        Acquisitions within each session are searched for files whose Flywheel BIDS metadata contains a filename identifying a T1-weighted NIfTI image.

        Args:
            fw: Authenticated Flywheel client.
            sessions: DataFrame containing ``bblid``, ``scanid``, and ``session_id`` columns.
            root: Root directory under which destination paths are created.

        Returns:
            A DataFrame containing one row per candidate file with ``bblid``, ``scanid``, ``acquisition_id``, ``file_name``, and ``destination`` columns.

        Notes:
            Multiple candidate files may initially map to the same destination. These are resolved later by :meth:`deduplicate`.
        """
        logger.info(
            f"Searching {len(sessions)} Flywheel sessions for T1-weighted NIfTI files"
        )

        rows = []

        for bblid, scanid, session_id, destination in zip(
            sessions["bblid"],
            sessions["scanid"],
            sessions["session_id"],
            make_path_new(sessions, root),
        ):
            logger.debug(
                f"Searching Flywheel session {session_id} for subject {bblid}, scan {scanid}"
            )

            session = fw.get_session(session_id)
            for acquisition in session.acquisitions():
                for file in acquisition.files:
                    if "BIDS" not in file.info:
                        continue
                    if "Filename" not in file.info["BIDS"]:
                        continue
                    if "T1w.nii.gz" not in file.info["BIDS"]["Filename"]:
                        continue

                    logger.debug(
                        f"Found T1-weighted candidate {file.name} in acquisition {acquisition.id}"
                    )

                    rows.append((bblid, scanid, acquisition.id, file.name, destination))
        files = pd.DataFrame(
            rows,
            columns=["bblid", "scanid", "acquisition_id", "file_name", "destination"],
        )

        logger.info(
            f"Found {len(files)} candidate T1-weighted files across {len(sessions)} Flywheel sessions"
        )

        return files

    @staticmethod
    def deduplicate(
        fw: flywheel.Client, files_duplicated: pd.DataFrame
    ) -> pd.DataFrame:
        """Select one file when multiple files share a destination.

        Files with unique destination paths are retained directly. When multiple files map to the same destination, the file with the latest acquisition time is selected.

        Args:
            fw: Authenticated Flywheel client.
            files_duplicated: Candidate file table that may contain multiple rows for a destination path.

        Returns:
            A DataFrame containing at most one file for each destination path.
        """
        logger.info(f"Deduplicating {len(files_duplicated)} candidate Flywheel files")

        files_single = files_duplicated.groupby("destination").filter(
            lambda g: len(g) == 1
        )
        files_multi = files_duplicated.groupby("destination").filter(
            lambda g: len(g) > 1
        )

        logger.debug(
            f"Found {len(files_single)} files with unique destinations and {len(files_multi)} files with duplicated destinations"
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

        logger.info(f"Retained {len(files_deduplicated)} files after deduplication")

        return files_deduplicated

    @classmethod
    def add_json(cls, fw: flywheel.Client, files: pd.DataFrame) -> pd.DataFrame:
        """Add available JSON sidecars to a NIfTI file table.

        Each NIfTI acquisition is searched for a JSON file with the matching basename. Existing sidecars are converted into separate transfer rows with JSON destination paths.

        Args:
            fw: Authenticated Flywheel client.
            files: Deduplicated NIfTI file table containing acquisition IDs, filenames, and destination paths.

        Returns:
            A combined DataFrame containing the original NIfTI files and all matching JSON sidecars.
        """
        logger.info(f"Searching for JSON sidecars for {len(files)} NIfTI files")

        files["json_file"] = files.apply(
            lambda row: cls.find_json_sidecar(
                fw,
                row["acquisition_id"],
                row["file_name"],
            ),
            axis=1,
        )

        sidecar_count = int(files["json_file"].notna().sum())

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

        logger.info(
            f"Added {sidecar_count} JSON sidecars to {len(files_nii)} NIfTI file records"
        )

        return files

    @staticmethod
    def find_json_sidecar(
        fw: flywheel.Client, acquisition_id: str, nii_name: str
    ) -> str:
        """Find the JSON sidecar corresponding to a NIfTI file.

        Args:
            fw: Authenticated Flywheel client.
            acquisition_id: Flywheel acquisition identifier.
            nii_name: Name of the NIfTI file whose sidecar should be located.

        Returns:
            The matching JSON filename, or ``None`` if no matching file exists.
        """
        acq = fw.get(acquisition_id)
        json_name = str(Path(nii_name).with_suffix("").with_suffix(".json"))
        match = next(
            (f.name for f in acq.files if f.name == json_name),
            None,
        )

        logger.debug(f"Found JSON sidecar {match} in acquisition {acquisition_id}")

        return match
