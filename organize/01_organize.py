import argparse
import json
from pathlib import Path

from extralong.organize import SubjectsSessions, FreeSurferCleaner

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("config", type=Path, help="Path to config JSON")
args = parser.parse_args()

with open(args.config) as f:
    config = json.load(f)

# imaging data
subjects_sessions = SubjectsSessions.create(references=config["references"])
imaging_data = FreeSurferCleaner.clean(inputs=config["inputs"], reference=subjects_sessions, lobes=config["references"]["lobes"])

exports = [
    {"path": "subjects_sessions.csv", "data": subjects_sessions},
    {"path": "imaging_data.csv", "data": imaging_data}
]

Path(config["out_dir"]).mkdir(exist_ok=True, parents=True)

for export in exports:
    export["data"].to_csv(Path(config["out_dir"]) / export["path"], index=False)
