import os
import re

def check_project_structure(repo_path: str, stack: str) -> dict:
    files = set(os.listdir(repo_path))
    checks = {}

    checks["Project Structure"] = len(files) > 2
    checks["Folder Organization"] = any(
        os.path.isdir(os.path.join(repo_path, f)) for f in files
    )
    checks["Required Features"] = "README.md" in files or "readme.md" in [f.lower() for f in files]

    if stack == "Laravel":
        checks["API Availability"] = os.path.isdir(os.path.join(repo_path, "routes"))
        checks["Database Connectivity"] = os.path.isdir(os.path.join(repo_path, "database"))
        checks["Authentication Flow"] = os.path.isdir(os.path.join(repo_path, "app", "Http", "Controllers"))
    elif stack == "MERN":
        checks["API Availability"] = "package.json" in files
        checks["Database Connectivity"] = os.path.exists(os.path.join(repo_path, "models")) or "mongoose" in _read_package_json(repo_path)
        checks["Authentication Flow"] = _search_text_in_repo(repo_path, ["jwt", "passport", "auth"])
    elif stack == "Python":
        checks["API Availability"] = _search_text_in_repo(repo_path, ["fastapi", "flask", "django"])
        checks["Database Connectivity"] = _search_text_in_repo(repo_path, ["sqlalchemy", "psycopg2", "pymongo"])
        checks["Authentication Flow"] = _search_text_in_repo(repo_path, ["jwt", "oauth", "login"])
    else:
        checks["API Availability"] = False
        checks["Database Connectivity"] = False
        checks["Authentication Flow"] = False

    checks["Error Handling"] = _search_text_in_repo(repo_path, ["try:", "except", "try {", "catch"])
    checks["Security Configuration"] = ".env.example" in files or ".gitignore" in files

    return checks

def _read_package_json(repo_path: str) -> str:
    path = os.path.join(repo_path, "package.json")
    if os.path.exists(path):
        with open(path, "r", errors="ignore") as f:
            return f.read().lower()
    return ""

def _search_text_in_repo(repo_path: str, keywords: list, max_files: int = 200) -> bool:
    count = 0
    for root, _, files in os.walk(repo_path):
        if ".git" in root:
            continue
        for fname in files:
            if count > max_files:
                return False
            if fname.endswith((".py", ".js", ".ts", ".php", ".dart", ".json")):
                try:
                    with open(os.path.join(root, fname), "r", errors="ignore") as f:
                        content = f.read().lower()
                        if any(kw in content for kw in keywords):
                            return True
                except Exception:
                    pass
                count += 1
    return False

def scan_for_exposed_secrets(repo_path: str) -> list:
    patterns = [
        r'(api[_-]?key)\s*=\s*["\'][A-Za-z0-9]{16,}["\']',
        r'(secret|password|passwd)\s*=\s*["\'][^"\']{6,}["\']',
        r'AKIA[0-9A-Z]{16}',
    ]
    findings = []
    for root, _, files in os.walk(repo_path):
        if ".git" in root:
            continue
        for fname in files:
            if fname.endswith((".py", ".js", ".env", ".php", ".json")):
                try:
                    with open(os.path.join(root, fname), "r", errors="ignore") as f:
                        content = f.read()
                        for pattern in patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                findings.append(fname)
                                break
                except Exception:
                    pass
    return findings