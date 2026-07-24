import os

def detect_stack(repo_path: str) -> str:
    files = os.listdir(repo_path)

    if "composer.json" in files or "artisan" in files:
        return "Laravel"
    if "pubspec.yaml" in files:
        return "Flutter"
    if "package.json" in files:
        return "MERN"
    if "requirements.txt" in files or "pyproject.toml" in files or "manage.py" in files:
        return "Python"

    return "Unknown"