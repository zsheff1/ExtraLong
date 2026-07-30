import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


class SubjectsSessions:
    """Create a combined subject-session metadata table.

    Imaging lookup records, participant demographics, and imaging quality control measurements are standardized and combined into one table with participant, scan, protocol, age, and Euler number information.
    """

    @classmethod
    def create(cls, references: dict[str, Path]) -> pd.DataFrame:
        """Create the combined subject-session metadata table.

        Args:
            references: Mapping containing paths for ``imglook``, ``demographics``, and ``imaging_qc`` source data. The ``imglook`` value is expected to contain a list of paths.

        Returns:
            A DataFrame containing participant identifiers, scan identifiers, protocols, ages in months, and Euler numbers.
        """
        logger.info("Creating subject-session metadata")

        logger.info("Processing imaging lookup data")
        imglook = cls.imglook(paths=references["imglook"])

        logger.info("Processing demographic data")
        demographics = cls.demographics(references["demographics"])

        logger.info("Processing imaging quality-control data")
        imaging_qc = cls.imaging_qc(references["imaging_qc"])

        logger.info(
            "Combining imaging lookup, demographics, imaging quality-control data"
        )
        subjects_sessions = cls.combine(imglook, demographics, imaging_qc)

        logger.info(f"Created subject-session table with {len(subjects_sessions)} rows")

        return subjects_sessions

    @staticmethod
    def combine(
        imglook: pd.DataFrame, demographics: pd.DataFrame, imaging_qc: pd.DataFrame
    ) -> pd.DataFrame:
        """Combine imaging, demographic, and quality-control data.

        Demographic records are joined to imaging lookup records by participant identifier. Imaging quality-control records are then joined by participant identifier and protocol. Age at scan is calculated in completed months.

        Args:
            imglook: Imaging lookup data containing participant, scan, protocol, and scan-date information.
            demographics: Demographic data containing participant identifiers and dates of birth.
            imaging_qc: Imaging quality-control data containing participant identifiers, protocols, and Euler numbers.

        Returns:
            A DataFrame containing ``bblid``, ``scanid``, ``protocol``, ``age``, and ``euler`` columns.
        """
        logger.debug(
            f"Combining {len(imglook)} imaging lookup rows, {len(demographics)} demographic rows, and {len(imaging_qc)} imaging QC rows"
        )

        combined = (
            pd.merge(demographics, imglook, how="outer", on="bblid")
            .merge(imaging_qc, how="right", on=["bblid", "protocol"])
            .assign(
                age=lambda df: (
                    (df["doscan"].dt.year - df["dobirth"].dt.year) * 12
                    + (df["doscan"].dt.month - df["dobirth"].dt.month)
                    - (df["doscan"].dt.day < df["dobirth"].dt.day)
                )
            )
            .astype({"age": "Int64"})
            .loc[:, ["bblid", "scanid", "protocol", "age", "euler"]]
        )

        logger.info(f"Combined source data into {len(combined)} subject-session rows")

        return combined

    @staticmethod
    def demographics(path: Path) -> pd.DataFrame:
        """Read and standardize participant demographic data.

        The date-of-birth column is renamed to ``dobirth`` when needed and converted to a pandas datetime type.

        Args:
            path: Path to the demographic CSV file.

        Returns:
            A DataFrame containing ``bblid`` and ``dobirth`` columns.
        """
        logger.debug(f"Reading demographic data from {path}")

        demographics = (
            pd.read_csv(path)
            .rename(columns={"dob": "dobirth"}, errors="ignore")
            .loc[:, ["bblid", "dobirth"]]
            .assign(dobirth=lambda df: pd.to_datetime(df["dobirth"], errors="coerce"))
        )

        logger.info(f"Read {len(demographics)} demographic records from {path}")

        return demographics

    @staticmethod
    def imglook(
        path: Path,
    ) -> pd.DataFrame:
        """Read and standardize imaging lookup data.

        Imaging lookup file is read, invalid scan-status records are removed, identifier columns are converted to nullable integers, and scan dates are parsed. When a participant has multiple records for the same protocol, only records from the earliest scan date are retained.

        Args:
            path: Path to imaging lookup CSV file.

        Returns:
            A DataFrame containing ``bblid``, ``scanid``, ``protocol``, and ``doscan`` columns.
        """
        logger.info(f"Reading imaging lookup data from {path}")

        imglook = (
            pd.read_csv(path)
            .rename(columns=str.lower)
            .loc[
                lambda df: ~df["scanstat"].str.match(r"IS5\w?", na=True),
                ["bblid", "scanid", "protocol", "doscan"],
            ]
            .astype({"bblid": "Int64", "scanid": "Int64"})
            .assign(doscan=lambda df: pd.to_datetime(df["doscan"], errors="coerce"))
            .loc[
                lambda df: df.groupby(["bblid", "protocol"])["doscan"]
                .transform("min")
                .eq(df["doscan"]),
                :,
            ]
            .sort_values(["bblid", "scanid"])
            .reset_index(drop=True)
        )

        logger.info(f"Imaging lookup processing retained {len(imglook)} rows")

        return imglook

    @staticmethod
    def imaging_qc(path: Path) -> pd.DataFrame:
        """Read and standardize imaging quality-control data.

        Hemisphere-specific Euler numbers are pivoted into separate columns and summed to create one bilateral Euler number for each participant and protocol.

        Args:
            path: Path to the imaging quality-control CSV file.

        Returns:
            A DataFrame containing ``bblid``, ``protocol``, and ``euler`` columns.
        """
        logger.debug(f"Reading imaging quality-control data from {path}")

        imaging_qc = (
            pd.read_csv(path)
            .pivot(index=["sub", "ses"], columns="hemi", values="euler")
            .reset_index()
            .assign(
                bblid=lambda df: df["sub"].str.extract(r"sub-(\d+)").astype("Int64"),
                protocol=lambda df: df["ses"].str.extract(r"ses-(\w+)"),
                euler=lambda df: df[["lh", "rh"]]
                .sum(axis=1, min_count=2)
                .astype("Int64"),
            )
            .loc[:, ["bblid", "protocol", "euler"]]
        )

        logger.info(
            f"Read {len(imaging_qc)} imaging quality-control records from {path}"
        )

        return imaging_qc
