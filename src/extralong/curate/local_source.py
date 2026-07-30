import logging
from pathlib import Path
import shutil

import pandas as pd

from .make_path_new import make_path_new

logger = logging.getLogger(__name__)


class LocalSource:
    """Locate, reconcile, and copy locally stored imaging files.

    Local imaging files are matched to records in an imaging lookup table,
    reconciled across multiple source locations, and converted into source and
    destination file pairs.

    Attributes:
        imglook: Imaging lookup table containing subject and session metadata.
        root: Root directory under which destination paths are constructed.
    """

    def __init__(self, imglook: pd.DataFrame, root: Path) -> None:
        """Locate, reconcile, and copy locally stored imaging files.

        Local imaging files are matched to records in an imaging lookup table,
        reconciled across multiple source locations, and converted into source and
        destination file pairs.

        Attributes:
            imglook: Imaging lookup table containing subject and session metadata.
            root: Root directory under which destination paths are constructed.
        """
        self.imglook = imglook
        self.root = root

        logger.debug(
            f"Initialized LocalSource with {len(imglook)} imglook rows and root {root}"
        )

    def find(self, inputs: list[dict[str, str | list[str]]]) -> pd.DataFrame:
        """Locate and prepare files from configured local data sources.

        Each input source is queried for imaging files, matched to the imaging
        lookup table according to its specified strategy, and combined with
        the other sources. The resulting sessions are then expanded into NIfTI
        and JSON source-destination file pairs.

        Args:
            inputs: Local source configurations. Each configuration must
                contain ``path`` and ``strategy`` entries and may contain
                ``glob``, ``protocol``, and ``session`` entries.

        Returns:
            A DataFrame containing subject and session identifiers together
            with existing source files and their standardized destination
            paths.
        """
        logger.info(
            f"Finding local imaging files from {len(inputs)} configured sources"
        )

        queried = [
            self.query(
                input.get("path"), input.get("glob", "sub-*/ses-*/anat/*_T1w.nii.gz")
            )
            for input in inputs
        ]

        logger.debug(
            f"Local source queries returned {sum(len(data) for data in queried)} total files"
        )

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

        logger.debug(
            f"Local source cleaning retained {sum(len(data) for data in cleaned)} total sessions"
        )

        merged = self.merge(cleaned, [input.get("path") for input in inputs])
        files = self.sessions_to_files(merged, self.root)

        logger.info(
            f"Prepared {len(files)} local files from {len(merged)} unique sessions"
        )

        return files

    @staticmethod
    def download(files: pd.DataFrame) -> None:
        """Copy local files to their destination paths.

        Missing destination directories are created automatically. Files are
        copied with ``shutil.copy2`` so that supported filesystem metadata is
        preserved.

        Args:
            files: DataFrame containing ``source`` and ``destination`` columns.
        """
        logger.info(f"Copying {len(files)} local files")

        for source, destination in zip(files["source"], files["destination"]):
            logger.debug(f"Copying local file from {source} to {destination}")
            try:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
            except OSError:
                logger.exception(
                    f"Failed to copy local file from {source} to {destination}"
                )
                raise

        logger.info(f"Finished copying {len(files)} local files")

    @staticmethod
    def query(path: Path, glob: str) -> pd.DataFrame:
        """Find imaging files and extract their subject and session identifiers.

        Args:
            path: Root directory from which to search for files.
            glob: Glob pattern, relative to ``path``, identifying the imaging
                files to include.

        Returns:
            A DataFrame with ``path``, ``bblid``, and ``session`` columns.
            Subject and session identifiers are extracted from the filenames.
        """
        logger.debug(f"Querying local source {path} with glob pattern {glob}")

        paths = path.glob(glob)
        queried = pd.DataFrame({"path": list(paths)})

        if queried.empty:
            logger.warning(f"No files found under {path} with glob pattern {glob}")
        else:
            logger.info(
                f"Found {len(queried)} files under {path} with glob pattern {glob}"
            )

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
    def clean(
        queried: pd.DataFrame,
        strategy: str,
        protocol: str | list[str],
        session: str,
        imglook: pd.DataFrame,
    ) -> pd.DataFrame:
        """Match queried files to records in the imaging lookup table.

        The matching procedure depends on ``strategy``:

        - ``many_to_one`` matches a specified local session to lookup records
          using subject identifiers.
        - ``many_to_many`` orders sessions within each subject and matches them
          to chronologically ordered lookup records.
        - ``full`` directly matches subject and numeric session identifiers.

        Args:
            queried: DataFrame returned by :meth:`query`.
            strategy: Matching strategy. Expected values are ``many_to_one``,
                ``many_to_many``, or ``full``.
            protocol: Protocol name or names used to filter ``imglook``. If
                ``None``, all lookup records are used.
            session: Local session label to retain when using the
                ``many_to_one`` strategy.
            imglook: Imaging lookup table containing subject, session,
                protocol, and scan-date information.

        Returns:
            A cleaned DataFrame containing ``bblid``, ``scanid``, and ``path``,
            sorted by subject and scan identifier.
        """
        logger.debug(
            f"Cleaning {len(queried)} queried files using strategy={strategy}, protocol={protocol}, session={session}"
        )

        if protocol is None:
            protocol_imglook = imglook.copy()
        else:
            if isinstance(protocol, str):
                protocol = [protocol]
            protocol_imglook = imglook.loc[imglook["protocol"].isin(protocol), :].copy()

        logger.debug(
            f"Imaging lookup contains {len(protocol_imglook)} rows after protocol filtering"
        )

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

        logger.info(
            f"Matched {len(cleaned)} of {len(queried)} queried files using strategy {strategy}"
        )

        return cleaned

    @staticmethod
    def merge(cleaned: pd.DataFrame, paths: list[str]) -> pd.DataFrame:
        """Combine cleaned source tables using ExtraLong as a fallback source.

        Records from sources other than the ExtraLong ``sourcedata`` directory
        are treated as the preferred standalone records. ExtraLong records are
        included only when their ``bblid`` and ``scanid`` combination is not
        already present in a standalone source.

        Args:
            cleaned: Cleaned DataFrames corresponding positionally to
                ``paths``.
            paths: Source root paths corresponding positionally to the cleaned
                DataFrames.

        Returns:
            A combined DataFrame containing one preferred record for each
            available subject and scan combination.

        Notes:
            This method expects one entry for the ExtraLong ``sourcedata``
            directory and at least one standalone source.
        """
        path_extralong = Path("/") / "project" / "ExtraLong" / "sourcedata"

        logger.info(f"Merging {len(cleaned)} cleaned local source tables")
        logger.debug(f"Using {path_extralong} as the fallback local source")

        standalone = pd.concat(
            [data for data, path in zip(cleaned, paths) if path != path_extralong]
        )
        extralong = next(
            data for data, path in zip(cleaned, paths) if path == path_extralong
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

        logger.info(
            f"Merged {len(standalone)} preferred records with {len(extralong_only)} fallback records into {len(merged)} sessions"
        )

        return merged

    @staticmethod
    def sessions_to_files(sessions: pd.DataFrame, root: Path) -> pd.DataFrame:
        """Convert session records into NIfTI and JSON transfer records.

        A source-destination row is created for each NIfTI file and its
        corresponding JSON sidecar. Records whose source file does not exist
        are removed.

        Args:
            sessions: DataFrame containing ``bblid``, ``scanid``, and ``path``
                columns.
            root: Root directory under which destination paths are created.

        Returns:
            A DataFrame containing ``bblid``, ``scanid``, ``source``, and
            ``destination`` columns for all existing NIfTI and JSON files.
        """
        logger.info(
            f"Expanding {len(sessions)} local sessions into NIfTI and JSON file records"
        )

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

        logger.info(
            f"Prepared {len(files)} existing local files: {len(files_nii)} NIfTI candidates and {len(files_json)} JSON candidates before existence filtering"
        )

        return files
