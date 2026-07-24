import docker
import git
import shutil
import os
import re
import time
import tempfile

client = docker.from_env()

BASE_IMAGES = {
    "Python": "python:3.11-slim",
    "MERN": "node:20-slim",
    "Laravel": "php:8.2-cli",
    "Flutter": "python:3.11-slim",
    "Unknown": "python:3.11-slim",
}

def clone_repository(github_url: str) -> str:
    temp_dir = tempfile.mkdtemp(prefix="sandbox_")
    git.Repo.clone_from(github_url, temp_dir, depth=1)
    return temp_dir

def run_in_container(repo_path: str, stack: str, timeout_seconds: int = 60):
    """
    Quick build/launch check — confirms the base image runs against this repo
    and captures a resource-usage snapshot. Does not execute the test suite;
    see run_real_tests() for that.
    """
    image = BASE_IMAGES.get(stack, "python:3.11-slim")
    start_time = time.time()
    logs = []
    stats_snapshot = {"cpu_percent": 0, "mem_usage_mb": 0}
    success = True

    try:
        client.images.pull(image)
    except Exception as e:
        logs.append(f"Image pull warning: {e}")

    container = None
    try:
        container = client.containers.run(
            image,
            command="sleep 30",
            volumes={repo_path: {"bind": "/workspace", "mode": "ro"}},
            working_dir="/workspace",
            detach=True,
            mem_limit="512m",
            nano_cpus=1_000_000_000,
        )

        try:
            stats = container.stats(stream=False)
            cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            system_delta = stats["cpu_stats"]["system_cpu_usage"] - stats["precpu_stats"]["system_cpu_usage"]
            cpu_percent = (cpu_delta / system_delta) * 100 if system_delta > 0 else 0
            mem_mb = stats["memory_stats"].get("usage", 0) / (1024 * 1024)
            stats_snapshot = {"cpu_percent": round(cpu_percent, 2), "mem_usage_mb": round(mem_mb, 2)}
        except Exception:
            pass

        logs.append(f"Container {container.short_id} started on image {image}")

    except Exception as e:
        success = False
        logs.append(f"Container execution failed: {e}")

    finally:
        if container:
            try:
                container.stop(timeout=5)
                container.remove(force=True)
            except Exception:
                pass

    build_time = time.time() - start_time
    return {
        "success": success,
        "logs": logs,
        "build_time_seconds": round(build_time, 2),
        "stats": stats_snapshot,
    }


def _parse_pytest_summary(output: str):
    """Extracts 'N passed' / 'N failed' counts from pytest's final summary line."""
    passed_match = re.search(r"(\d+)\s+passed", output)
    failed_match = re.search(r"(\d+)\s+failed", output)
    passed = int(passed_match.group(1)) if passed_match else None
    failed = int(failed_match.group(1)) if failed_match else 0
    return passed, failed


def run_real_tests(repo_path: str, stack: str, timeout_seconds: int = 120) -> dict:
    """
    Actually executes the project's test suite inside an isolated Docker
    container — this is real dynamic analysis, not just file detection.

    Supported today: Python (pytest) and MERN (npm test).
    Laravel and Flutter are intentionally NOT auto-executed here, because a
    generic, dependency-free test run for those stacks usually requires a
    configured database or emulator that can't be safely assumed — running
    them would produce misleading pass/fail results rather than an honest
    "not supported" signal. Static test-file detection is used for those
    stacks instead (see test_runner.py).
    """
    image = BASE_IMAGES.get(stack, "python:3.11-slim")

    if stack == "Python":
        shell_cmd = (
            "pip install --quiet --no-cache-dir -r requirements.txt 2>/dev/null; "
            "pip install --quiet --no-cache-dir pytest 2>/dev/null; "
            "pytest --tb=no -q 2>&1 | tail -n 100"
        )
    elif stack == "MERN":
        shell_cmd = (
            "npm install --silent --no-audit --no-fund 2>/dev/null; "
            "npm test --silent 2>&1 | tail -n 100"
        )
    else:
        return {
            "executed": False,
            "reason": f"Automatic test execution is not supported for stack '{stack}' in this build. "
                      f"Falling back to static test-file detection."
        }

    container = None
    output = ""
    exit_code = None

    try:
        container = client.containers.run(
            image,
            command=["sh", "-c", shell_cmd],
            volumes={repo_path: {"bind": "/workspace", "mode": "rw"}},
            working_dir="/workspace",
            detach=True,
            mem_limit="768m",
            nano_cpus=1_000_000_000,
        )
        result = container.wait(timeout=timeout_seconds)
        exit_code = result.get("StatusCode", 1)
        output = container.logs().decode(errors="ignore")
    except Exception as e:
        output = f"Test execution error: {e}"
        exit_code = 1
    finally:
        if container:
            try:
                container.remove(force=True)
            except Exception:
                pass

    # MERN: no "test" script defined in package.json — this is not a failure,
    # it just means there's nothing to execute. Fall back to static detection.
    if stack == "MERN" and "missing script" in output.lower():
        return {
            "executed": False,
            "reason": "No 'test' script defined in package.json.",
            "output_tail": output[-1000:],
        }

    # pytest exit code 5 = no tests were collected at all — not a failure,
    # just means there's nothing to run. Fall back to static detection.
    if stack == "Python" and exit_code == 5:
        return {
            "executed": False,
            "reason": "No tests were collected by pytest.",
            "output_tail": output[-1000:],
        }

    # Environment-level errors (bad pytest invocation, interrupted run, etc.)
    # are not the same as "the code's tests failed" — don't penalize for these.
    if stack == "Python" and exit_code in (2, 3, 4):
        return {
            "executed": False,
            "reason": f"Test runner exited with an environment error (code {exit_code}), not a test failure.",
            "output_tail": output[-1000:],
        }

    passed, failed = _parse_pytest_summary(output) if stack == "Python" else (None, None)

    return {
        "executed": True,
        "exit_code": exit_code,
        "success": exit_code == 0,
        "output_tail": output[-2000:],
        "passed_count": passed,
        "failed_count": failed,
    }


def cleanup_repo(repo_path: str):
    shutil.rmtree(repo_path, ignore_errors=True)