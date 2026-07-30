import logging
from pathlib import Path
import shutil
import subprocess
from zipfile import ZipFile

import pandas as pd
import flywheel

PATH_SCRIPT = (
    Path("/") / "project" / "ExtraLong" / "code" / "curate" / "helpers" / "convert.sh"
)
PATH_OUT = Path("/") / "project" / "ExtraLong"
PATH_HEURISTICS = Path("/") / "project" / "ExtraLong" / "code" / "curate" / "assets"

logger = logging.getLogger(__name__)


def download_uncurated(
    remaining: pd.DataFrame,
    fw: flywheel.Client,
    dir_scratch: Path,
    stem: str,
    protocol: str,
    project_label: str,
    heuristic: str | None = None,
    sample: bool = False,
) -> None:
    """Download and convert uncurated Flywheel imaging sessions.

    Sessions belonging to the requested protocol are located in a Flywheel project, downloaded as ZIP archives, extracted into a temporary directory, and moved into a standardized intermediate directory structure. Each session is then passed to the conversion script to produce curated output.

    Session lookup first uses the configured session label and then retries after replacing underscores with slashes. Sessions that cannot be found under either label are reported and skipped.

    Args:
        remaining: DataFrame containing sessions that have not yet been curated. Expected columns include ``protocol``, ``bblid``, ``scanid``, and ``sourceid``.
        fw: Authenticated Flywheel client.
        dir_scratch: Scratch directory in which downloads and extracted files are temporarily stored.
        stem: Name used by the conversion script to identify the calling pipeline or output group.
        protocol: Protocol whose sessions should be selected from ``remaining``.
        project_label: Flywheel project label from which sessions should be downloaded.
        heuristic: Filename of the heuristic passed to the conversion script.
        sample: If ``True``, process a reproducible random sample of three sessions rather than all matching sessions.

    Raises:
        flywheel.rest.ApiException: If a Flywheel lookup fails for a reason other than the session not being found.
        RuntimeError: If an extracted session directory does not have the expected structure.
        subprocess.CalledProcessError: If the conversion script exits with a nonzero status.

    Notes:
        The temporary project directory is deleted after all selected sessions have been processed. Sessions that cannot be found in Flywheel are skipped rather than treated as fatal errors.
    """
    logger.info(
        f"Downloading uncurated sessions for protocol {protocol} from Flywheel project {project_label}"
    )

    dir_tmp = dir_scratch / f"tmp_{project_label}"
    dir_inner = dir_tmp / "scitran" / "bbl" / project_label
    dir_final = dir_scratch / project_label

    logger.debug(f"Using temporary directory {dir_tmp} and final directory {dir_final}")

    dir_tmp.mkdir(parents=True, exist_ok=True)
    dir_final.mkdir(parents=True, exist_ok=True)

    remaining_subset = (
        remaining.loc[remaining["protocol"].eq(protocol), :]
        .astype({"bblid": "Int64", "scanid": "Int64"})
        .astype({"bblid": "string", "scanid": "string"})
        .assign(
            sub_ses=lambda df: df["bblid"] + "_" + df["scanid"],
            session_label=lambda df: df["sourceid"].fillna(df["sub_ses"]),
        )
        .loc[:, ["bblid", "scanid", "session_label", "sub_ses"]]
    )

    logger.info(
        f"Found {len(remaining_subset)} uncurated sessions for protocol {protocol}"
    )

    if sample:
        remaining_subset = remaining_subset.sample(n=3, random_state=42)
        logger.info(
            f"Sampling {len(remaining_subset)} uncurated sessions with random state 42"
        )

    for bblid, scanid, session_label, sub_ses in remaining_subset.itertuples(
        index=False, name=None
    ):
        logger.info(
            f"Processing subject {bblid}, scan {scanid} from Flywheel project {project_label}"
        )

        candidate_labels = [session_label, session_label.replace("_", "/")]
        for candidate_label in candidate_labels:
            lookup_path = f"bbl/{project_label}/{candidate_label}"
            logger.debug(f"Looking up Flywheel session {lookup_path}")

            try:
                session = fw.lookup(lookup_path)
                logger.debug(f"Found Flywheel session {lookup_path}")
                break
            except flywheel.rest.ApiException as error:
                if error.status != 404:
                    logger.exception(f"Flywheel lookup failed for {lookup_path}")
                    raise
                logger.debug(f"Flywheel session was not found at {lookup_path}")
        else:
            logger.warning(f"Session not found: {', '.join(candidate_labels)}")
            continue

        destination = dir_tmp / f"{sub_ses}.zip"

        logger.debug(f"Downloading Flywheel session {session.id} to {destination}")
        fw.download_zip(session, str(destination))

        logger.debug(f"Extracting {destination} into {dir_tmp}")
        with ZipFile(destination, "r") as zip_file:
            zip_file.extractall(dir_tmp)
        path_new = dir_final / sub_ses
        if "/" in candidate_label:
            path_old = dir_inner / candidate_label
        else:
            paths_old = list((dir_inner / candidate_label).iterdir())
            if len(paths_old) == 1:
                path_old = paths_old[0]
            else:
                raise RuntimeError(
                    f"Expected directory structure violated: {str(dir_inner / candidate_label)}"
                )

        logger.debug(f"Moving extracted session from {path_old} to {path_new}")

        shutil.move(path_old, path_new)

        logger.info(
            f"Converting subject {bblid}, scan {scanid} with heuristic {heuristic}"
        )

        subprocess.run(
            [
                str(PATH_SCRIPT),
                "--input",
                str(path_new),
                "--output",
                str(PATH_OUT),
                "--heuristic",
                str(PATH_HEURISTICS / heuristic),
                "--subject",
                str(bblid).zfill(6),
                "--session",
                str(scanid).zfill(5),
                "--stem",
                stem,
            ],
            check=True,
        )

        logger.info(f"Finished converting subject {bblid}, scan {scanid}")

    logger.debug(f"Removing temporary directory {dir_tmp}")
    shutil.rmtree(dir_tmp)

    logger.info(
        f"Finished downloading and converting uncurated sessions from Flywheel project {project_label}"
    )
