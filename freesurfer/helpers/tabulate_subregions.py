#!/usr/bin/env python3

import argparse
import os
from pathlib import Path
import re

import pandas as pd


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tabulate hippocampal/amygdala subregion stats across subjects."
    )

    parser.add_argument(
        "-f",
        "--file",
        action="append",
        required=True,
        help="Input stats file basename. Can be specified multiple times.",
    )

    parser.add_argument(
        "-o", "--output-dir", type=Path, required=True, help="Output directory."
    )

    return parser.parse_args()


class TabulateSubregions:
    SUB_PATTERN = re.compile(r"sub-\d{6}")
    SES_PATTERN = re.compile(r"ses-\d{5}")
    LONG_PATTERN = re.compile(r"sub-\d{6}_ses-\d{5}\.long\.sub-\d{6}")

    def __init__(self, input_dir: Path) -> None:
        self.input_dir = input_dir
        with open(input_dir / "subjectsfile.txt", "r") as f:
            self.subjects = [line.strip() for line in f if line.strip()]

    def tabulate(self, basename: str, output_dir: Path) -> None:
        table = self.create_table(self.input_dir, self.subjects, basename)
        self.write_table(table, output_dir, basename)

    @classmethod
    def write_table(table: pd.DataFrame, output_dir: Path, basename: str) -> None:
        output_dir.mkdir(parents=True, exist_ok=True)
        path = (output_dir / basename).with_suffix("tsv")
        table.to_csv(path, sep="\t", index=False)

    @classmethod
    def create_table(
        cls, input_dir: Path, subject_dirs: list[str], basename: str
    ) -> pd.DataFrame:
        subject_dfs = []

        for subject_dir in subject_dirs:
            subject, session = cls.parse_subject_session(subject_dir)

            if cls.LONG_PATTERN.match(subject_dir):
                input_basename = basename.replace(".txt", ".long.txt")
            else:
                input_basename = basename

            input_path = input_dir / subject_dir / "mri" / input_basename

            subject_dfs.append(cls.read_stats_file(input_path, subject, session))

        return pd.concat(subject_dfs, ignore_index=True)

    @classmethod
    def parse_subject_session(cls, subject_dir: Path) -> tuple[str]:
        sub_match = cls.SUB_PATTERN.search(subject_dir)
        ses_match = cls.SES_PATTERN.search(subject_dir)

        if sub_match is None:
            raise ValueError(f"Could not find subject ID in: {subject_dir}")

        if ses_match is None:
            raise ValueError(f"Could not find session ID in: {subject_dir}")

        return sub_match.group(), ses_match.group()

    @staticmethod
    def read_stats_file(input_path: Path, subject: str, session: str) -> pd.DataFrame:
        return (
            pd.read_csv(input_path, sep=r"\s+", header=None, names=["region", "value"])
            .set_index("region")["value"]
            .to_frame()
            .T.reset_index(drop=True)
            .rename_axis(columns=None)
            .assign(subject=subject, session=session)
            .loc[
                :,
                lambda df: [
                    "subject",
                    "session",
                    *df.columns.difference(["subject", "session"], sort=False),
                ],
            ]
        )


def main() -> None:
    args = parse_args()

    tabulate_subregions = TabulateSubregions(
        input_dir=Path(os.environ["SUBJECTS_DIR"]),
        output_dir=args.output_dir,
        files=args.file,
    )

    for basename in args.file:
        tabulate_subregions.tabulate(basename, args.output_dir)


if __name__ == "__main__":
    main()
