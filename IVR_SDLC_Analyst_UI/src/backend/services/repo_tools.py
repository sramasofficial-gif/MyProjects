from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = (
    Path(__file__).parent.parent
    / "ivr_repo"
).resolve()


def resolve_repository_file(relative_path):

    relative_path = relative_path.strip()

    path = (
        PROJECT_ROOT /
        relative_path
    ).resolve()

    path.relative_to(PROJECT_ROOT)

    return path

def find_files(extension=".json"):

    if not extension.startswith("."):
        extension = "." + extension

    return {
        "project_root": str(PROJECT_ROOT),
        "extension": extension,
        "files_found": [

            str(
                file.relative_to(PROJECT_ROOT)
            )

            for file in PROJECT_ROOT.rglob(
                f"*{extension}"
            )

            if file.is_file()
        ]
    }


def read_file(relative_path):

    file_path = resolve_repository_file(
        relative_path
    )

    return file_path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

def get_repo_tree():

    tree = defaultdict(list)

    for path in PROJECT_ROOT.rglob("*"):

        if not path.is_file():
            continue

        relative = path.relative_to(PROJECT_ROOT)

        folder = str(relative.parent)

        tree[folder].append(path.name)

    return [
        {
            "folder": folder,
            "files": files
        }
        for folder, files in tree.items()
    ]