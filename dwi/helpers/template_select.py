#!/usr/bin/env python3

import re
from pathlib import Path

import pandas as pd
import numpy as np

from extralong.config import load_project_paths

paths = load_project_paths()
PROJECT_PATH = paths["PROJECT_DIR"]

DERIVATIVES_PATH = PROJECT_PATH / "derivatives"
DWI_DIR = DERIVATIVES_PATH / "dwi"
QC_PATH = DWI_DIR / "qc" / "tsnr_b0.csv"
TEMPLATE_DIR = DWI_DIR / "template"
PARTICIPANTS_PATH = PROJECT_PATH / "participants.tsv"

SUB_PATTERN = re.compile(r"sub-\d{6}")

def select_from_bin(group, bin_label):
    group = group.sort_values("tsnr_b0", ascending=False).copy()
    n = len(group)
    top_n = (n // 2) + (n % 2)
    return group.assign(
        select=[True] * top_n + [False] * (n - top_n) if n >= 5 else [False] * n,
        build=[True] + [False] * (n - 1) if n < 5 else [False] * n,
        bin=bin_label,
    )

participants = pd.read_csv(PARTICIPANTS_PATH, sep="\t")

sessions = pd.concat(
    [
        (
            pd.read_csv(session, sep="\t").assign(
                participant_id=SUB_PATTERN.search(session.name).group()
            )
        )
        for session in PROJECT_PATH.glob("sub-*/sub-*_sessions.tsv")
    ],
    ignore_index=True,
).assign(age=lambda df: df["age"] // 12)

# qc = pd.read_csv(QC_PATH)

images = (
    sessions
    .merge(participants, how="left", on="participant_id")
    # .merge(qc, how = "left", on = ["participant_id", "session_id"])
    .assign(
        bin=lambda df: df["age"].astype("str").str.zfill(2)
        + df["sex"].str.upper().str[0],
        dtitk_path=lambda df: DWI_DIR
        / df["participant_id"]
        / df["session_id"]
        / "dwi"
        / (df["participant_id"] + "_" + df["session_id"] + ".nii.gz"),
        fa_path=lambda df: DWI_DIR
        / df["participant_id"]
        / df["session_id"]
        / "dwi"
        / (df["participant_id"] + "_" + df["session_id"] + "_FA.nii.gz"),
        tsnr_b0=lambda df: np.random.random(len(df)),
    )
    # .loc[lambda df: df["dtitk_path"].map(Path.exists), :]
    .groupby("bin", group_keys=False)
    .apply(lambda g: select_from_bin(g, g.name), include_groups=False)
    .loc[:, ["bin", "select", "build", "dtitk_path", "fa_path"]]
    .sort_values(["bin", "dtitk_path"])
    .reset_index(drop=True)
)

TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

images.to_csv(TEMPLATE_DIR / "selection.csv", index=False)
