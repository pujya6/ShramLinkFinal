"""Validated server switches. Optional services fail to the local demonstrator."""

import os
import re


def defaults():
    return {
        name: os.getenv(name, default)
        for name, default in {
            "VOICE_PROVIDER": "deterministic",
            "JOB_SOURCE": "demo",
            "SHRAMLINK_DEMO": "true",
            "XAI_API_KEY": "",
            "XAI_MODEL": "",
            "XAI_DAILY_REQUEST_LIMIT": "60",
            "XAI_USER_DAILY_LIMIT": "30",
            "XAI_INPUT_USD_PER_MILLION": "0",
            "XAI_OUTPUT_USD_PER_MILLION": "0",
            "GREENHOUSE_BOARD": "",
            "GREENHOUSE_EMPLOYER": "",
            "GREENHOUSE_FORMAL_ATTESTED": "false",
        }.items()
    }


def configure(app):
    c = app.config
    for name, choices in [
        ("VOICE_PROVIDER", ("deterministic", "api")),
        ("JOB_SOURCE", ("demo", "integrated")),
    ]:
        if c[name] not in choices:
            raise RuntimeError(f"{name} must be one of {', '.join(choices)}.")
    for name in ["SHRAMLINK_DEMO", "GREENHOUSE_FORMAL_ATTESTED"]:
        value = c[name]
        if str(value).lower() not in ("true", "false"):
            raise RuntimeError(f"{name} must be true or false.")
        c[name] = str(value).lower() == "true"
    for name in ["XAI_DAILY_REQUEST_LIMIT", "XAI_USER_DAILY_LIMIT"]:
        try:
            value = int(c[name])
        except (ValueError, TypeError):
            raise RuntimeError(f"{name} must be a whole number.") from None
        if not 0 <= value <= 240:
            raise RuntimeError(f"{name} must be 0–240 (0 disables API requests).")
        c[name] = value
    for name in ["XAI_INPUT_USD_PER_MILLION", "XAI_OUTPUT_USD_PER_MILLION"]:
        try:
            value = float(c[name])
        except (ValueError, TypeError):
            raise RuntimeError(f"{name} must be a nonnegative price.") from None
        if not 0 <= value <= 1000:
            raise RuntimeError(f"{name} must be 0–1000.")
        c[name] = value
    if c["GREENHOUSE_BOARD"] and not re.fullmatch(
        r"[a-zA-Z0-9_-]{1,80}", c["GREENHOUSE_BOARD"]
    ):
        raise RuntimeError("GREENHOUSE_BOARD must be a board token, not a URL.")
    if len(c["GREENHOUSE_EMPLOYER"]) > 160:
        raise RuntimeError("GREENHOUSE_EMPLOYER is too long.")
    if c["XAI_MODEL"] not in ("", "grok-4.3"):
        raise RuntimeError(
            "XAI_MODEL must be grok-4.3, the documented bounded non-reasoning configuration."
        )
    c["EFFECTIVE_VOICE_PROVIDER"] = (
        "api"
        if c["VOICE_PROVIDER"] == "api"
        and c["XAI_API_KEY"]
        and c["XAI_MODEL"]
        and c["XAI_DAILY_REQUEST_LIMIT"]
        and c["XAI_USER_DAILY_LIMIT"]
        else "deterministic"
    )
    c["EFFECTIVE_JOB_SOURCE"] = (
        "integrated"
        if c["JOB_SOURCE"] == "integrated"
        and c["GREENHOUSE_BOARD"]
        and c["GREENHOUSE_EMPLOYER"]
        and c["GREENHOUSE_FORMAL_ATTESTED"]
        else "demo"
    )
    modes = {
        ("api", "demo"): "V3a",
        ("deterministic", "demo"): "V3b",
        ("deterministic", "integrated"): "V3c",
        ("api", "integrated"): "V3d",
    }
    c["CONFIGURATION_LABEL"] = modes[
        c["EFFECTIVE_VOICE_PROVIDER"], c["EFFECTIVE_JOB_SOURCE"]
    ]
    c["REQUESTED_CONFIGURATION_LABEL"] = modes[c["VOICE_PROVIDER"], c["JOB_SOURCE"]]
