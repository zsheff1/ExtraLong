#!/usr/bin/env python3

import argparse
import csv
import os
from pathlib import Path
import re


SUB_PATTERN = re.compile(r"sub-\d{6}")
SES_PATTERN = re.compile(r"ses-\w{3,4}1")
LONG_PATTERN = re.compile(r"sub-\d{6}_ses-\w{3,4}1\.long\.sub-\d{6}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Tabulate hippocampal/amygdala subregion stats across subjects."
    )

    parser.add_argument(
        "-f", "--file",
        action="append",
        required=True,
        help="Input stats file basename. Can be specified multiple times."
    )

    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        required=True,
        help="Output directory."
    )

    return parser.parse_args()


def read_subjects(subjectsfile):
    with open(subjectsfile, "r") as f:
        return [line.strip() for line in f if line.strip()]


def parse_subject_session(subject_dir):
    sub_match = SUB_PATTERN.search(subject_dir)
    ses_match = SES_PATTERN.search(subject_dir)

    if sub_match is None:
        raise ValueError(f"Could not find subject ID in: {subject_dir}")

    if ses_match is None:
        raise ValueError(f"Could not find session ID in: {subject_dir}")

    return sub_match.group(), ses_match.group()


def read_stats_file(path):
    rows = []

    with open(path, "r") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            region, value = line.split()
            rows.append((region, value))

    return rows


def tabulate_one_file(input_dir, subjects, basename, output_dir):
    regions = []
    seen_regions = set()
    rows_by_subject_session = {}

    for subject_dir in subjects:
        subject, session = parse_subject_session(subject_dir)

        if LONG_PATTERN.match(subject_dir):
            input_basename = basename.replace(".txt", ".long.txt")
        else:
            input_basename = basename

        input_path = input_dir / subject_dir / "mri" / input_basename

        values = {}

        for region, value in read_stats_file(input_path):
            values[region] = value

            if region not in seen_regions:
                seen_regions.add(region)
                regions.append(region)

        rows_by_subject_session[(subject, session)] = values

    output_path = output_dir / basename.replace(".txt", ".csv")

    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)

        writer.writerow(["subject", "session"] + regions)

        for subject, session in rows_by_subject_session:
            values = rows_by_subject_session[(subject, session)]

            writer.writerow(
                [subject, session] + [values.get(region, "") for region in regions]
            )


def main():
    args = parse_args()

    input_dir = Path(os.environ["SUBJECTS_DIR"])
    subjectsfile = input_dir / "subjectsfile.txt"

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    subjects = read_subjects(subjectsfile)

    for basename in args.file:
        tabulate_one_file(
            input_dir=input_dir,
            subjects=subjects,
            basename=basename,
            output_dir=output_dir,
        )


if __name__ == "__main__":
    main()