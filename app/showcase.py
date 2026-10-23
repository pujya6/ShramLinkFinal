"""Public, read-only architecture examples. Never query profiles or call providers."""

from itertools import product
from types import SimpleNamespace

from app.recruitment import matching

REPOSITORY = "https://github.com/Je37-arch/ShramLink"
BRANCH = "feature/shramlink-v3-release"
BASE_SHA = "0bea8e29aca12a2f48c08b9c748f6b7b6f127f33"
# Updated only after executing the documented suite. Counts are evidence, not telemetry.
RELEASE_EVIDENCE = dict(date="2026-10-23", status="passed", python=204, javascript=41)


def synthetic_matches():
    job = SimpleNamespace(
        skill=SimpleNamespace(value="welder"),
        location="Delhi",
        domain="manufacturing",
        required_experience_months=24,
    )
    examples = {}
    for skill, city, months in product(
        ["welder", "helper"], ["Delhi", "Noida"], [18, 32]
    ):
        worker = SimpleNamespace(
            get_skills_list=lambda: [skill],
            location=city,
            preferred_domain="manufacturing",
            total_experience_months=months,
            profile_complete=True,
        )
        examples[f"{skill}:{city}:{months}"] = matching(job, worker)
    return examples
