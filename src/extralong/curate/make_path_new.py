import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def make_path_new(df: pd.DataFrame, root: Path) -> pd.Series:
    """Construct standardized destination paths for imaging sessions.

    Each row is converted into a BIDS-style T1-weighted NIfTI path using
        its ``bblid`` and ``scanid`` values. Subject identifiers are
        zero-padded to six digits and scan identifiers are zero-padded
        to five digits.

    Args:
        df: DataFrame containing integer-like ``bblid`` and ``scanid``
            columns.
        root: Root directory under which the subject and session
            directories are created.

    Returns:
        A Series of destination paths aligned to the input's index.
    """
    logger.debug(f"Constructing {len(df)} standardized destination paths under {root}")
    return pd.Series(
        [
            root
            / f"sub-{bblid:06d}"
            / f"ses-{scanid:05d}"
            / "anat"
            / f"sub-{bblid:06d}_ses-{scanid:05d}_T1w.nii.gz"
            for bblid, scanid in zip(df["bblid"], df["scanid"])
        ],
        index=df.index,
    )
