import hashlib
import os

def compute_source_hash(repo_path: str) -> str:
    hasher = hashlib.sha256()
    for root, _, files in sorted(os.walk(repo_path)):
        if ".git" in root:
            continue
        for fname in sorted(files):
            if fname.endswith((".py", ".js", ".php", ".dart")):
                try:
                    with open(os.path.join(root, fname), "rb") as f:
                        hasher.update(f.read())
                except Exception:
                    pass
    return hasher.hexdigest()

def check_similarity(new_hash: str, existing_hashes: list) -> float:
    if new_hash in existing_hashes:
        return 100.0
    return 0.0