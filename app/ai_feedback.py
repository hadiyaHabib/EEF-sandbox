import os
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

load_dotenv()

_api_key = os.getenv("GEMINI_API_KEY")
_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"


def generate_ai_feedback(repo_name: str, stack: str, structure_checks: dict,
                          test_results: dict, scores: dict) -> dict:
    """
    Calls Google Gemini directly over REST (via urllib, not the google SDK,
    to avoid a real dependency conflict between google-generativeai's
    requests>=2.33 requirement and the Docker SDK's requests<2.32
    requirement in the same environment).

    Falls back silently if no key is configured or the call fails, so the
    platform's core pipeline never breaks because of this optional feature.
    """
    if not _api_key:
        return {"available": False, "reason": "No GEMINI_API_KEY configured."}

    passed_checks = [k for k, v in structure_checks.items() if v]
    failed_checks = [k for k, v in structure_checks.items() if not v]
    passed_tests = [k for k, v in test_results.items() if v]
    failed_tests = [k for k, v in test_results.items() if not v]

    prompt = f"""You are a senior software engineering mentor reviewing an intern's code submission for an internal evaluation platform.

Repository: {repo_name}
Detected technology stack: {stack}

Structural checks that PASSED: {', '.join(passed_checks) or 'none'}
Structural checks that FAILED: {', '.join(failed_checks) or 'none'}
Test categories detected: {', '.join(passed_tests) or 'none'}
Test categories missing: {', '.join(failed_tests) or 'none'}

Engineering scores (0-100): {json.dumps(scores)}

Write a short, specific engineering review as a mentor would. Respond ONLY with valid JSON in this exact shape, no markdown, no code fences:
{{
  "strengths": ["short specific sentence", "short specific sentence"],
  "weaknesses": ["short specific sentence", "short specific sentence"],
  "roadmap": "one sentence describing the single most valuable next improvement"
}}

Keep each item under 20 words. Base every statement strictly on the data given above — do not invent details about the code you cannot see."""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    url = f"{_GEMINI_URL}?key={_api_key}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            result = json.loads(response.read().decode())

        raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()

        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]

        parsed = json.loads(raw_text.strip())

        return {
            "available": True,
            "strengths": parsed.get("strengths", []),
            "weaknesses": parsed.get("weaknesses", []),
            "roadmap": parsed.get("roadmap", ""),
        }

    except urllib.error.HTTPError as e:
        return {"available": False, "reason": f"Gemini API error ({e.code}): {e.read().decode(errors='ignore')}"}
    except Exception as e:
        return {"available": False, "reason": f"Gemini call failed: {e}"}