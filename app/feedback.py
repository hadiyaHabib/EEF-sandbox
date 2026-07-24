def generate_feedback(structure_checks: dict, test_results: dict, secrets_found: list) -> dict:
    strengths = []
    weaknesses = []

    for check, passed in structure_checks.items():
        if passed:
            strengths.append(f"{check} is properly implemented.")
        else:
            weaknesses.append(f"{check} is missing or incomplete.")

    for test_name, passed in test_results.items():
        if not passed:
            weaknesses.append(f"{test_name.upper()} coverage is missing — add tests for this area.")

    if secrets_found:
        weaknesses.append(f"Potential hardcoded secrets found in: {', '.join(secrets_found[:3])}. Move these to environment variables.")
    else:
        strengths.append("No hardcoded secrets detected in scanned files.")

    if not strengths:
        strengths.append("Repository was evaluated successfully with baseline structure detected.")
    if not weaknesses:
        weaknesses.append("No major issues detected in this evaluation pass.")

    return {"strengths": strengths[:6], "weaknesses": weaknesses[:6]}