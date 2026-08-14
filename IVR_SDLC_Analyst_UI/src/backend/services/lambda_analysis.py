from services.repo_tools import read_file


def analyze_lambda(relative_path):

    content = read_file(
        relative_path
    )

    imports = []

    for line in content.splitlines():

        if line.startswith("import "):
            imports.append(line.strip())

        elif line.startswith("from "):
            imports.append(line.strip())

    return {
        "file": relative_path,
        "line_count": len(
            content.splitlines()
        ),
        "contains_handler":
            "lambda_handler" in content,
        "imports": imports
    }
