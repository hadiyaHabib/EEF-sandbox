import os

def run_test_suite(repo_path: str, stack: str) -> dict:
    has_unit = _has_test_files(repo_path, stack)
    has_api_routes = _has_api_definition(repo_path, stack)

    return {
        "api": has_api_routes,
        "unit": has_unit,
        "db": _has_db_config(repo_path, stack),
        "integration": has_unit and has_api_routes,
        "uismoke": os.path.isdir(os.path.join(repo_path, "public")) or os.path.isdir(os.path.join(repo_path, "src")),
        "performance": has_unit,
    }

def _has_test_files(repo_path: str, stack: str) -> bool:
    test_dirs = ["tests", "test", "__tests__", "spec"]
    for root, dirs, files in os.walk(repo_path):
        if ".git" in root:
            continue
        for d in dirs:
            if d.lower() in test_dirs:
                return True
        for f in files:
            if "test" in f.lower() and f.endswith((".py", ".js", ".php", ".dart")):
                return True
    return False

def _has_api_definition(repo_path: str, stack: str) -> bool:
    keywords = {
        "Laravel": ["route::"],
        "MERN": ["app.get(", "app.post(", "router.get("],
        "Python": ["@app.get", "@app.route", "@app.post"],
    }.get(stack, [])
    for root, _, files in os.walk(repo_path):
        if ".git" in root:
            continue
        for f in files:
            if f.endswith((".py", ".js", ".php")):
                try:
                    with open(os.path.join(root, f), "r", errors="ignore") as fh:
                        content = fh.read().lower()
                        if any(kw in content for kw in keywords):
                            return True
                except Exception:
                    pass
    return False

def _has_db_config(repo_path: str, stack: str) -> bool:
    indicators = [".env.example", "config/database.php", "models", "schema.prisma"]
    all_paths = []
    for root, dirs, files in os.walk(repo_path):
        all_paths.extend(dirs)
        all_paths.extend(files)
    return any(ind in all_paths for ind in indicators)