"""Tiny app for exercise 1: uses both dependencies (and contains one deliberate Bandit finding)."""

from __future__ import annotations

import subprocess

import jinja2
import requests


def render_greeting(name: str) -> str:
    env = jinja2.Environment(autoescape=True)
    return env.from_string("Hello, {{ name }}!").render(name=name)


def user_agent() -> str:
    return requests.utils.default_user_agent()


def run_shell(cmd: str) -> str:
    # Deliberately bad (for the Bandit contrast): shell=True with an arbitrary string -> B602.
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False).stdout


if __name__ == "__main__":
    print(render_greeting("SPbU"), "|", user_agent())
