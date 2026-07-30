import logging
from pathlib import Path

PATH_CODE = Path(__file__).resolve().parents[2]
PATH_PROJECT_ENV = PATH_CODE / "config" / "project.env"

logger = logging.getLogger(__name__)


def load_project_paths(
    path: Path = PATH_PROJECT_ENV,
) -> dict[str, Path]:
    """Load project paths from an environment-style configuration file.

    Blank lines and lines beginning with ``#`` are ignored. Each remaining line is split at the first equals sign, and its value is converted to a ``Path``.

    Args:
        path: Path to the environment-style configuration file.

    Returns:
        A dictionary mapping configuration variable names to paths.
    """
    logger.debug(f"Loading project paths from {path}")

    values: dict[str, Path] = {}

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        key, value = line.split("=", maxsplit=1)
        values[key.strip()] = Path(value.strip())

    logger.info(f"Loaded {len(values)} project paths from {path}")

    return values
