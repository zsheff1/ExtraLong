import json
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class Scans:
    """Create and update BIDS scans tables for imaging sessions.

    Existing scans tables are read when available, missing imaging files are added, missing acquisition times are recovered from JSON sidecars, and acquisition dates are anonymized.

    Attributes:
        data: Session metadata containing participant identifiers, session identifiers, ages, and scan dates.
        path_project: Root directory containing participant and session directories.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        path_project: Path,
    ) -> None:
        """Initialize a scans table processor.

        Args:
            data: Session metadata containing participant identifiers, session identifiers, ages, and scan dates.
            path_project: Root directory containing participant and session directories.
        """
        self.data = data
        self.path_project = path_project

        logger.debug(
            f"Initialized Scans with {len(data)} metadata rows and project path {path_project}"
        )

    def method(
        self,
        participant_id: str,
        session_id: str,
    ) -> pd.DataFrame:
        """Create an updated scans table for one imaging session.

        The existing scans table is read when present. Imaging files not listed in the table are added, missing acquisition times are recovered from JSON sidecars when possible, and acquisition dates are anonymized while preserving the original scan times.

        Args:
            participant_id: BIDS participant identifier.
            session_id: BIDS session identifier.

        Returns:
            A DataFrame containing the imaging filenames and anonymized acquisition times for the session.
        """
        logger.info(f"Creating scans table for {participant_id}, {session_id}")

        session_dir = self.path_project / participant_id / session_id
        scans_name = f"{participant_id}_{session_id}_scans.tsv"
        scans_path = session_dir / scans_name

        if scans_path.exists():
            logger.debug(f"Reading existing scans table {scans_path}")
            scans = pd.read_csv(scans_path, sep="\t", usecols=["filename", "acq_time"])
            logger.debug(f"Read {len(scans)} rows from {scans_path}")
        else:
            logger.warning(
                f"No scans table found at {scans_path}; creating an empty table"
            )
            scans = pd.DataFrame(columns=["filename", "acq_time"])
        scans = self.add_missing_files(scans, session_dir)
        scans = (
            self.impute_acq_time(
                scans, session_dir, participant_id, session_id, self.data
            )
            .assign(
                acq_time=lambda df: self.anonymize_acq_time(
                    participant_id, session_id, df["acq_time"], self.data
                )
            )
            .loc[:, ["filename", "acq_time"]]
            .sort_values("filename")
        )

        logger.info(
            f"Created scans table with {len(scans)} rows for {participant_id}, {session_id}"
        )

        return scans

    @staticmethod
    def anonymize_acq_time(
        participant_id: str,
        session_id: str,
        acq_time: pd.Series,
        data: pd.DataFrame,
    ) -> pd.Series:
        """Anonymize acquisition dates while preserving scan times.

        The participant's age in months is added to a fixed date of birth of January 1, 1900. The resulting anonymized scan date is combined with the original hour, minute, and second for each acquisition.

        Args:
            participant_id: BIDS participant identifier.
            session_id: BIDS session identifier.
            acq_time: Series containing acquisition date-time values.
            data: Session metadata containing an ``age`` column.

        Returns:
            A Series containing ISO-formatted anonymized acquisition times. Missing values are represented as ``"n/a"``.
        """
        logger.debug(
            f"Anonymizing {len(acq_time)} acquisition times for "
            f"{participant_id}, {session_id}"
        )

        ANON_DOB = pd.to_datetime("1900-01-01")
        acq_time = pd.to_datetime(acq_time, errors="coerce")

        age_months = data.loc[
            lambda df: df["participant_id"].eq(participant_id)
            & df["session_id"].eq(session_id),
            "age",
        ].item()

        logger.debug(
            f"Using age {age_months} months to anonymize {participant_id}, {session_id}"
        )

        anon_age = pd.DateOffset(months=age_months)
        anon_scandate = ANON_DOB + anon_age

        anonymized = acq_time.map(
            lambda t: (
                anon_scandate.replace(
                    hour=t.hour,
                    minute=t.minute,
                    second=t.second,
                    microsecond=0,
                ).isoformat()
                if pd.notna(t)
                else "n/a"
            )
        )

        logger.debug(
            f"Anonymized {anonymized.ne('n/a').sum()} acquisition times for {participant_id}, {session_id}"
        )

        return anonymized

    @staticmethod
    def impute_acq_time(
        scans: pd.DataFrame,
        session_dir: Path,
        participant_id: str,
        session_id: str,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        """Impute missing acquisition times from JSON sidecars.

        Rows whose acquisition time is ``"n/a"`` are matched to JSON sidecars. When a sidecar contains ``AcquisitionTime``, its time component is combined with the session's scan date.

        Args:
            scans: Scans table containing ``filename`` and ``acq_time`` columns.
            session_dir: Directory containing the session imaging files.
            participant_id: BIDS participant identifier.
            session_id: BIDS session identifier.
            data: Session metadata containing a ``doscan`` column.

        Returns: The scans DataFrame with available missing acquisition times imputed.
        """
        indices = scans.index[scans["acq_time"].eq("n/a")]

        if indices.empty:
            logger.debug(
                f"No acquisition times require imputation for {participant_id}, {session_id}"
            )
            return scans

        logger.info(
            f"Attempting to impute {len(indices)} acquisition times for {participant_id}, {session_id}"
        )

        for i in indices:
            filename = scans.loc[i, "filename"]
            sidecar_path = (session_dir / filename).with_suffix("").with_suffix(".json")

            if not sidecar_path.exists():
                logger.warning(
                    f"Cannot impute acquisition time for {filename}: sidecar not found at {sidecar_path}"
                )
                continue

            logger.debug(f"Reading acquisition time from {sidecar_path}")

            with open(sidecar_path, "r") as file:
                sidecar = json.load(file)

            if "AcquisitionTime" not in sidecar:
                logger.warning(
                    f"Cannot impute acquisition time for {filename}: AcquisitionTime is absent from {sidecar_path}"
                )
                continue

            acquisition_time = pd.to_datetime(sidecar["AcquisitionTime"])

            doscan = data.loc[
                data["participant_id"].eq(participant_id)
                & data["session_id"].eq(session_id),
                "doscan",
            ].item()

            acq_time = doscan.replace(
                hour=acquisition_time.hour,
                minute=acquisition_time.minute,
                second=acquisition_time.second,
                microsecond=0,
            ).isoformat()

            scans.loc[i, "acq_time"] = acq_time

            logger.debug(f"Imputed acquisition time for {filename}: {acq_time}")

        remaining_missing = scans["acq_time"].eq("n/a").sum()

        logger.info(
            f"Finished acquisition-time imputation for {participant_id}, {session_id}; {remaining_missing} values remain missing"
        )

        return scans

    @staticmethod
    def add_missing_files(
        scans: pd.DataFrame,
        session_dir: Path,
    ) -> pd.DataFrame:
        """Add imaging files that are absent from a scans table.

        NIfTI files one directory below the session directory are compared with the filenames already present in the scans table. New files are added with an acquisition time of ``"n/a"``.

        Args:
            scans: Existing scans table containing a ``filename`` column.
            session_dir: Directory containing the session imaging files.

        Returns:
            The scans DataFrame with any previously unlisted NIfTI files appended.
        """
        logger.debug(
            f"Searching for imaging files missing from the scans table under {session_dir}"
        )

        filenames = pd.Series(
            f"{scan_path.parent.name}/{scan_path.name}"
            for scan_path in session_dir.glob("*/*.nii.gz")
        )

        new_filenames = filenames.loc[~(filenames.isin(scans["filename"]))]

        if new_filenames.empty:
            logger.debug(
                f"No imaging files are missing from the scans table under {session_dir}"
            )
            return scans

        logger.info(
            f"Adding {len(new_filenames)} imaging files to the scans table for {session_dir}"
        )

        return pd.concat(
            [
                scans,
                pd.DataFrame(
                    {
                        "filename": new_filenames,
                        "acq_time": "n/a",
                    }
                ),
            ],
            ignore_index=True,
        )
