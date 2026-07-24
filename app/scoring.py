def calculate_scores(structure_checks: dict, test_results: dict, secrets_found: list, build_success: bool, build_time_seconds: float) -> dict:

    structure_pass_count = sum(1 for v in structure_checks.values() if v)
    structure_total = len(structure_checks) if structure_checks else 1
    structure_ratio = structure_pass_count / structure_total

    test_pass_count = sum(1 for v in test_results.values() if v)
    test_total = len(test_results) if test_results else 1
    test_ratio = test_pass_count / test_total

    feature_completion = round(structure_ratio * 100, 1)
    code_quality = round((structure_ratio * 0.6 + test_ratio * 0.4) * 100, 1)
    architecture = round(structure_ratio * 100, 1)

    security_penalty = min(len(secrets_found) * 15, 60)
    security = round(max(100 - security_penalty, 20), 1)

    api_quality = round((100 if test_results.get("api") else 40), 1)
    deployment_readiness = round((100 if build_success else 30), 1)

    engineering_maturity = round((feature_completion + code_quality + architecture + security) / 4, 1)

    documentation = round(100 if structure_checks.get("Required Features") else 40, 1)
    performance = round(100 if test_results.get("performance") else 50, 1)

    overall = round((
        feature_completion + code_quality + architecture + security +
        api_quality + deployment_readiness + engineering_maturity
    ) / 7, 1)

    grade = "A" if overall >= 90 else "B" if overall >= 75 else "C"

    return {
        "feature_completion": feature_completion,
        "code_quality": code_quality,
        "architecture": architecture,
        "security": security,
        "api_quality": api_quality,
        "deployment_readiness": deployment_readiness,
        "engineering_maturity": engineering_maturity,
        "documentation": documentation,
        "performance": performance,
        "overall_score": overall,
        "grade": grade,
    }