from pathlib import Path

import pandas as pd
import numpy as np
import re

class SubjectsSessions():
    @classmethod
    def create(cls, references):
        imglook = cls.imglook(paths=references["imglook"]["paths"], map=references["imglook"]["map"])
        demographics = cls.demographics(references["demographics"])
        imaging_qc = cls.imaging_qc(references["imaging_qc"])
        subjects_sessions = cls.combine(imglook, demographics, imaging_qc)
        return subjects_sessions
    @staticmethod
    def combine(imglook, demographics, imaging_qc):
        return (
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
    @staticmethod
    def demographics(path):
        return (
            pd.read_csv(path)
            .rename(columns={"dob": "dobirth"}, errors="ignore")
            .loc[:, ["bblid", "dobirth"]]
            .assign(dobirth=lambda df: pd.to_datetime(df["dobirth"], errors="coerce"))
        )
    @staticmethod
    def imglook(paths, map):
        return (
            pd.concat([pd.read_csv(path) for path in paths], axis=0)
            .rename(columns=str.lower)
            .loc[
                lambda df: ~df["scanstat"].str.match(r"IS5\w?", na=True),
                ["bblid", "scanid", "protocol", "doscan"],
            ]
            .astype({"bblid": "Int64", "scanid": "Int64"})
            .assign(
                doscan=lambda df: pd.to_datetime(df["doscan"], errors="coerce"),
                protocol=lambda df: df["protocol"].replace(map),
            )
            .loc[lambda df: df["protocol"].isin(map.values()) & df.groupby(["bblid", "protocol"])["doscan"].transform("min").eq(df["doscan"]), :]
            .sort_values(["bblid", "scanid"])
            .reset_index(drop=True)
        )
    @staticmethod
    def imaging_qc(path):
        return (
            pd.read_csv(path)
            .pivot(index=["sub", "ses"], columns="hemi", values="euler")
            .reset_index()
            .assign(
                bblid=lambda df: df["sub"].str.extract(r"sub-(\d+)").astype("Int64"),
                protocol=lambda df: df["ses"].str.extract(r"ses-(\w+)"),
                euler=lambda df: df[["lh", "rh"]].sum(axis=1, min_count=2).astype("Int64")
            )
            .loc[:, ["bblid", "protocol", "euler"]]
        )

class FreeSurferCleaner():
    @classmethod
    def clean(cls, inputs, reference, lobes):
        return (
            pd.concat(
                [cls.clean_inner(reference=reference, **kwargs) for kwargs in inputs],
                axis=0
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
    @classmethod
    def clean_inner(cls, reference, path, atlas, metric_input=None, laterality_input=None, match_input=None):
        path = Path(path)
        df_raw = cls.read_table(path)
        metric_parsed, laterality_parsed, match_parsed, subject, session = cls.parse_head(df_raw)
        df_standard = cls.standardize_head(df_raw, reference, subject, session)
        laterality = cls.find_laterality(laterality_input, laterality_parsed, path)
        match = match_input if match_input is not None else match_parsed
        metric = cls.find_metric(metric_input, metric_parsed, path)
        cols = [col for col in df_standard.filter(regex=match).columns if col not in ["bblid", "scanid", "unknown"]]
        df_long = cls.wide_to_long(df_standard, cols, laterality, metric, atlas)
        return df_long
    @staticmethod
    def read_table(path):
        sep = "\t" if path.suffix == ".tsv" else ","
        df = pd.read_csv(path, sep=sep)
        return df
    @staticmethod
    def parse_head(df):
        PATTERN_APARC = re.compile(r"^(?P<hemisphere>[lr]h)\.aparc\.(?P<metric>\w+)$")
        PATTERN_ASEG = re.compile(r"Measure:(?P<metric>\w+)")
        columns = df.columns
        head = columns[0]
        match_aparc = PATTERN_APARC.match(head)
        match_aseg = PATTERN_ASEG.match(head)
        matches_subregions = "subject" in columns and "session" in columns
        if match_aparc:
            hemisphere, metric = match_aparc.groups()
            match = rf"_{metric}$"
            laterality = "left" if hemisphere == "lh" else "right" if hemisphere == "rh" else None
            subject, session = head, head
        elif match_aseg:
            metric = match_aseg.group("metric")
            metric = "lgi" if metric == "mean" else metric
            laterality = None
            match = r".*"
            subject, session = head, head
        elif matches_subregions:
            metric, laterality = None, None
            match = r".*"
            subject, session = "subject", "session"
        else:
            raise ValueError("Data frame header cannot be parsed")
        return metric, laterality, match, subject, session
    @staticmethod
    def wide_to_long(df, cols, laterality, metric, atlas):
        pattern_cortical = r"^[lr]h_(\w+)_\w+$"
        pattern_wmparc = r"^wm-[lr]h-(\w+)"
        pattern_subcortical = r"^(Left-|Right-|lh-|rh-)"
        return (
            df
            .melt(
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
            .loc[:, ["bblid", "scanid", "metric", "laterality", "region", "atlas", "value"]]
        )            
    @staticmethod
    def standardize_head(df, reference, subject, session):
        return (
            df.copy()
            .assign(
                bblid=lambda df: df[subject].str.extract(r"sub-(\d+)").astype("Int64"),
                protocol=lambda df: df[session].str.extract(r"ses-(\w+)")
            )
            .merge(reference.loc[:, ["bblid", "protocol", "scanid"]], on=["bblid", "protocol"], how="left")
            .drop({subject, session, "protocol"}, axis=1)
        )
    @staticmethod
    def find_laterality(laterality_input, laterality_parsed, path):
        laterality_match = re.search(r"(^[lr]h|[lr]h$)", path.stem)
        laterality_path = laterality_match.group(0) if laterality_match else None
        if laterality_input is not None:
            laterality = laterality_input
        elif laterality_parsed is not None:
            laterality = laterality_parsed
        elif laterality_path == "lh":
            laterality = "left"
        elif laterality_path == "rh":
            laterality = "right"
        else:
            laterality=lambda df: np.select(
                [
                    df["region"].str.match(r"^Left-|^(wm-)?lh", na=False),
                    df["region"].str.match(r"^Right-|^(wm-)?rh", na=False)
                ],
                ["left", "right"],
                default="bilateral"
            )
        return laterality
    @staticmethod
    def find_metric(metric_input, metric_parsed, path):
        metrics = ["area", "lgi", "meancurv", "thickness", "volume", "wm_volume"]
        if metric_input is not None:
            return metric_input
        if metric_parsed is not None:
            return metric_parsed
        for test_metric in metrics:
            if test_metric in path.stem.lower():
                return test_metric
        if "volume" in path.stem and "wm" in path.stem:
            return "wm_volume"
        raise ValueError("Data frame header cannot be parsed")