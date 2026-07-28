from pathlib import Path


PATH_CODE = Path(__file__).resolve().parents[2]
PATH_PROJECT_ENV = PATH_CODE / "config" / "project.env"


def load_project_paths(
    path: Path = PATH_PROJECT_ENV,
) -> dict[str, Path]:
    values: dict[str, Path] = {}

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        key, value = line.split("=", maxsplit=1)
        values[key.strip()] = Path(value.strip())

    return values