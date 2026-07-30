import logging
from pathlib import Path

import pandas as pd
import numpy as np
import re

logger = logging.getLogger(__name__)


class FreeSurferCleaner:
    """Standardize FreeSurfer statistics into a long-format table.

    FreeSurfer tables from multiple atlases and metrics are read, matched to reference subject-session data, reshaped into a common format, and optionally mapped to anatomical lobes.
    """

    @classmethod
    def clean(
        cls, inputs: list[dict[str, str | Path]], reference: pd.DataFrame, lobes: Path
    ) -> pd.DataFrame:
        """Clean and combine multiple FreeSurfer statistics tables.

        Each input configuration is passed to :meth:`clean_inner`. The resulting tables are concatenated, sorted, and annotated with lobe labels for Desikan-Killiany regions.

        Args:
            inputs: Configurations describing the input path, atlas, and optional parsing overrides for each table.
            reference: Subject-session reference table containing ``bblid``, ``protocol``, and ``scanid`` columns.
            lobes: Path to a CSV file mapping cortical regions to lobes.

        Returns:
            A standardized long-format DataFrame containing atlas, metric, subject, session, region, laterality, value, and lobe information.
        """
        logger.info(f"Cleaning {len(inputs)} FreeSurfer input tables")

        cleaned = (
            pd.concat(
                [cls.clean_inner(reference=reference, **kwargs) for kwargs in inputs],
                axis=0,
            )
            .sort_values(["atlas", "metric", "bblid", "scanid", "region", "laterality"])
            .reset_index(drop=True)
            .assign(
                lobe=lambda df: (
                    df["region"]
                    .where(df["atlas"].eq("desikan_killiany"))
                    .map(pd.read_csv(lobes).set_index("region")["lobe"].to_dict())
                )
            )
        )

        logger.info(f"Created {len(cleaned)} standardized FreeSurfer rows")

        return cleaned

    @classmethod
    def clean_inner(
        cls,
        reference: pd.DataFrame,
        path: str,
        atlas: str,
        metric_input=None,
        laterality_input=None,
        match_input=None,
    ) -> pd.DataFrame:
        """Clean one FreeSurfer statistics table.

        The table format is inferred from its header. Subject and session identifiers are standardized, the metric and laterality are resolved, matching measurement columns are selected, and the table is converted to long format.

        Args:
            reference: Subject-session reference table containing ``bblid``, ``protocol``, and ``scanid`` columns.
            path: Path to the FreeSurfer statistics table.
            atlas: Atlas name assigned to the output rows.
            metric_input: Optional metric overriding the parsed or filename-derived metric.
            laterality_input: Optional laterality overriding parsed or filename-derived laterality.
            match_input: Optional regular expression selecting the measurement columns.

        Returns:
            A standardized long-format DataFrame for the input table.
        """
        logger.info(f"Cleaning FreeSurfer table {path}")

        path = Path(path)
        df_raw = pd.read_csv(path, sep="\t")

        (metric_parsed, laterality_parsed, match_parsed, subject, session) = (
            cls.parse_head(df_raw)
        )

        logger.debug(
            f"Parsed {path}: metric={metric_parsed!r}, laterality={laterality_parsed!r}, match={match_parsed!r}"
        )

        df_standard = cls.standardize_head(df_raw, reference, subject, session)
        laterality = cls.find_laterality(laterality_input, laterality_parsed, path)
        match = match_input if match_input is not None else match_parsed
        metric = cls.find_metric(metric_input, metric_parsed, path)

        cols = [
            col
            for col in df_standard.filter(regex=match).columns
            if col not in ["bblid", "scanid", "unknown"]
        ]
        logger.debug(f"Selected {len(cols)} measurement columns from {path}")

        df_long = cls.wide_to_long(df_standard, cols, laterality, metric, atlas)
        logger.info(f"Cleaned {path} into {len(df_long)} long-format rows")

        return df_long

    @staticmethod
    def parse_head(df: pd.DataFrame) -> tuple[str]:
        """Infer table metadata from its column headers.

        Cortical parcellation tables are identified by an
        ``lh.aparc`` or ``rh.aparc`` first column. Aseg-style tables
        are identified by a first column beginning with ``Measure:``.
        Subregion tables are identified by explicit ``subject`` and
        ``session`` columns.

        Args:
            df: Raw FreeSurfer statistics table.

        Returns:
            A tuple containing the metric, laterality, column-matching
            regular expression, subject column, and session column.

        Raises:
            ValueError: If the table format cannot be inferred from its
                headers.
        """
        PATTERN_APARC = re.compile(r"^(?P<hemisphere>[lr]h)\.aparc\.(?P<metric>\w+)$")
        PATTERN_ASEG = re.compile(r"Measure:(?P<metric>\w+)")

        columns = df.columns
        head = columns[0]

        logger.debug(f"Parsing FreeSurfer table header beginning with {head!r}")

        match_aparc = PATTERN_APARC.match(head)
        match_aseg = PATTERN_ASEG.match(head)
        matches_subregions = "subject" in columns and "session" in columns

        if match_aparc:
            hemisphere, metric = match_aparc.groups()
            match = rf"_{metric}$"
            laterality = (
                "left"
                if hemisphere == "lh"
                else "right" if hemisphere == "rh" else None
            )
            subject, session = head, head

            logger.debug(
                f"Identified aparc table with hemisphere {hemisphere} and metric {metric}"
            )

        elif match_aseg:
            metric = match_aseg.group("metric")
            metric = "lgi" if metric == "mean" else metric
            laterality = None
            match = r".*"
            subject, session = head, head

            logger.debug(f"Identified aseg-style table with metric {metric}")

        elif matches_subregions:
            metric, laterality = None, None
            match = r".*"
            subject, session = "subject", "session"

            logger.debug(
                "Identified subregion table with explicit subject and session columns"
            )

        else:
            raise ValueError("Data frame header cannot be parsed")

        return metric, laterality, match, subject, session

    @staticmethod
    def wide_to_long(
        df: pd.DataFrame, cols: list[str], laterality: str, metric: str, atlas: str
    ) -> pd.DataFrame:
        """Convert a standardized FreeSurfer table to long format.

        Measurement columns are melted into region-value pairs.
        Cortical, white-matter, and subcortical naming conventions are
        standardized by removing metric and laterality components from
        region names.

        Args:
            df: Standardized wide-format FreeSurfer table.
            cols: Measurement columns to reshape.
            laterality: Laterality value or callable used to populate
                the output laterality column.
            metric: Metric assigned to the output rows.
            atlas: Atlas assigned to the output rows.

        Returns:
            A long-format DataFrame with one row per subject, session,
            and region measurement.
        """
        logger.debug(
            f"Converting {len(df)} rows and {len(cols)} measurement columns to long format for atlas {atlas}"
        )

        pattern_cortical = r"^[lr]h_(\w+)_\w+$"
        pattern_wmparc = r"^wm-[lr]h-(\w+)"
        pattern_subcortical = r"^(Left-|Right-|lh-|rh-)"

        df_long = (
            df.melt(
                id_vars=["bblid", "scanid"],
                value_vars=cols,
                var_name="region",
                value_name="value",
            )
            .assign(
                metric=metric,
                laterality=laterality,
                region=lambda df: np.select(
                    [
                        df["region"].str.match(pattern_cortical, na=False),
                        df["region"].str.match(pattern_wmparc, na=False),
                        df["region"].str.match(pattern_subcortical, na=False),
                    ],
                    [
                        df["region"].str.extract(pattern_cortical, expand=False),
                        df["region"].str.extract(pattern_wmparc, expand=False),
                        df["region"].str.replace(pattern_subcortical, "", regex=True),
                    ],
                    default=df["region"],
                ),
                atlas=atlas,
            )
            .loc[
                :,
                ["bblid", "scanid", "metric", "laterality", "region", "atlas", "value"],
            ]
        )

        logger.debug(f"Converted FreeSurfer table into {len(df_long)} long-format rows")

        return df_long

    @staticmethod
    def standardize_head(
        df: pd.DataFrame, reference: pd.DataFrame, subject: str, session: str
    ) -> pd.DataFrame:
        """Standardize subject and session identifier columns.

        BIDS subject and protocol labels are extracted from the
        specified columns. The protocol is then matched to the reference
        table to obtain the corresponding scan identifier.

        Args:
            df: Raw FreeSurfer statistics table.
            reference: Subject-session reference table containing
                ``bblid``, ``protocol``, and ``scanid`` columns.
            subject: Column containing the BIDS participant label.
            session: Column containing the BIDS session label.

        Returns:
            A DataFrame containing standardized ``bblid`` and
            ``scanid`` columns.
        """
        logger.debug(
            f"Standardizing subject column {subject!r} and session column {session!r} for {len(df)} rows"
        )

        standardized = (
            df.copy()
            .assign(
                bblid=lambda df: df[subject].str.extract(r"sub-(\d+)").astype("Int64"),
                protocol=lambda df: df[session].str.extract(r"ses-(\w+)"),
            )
            .merge(
                reference.loc[:, ["bblid", "protocol", "scanid"]],
                on=["bblid", "protocol"],
                how="left",
            )
            .drop({subject, session, "protocol"}, axis=1)
        )

        return standardized

    @staticmethod
    def find_laterality(
        laterality_input: str, laterality_parsed: str, path: Path
    ) -> str:
        """Resolve laterality from input, headers, or the filename.

        Explicit input laterality takes precedence over header-derived
        laterality. If neither is available, the filename is inspected
        for an ``lh`` or ``rh`` marker. Otherwise, laterality is
        inferred separately for each region.

        Args:
            laterality_input: Optional explicitly configured
                laterality.
            laterality_parsed: Laterality parsed from the table header.
            path: Path used to inspect the filename for laterality.

        Returns:
            A laterality label or a callable that derives laterality
            from region names.
        """
        laterality_match = re.search(r"(^[lr]h|[lr]h$)", path.stem)
        laterality_path = laterality_match.group(0) if laterality_match else None

        if laterality_input is not None:
            laterality = laterality_input
            logger.debug(f"Using configured laterality {laterality!r} for {path}")

        elif laterality_parsed is not None:
            laterality = laterality_parsed
            logger.debug(f"Using header-derived laterality {laterality!r} for {path}")

        elif laterality_path == "lh":
            laterality = "left"
            logger.debug(f"Inferred left laterality from filename {path.name}")

        elif laterality_path == "rh":
            laterality = "right"
            logger.debug(f"Inferred right laterality from filename {path.name}")

        else:
            laterality = lambda df: np.select(
                [
                    df["region"].str.match(r"^Left-|^(wm-)?lh", na=False),
                    df["region"].str.match(r"^Right-|^(wm-)?rh", na=False),
                ],
                ["left", "right"],
                default="bilateral",
            )
            logger.debug(f"Laterality will be inferred from region names for {path}")

        return laterality

    @staticmethod
    def find_metric(metric_input: str, metric_parsed: str, path: Path) -> str:
        """Resolve the metric from input, headers, or the filename.

        Explicit input takes precedence over the metric parsed from the
        table header. If neither is available, supported metric names
        are searched for in the filename.

        Args:
            metric_input: Optional explicitly configured metric.
            metric_parsed: Metric parsed from the table header.
            path: Path used to inspect the filename for a metric.

        Returns:
            The resolved metric name.

        Raises:
            ValueError: If no metric can be resolved.
        """
        metrics = ["area", "lgi", "meancurv", "thickness", "wm_volume", "volume"]

        if metric_input is not None:
            logger.debug(f"Using configured metric {metric_input!r} for {path}")
            return metric_input

        if metric_parsed is not None:
            logger.debug(f"Using header-derived metric {metric_parsed!r} for {path}")
            return metric_parsed

        for test_metric in metrics:
            if test_metric in path.stem.lower():
                logger.debug(f"Inferred metric {test_metric!r} from {path.name}")
                return test_metric

        if "volume" in path.stem and "wm" in path.stem:
            logger.debug(f"Inferred metric 'wm_volume' from {path.name}")
            return "wm_volume"

        raise ValueError("Data frame header cannot be parsed")
