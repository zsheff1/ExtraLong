import json
from pathlib import Path

import pandas as pd

class Scans:
    def __init__(
        self,
        data: pd.DataFrame,
        path_project: Path,
    ) -> None:
        self.data = data
        self.path_project = path_project

    def method(
        self,
        participant_id: str,
        session_id: str,
    ) -> pd.DataFrame:
        session_dir = self.path_project / participant_id / session_id
        scans_name = f"{participant_id}_{session_id}_scans.tsv"
        scans_path = session_dir / scans_name
        if scans_path.exists():
            scans = pd.read_csv(scans_path, sep="\t", usecols=["filename", "acq_time"])
        else:
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
        return scans

    @staticmethod
    def anonymize_acq_time(
        participant_id: str,
        session_id: str,
        acq_time: pd.Series,
        data: pd.DataFrame,
    ) -> pd.Series:
        ANON_DOB = pd.to_datetime("1900-01-01")
        acq_time = pd.to_datetime(acq_time, errors="coerce")
        age_months = data.loc[
            lambda df: df["participant_id"].eq(participant_id)
            & df["session_id"].eq(session_id),
            "age",
        ].item()
        anon_age = pd.DateOffset(months=age_months)
        anon_scandate = ANON_DOB + anon_age
        return acq_time.map(
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

    @staticmethod
    def impute_acq_time(
        scans: pd.DataFrame,
        session_dir: Path,
        participant_id: str,
        session_id: str,
        data: pd.DataFrame,
    ) -> pd.DataFrame:
        indices = scans.index[scans["acq_time"].eq("n/a")]
        if indices.empty:
            return scans
        for i in indices:
            filename = scans.loc[i, "filename"]
            sidecar_path = (session_dir / filename).with_suffix("").with_suffix(".json")
            if not sidecar_path.exists():
                continue
            with open(sidecar_path, "r") as file:
                sidecar = json.load(file)
            if "AcquisitionTime" not in sidecar:
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
        return scans

    @staticmethod
    def add_missing_files(
        scans: pd.DataFrame,
        session_dir: Path,
    ) -> pd.DataFrame:
        filenames = pd.Series(
            f"{scan_path.parent.name}/{scan_path.name}"
            for scan_path in session_dir.glob("*/*.nii.gz")
        )
        new_filenames = filenames.loc[~(filenames.isin(scans["filename"]))]
        if new_filenames.empty:
            return scans
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