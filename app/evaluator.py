import os
import ast

def analyze_code_file(file_path):
    metrics = {"has_try_except": False, "secure_methods": True, "functions_count": 0}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            node = ast.parse(f.read())
        for child in ast.walk(node):
            if isinstance(child, ast.Try): metrics["has_try_except"] = True
            if isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                if child.func.id in ["eval", "exec"]: metrics["secure_methods"] = False
            if isinstance(child, ast.FunctionDef): metrics["functions_count"] += 1
    except Exception: pass
    return metrics

def evaluate_project(folder_path: str):
    if not folder_path or not os.path.exists(folder_path):
        return {"code_quality": 0, "architecture": 0, "feature_score": 0, "feedback": "Repository path invalid."}

    code_quality = 30
    architecture = 40
    feature_score = 40
    strengths = []
    weaknesses = []

    has_app = os.path.exists(os.path.join(folder_path, "app")) or os.path.exists(os.path.join(folder_path, "src"))
    has_tests = os.path.exists(os.path.join(folder_path, "tests"))
    has_requirements = os.path.exists(os.path.join(folder_path, "requirements.txt"))
    has_readme = os.path.exists(os.path.join(folder_path, "README.md"))

    if has_app: 
        architecture += 30
        strengths.append("Standard project folder structure (app/src) found.")
    else:
        weaknesses.append("Missing standard source directory (app/src).")

    if has_tests: 
        architecture += 30
        strengths.append("Automated tests directory found.")
    else:
        weaknesses.append("No automated test suite discovered.")

    if has_requirements: 
        code_quality += 30
        strengths.append("Dependency list (requirements.txt) is provided.")
    else:
        weaknesses.append("Missing requirements.txt file.")

    if has_readme: 
        code_quality += 20
        strengths.append("Documentation (README.md) is present.")
    else:
        weaknesses.append("Project lacks documentation or README.")

    total_functions = 0
    secure_code = True
    error_handling_found = False

    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".py") and "venv" not in root:
                file_metrics = analyze_code_file(os.path.join(root, file))
                total_functions += file_metrics["functions_count"]
                if file_metrics["has_try_except"]: error_handling_found = True
                if not file_metrics["secure_methods"]: secure_code = False

    if error_handling_found:
        code_quality += 20
        strengths.append("Robust implementation with proper try-except error blocks.")
    else:
        weaknesses.append("Poor exception handling; risks crashing on unexpected input.")

    if secure_code and total_functions > 0:
        code_quality = min(code_quality + 10, 100)
    elif not secure_code:
        weaknesses.append("Security risk: Dangerous functions like eval() or exec() detected.")

    if total_functions >= 3: feature_score += 60
    elif total_functions > 0: feature_score += 30
    else: feature_score += 10

    # Formatting text feedback
    feedback_str = "STRENGTHS:\n" + ("\n".join([f"- {s}" for s in strengths]) if strengths else "- None")
    feedback_str += "\n\nWEAKNESSES / SUGGESTIONS:\n" + ("\n".join([f"- {w}" for w in weaknesses]) if weaknesses else "- Project matches production-ready code criteria.")

    return {
        "code_quality": min(code_quality, 100),
        "architecture": min(architecture, 100),
        "feature_score": min(feature_score, 100),
        "feedback": feedback_str
    }