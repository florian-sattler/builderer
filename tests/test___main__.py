import os
import pathlib
import re
import signal
import subprocess
import sys
import time
import typing
from unittest.mock import call

import pytest
from pytest_mock import MockerFixture

import builderer
import builderer.__main__

# Real Ctrl-C handling relies on POSIX signals / process groups.
requires_posix = pytest.mark.skipif(os.name != "posix", reason="SIGINT process-group signalling requires POSIX")

_REPO_ROOT = pathlib.Path(builderer.__file__).resolve().parent.parent


def _run_until_interrupt(config: pathlib.Path) -> tuple[int, str]:
    """Run `python -m builderer`, wait until the first action starts, then send a Ctrl-C.

    The process is started in its own session so a SIGINT to its process group mimics what a
    terminal does on Ctrl-C (the running child command is interrupted too).

    Returns:
        tuple[int, str]: the exit code and the combined stdout/stderr output.
    """
    proc = subprocess.Popen(
        [sys.executable, "-m", "builderer", "--config", str(config)],
        cwd=_REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    assert proc.stdout is not None

    first_line = proc.stdout.readline()  # blocks until the first action prints (or EOF on early exit)
    time.sleep(1)  # let the action's child command spawn into the group before interrupting
    os.killpg(proc.pid, signal.SIGINT)

    try:
        rest = proc.communicate(timeout=10)[0]
    except subprocess.TimeoutExpired:  # pragma: no cover - only hit if the abort handling regresses
        proc.kill()
        proc.communicate()
        raise AssertionError("builderer did not exit promptly after SIGINT")

    assert proc.returncode is not None
    return proc.returncode, first_line + rest


@requires_posix
def test_sigint_aborts_gracefully(tmp_path: pathlib.Path) -> None:
    # A Ctrl-C while a (main-thread) action runs exits cleanly: code 130, message, no traceback.
    config = tmp_path / ".builderer.yml"
    config.write_text(
        'steps:\n  - type: action\n    name: long task\n    commands: [["sleep", "30"]]\n    post: false\n'
    )

    code, output = _run_until_interrupt(config)

    assert code == 130
    assert "Aborted!" in output
    assert "Traceback" not in output


@requires_posix
def test_sigint_cancels_pending_group_actions(tmp_path: pathlib.Path) -> None:
    # num_parallel=1 keeps the second action queued while the first runs. A Ctrl-C must cancel
    # the queued action rather than letting it run while the executor shuts down.
    config = tmp_path / ".builderer.yml"
    config.write_text(
        "steps:\n"
        "  - type: group\n"
        "    num_parallel: 1\n"
        "    steps:\n"
        '      - {type: action, name: started, commands: [["sleep", "30"]], post: false}\n'
        '      - {type: action, name: cancelled, commands: [["sleep", "30"]], post: false}\n'
    )

    code, output = _run_until_interrupt(config)

    assert code == 130
    assert "Aborted!" in output
    assert "started" in output  # the running action did start
    assert "cancelled" not in output  # the queued action was cancelled, never run
    assert "Traceback" not in output


@pytest.mark.parametrize(
    ("input_args", "expected_config", "expected_args"),
    [
        (
            [],
            ".builderer.yml",
            {},
        ),
        (
            [
                "--registry",
                "reg.example.com:6789",
                "--prefix",
                "user",
                "--tags",
                "foo",
                "bar",
                "baz",
                "--no-push",
                "--cache",
                "--verbose",
                "--simulate",
                "--backend",
                "podman",
                "--config",
                "test.yaml",
            ],
            "test.yaml",
            {
                "registry": "reg.example.com:6789",
                "prefix": "user",
                "tags": ["foo", "bar", "baz"],
                "push": False,
                "cache": True,
                "verbose": True,
                "simulate": True,
                "backend": "podman",
            },
        ),
    ],
)
def test_parse_args(input_args: list[str], expected_config: str, expected_args: dict[str, typing.Any]) -> None:
    actual_config, actual_args = builderer.__main__.parse_args(input_args)
    assert actual_config == expected_config
    assert actual_args == expected_args


@pytest.mark.parametrize(("value", "expected"), [("cores", "cores"), ("8", 8)])
def test_parse_args_max_parallel(value: str, expected: typing.Any) -> None:
    _, args = builderer.__main__.parse_args(["--max-parallel", value])
    assert args["max_parallel"] == expected


@pytest.mark.parametrize("value", ["0", "-1", "all", "bogus"])
def test_parse_args_max_parallel_invalid(value: str) -> None:
    with pytest.raises(SystemExit):
        builderer.__main__.parse_args(["--max-parallel", value])


@pytest.mark.parametrize(
    ("flag", "pattern"),
    [
        ("--help", "^usage: builderer.*options"),
        ("-h", "^usage: builderer.*options"),
        ("--version", r"^builderer \d+\.\d+\.\d+$"),
    ],
)
def test_parse_args_special_action(flag: str, pattern: str, capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit, match="^0$"):
        builderer.__main__.parse_args([flag])

    captured = capsys.readouterr()

    assert captured.err == ""
    assert re.match(pattern, captured.out, re.DOTALL) is not None


@pytest.mark.parametrize("verbose", [True, False])
def test_main_simulate_example_workspace(
    datadir: pathlib.Path, capsys: pytest.CaptureFixture[str], verbose: bool
) -> None:
    run_config = datadir / "example_workspace" / ".builderer.yml"
    arguments = ["--config", str(run_config), "--simulate"] + (["--verbose"] if verbose else [])

    return_code = builderer.__main__.main(arguments)
    captured = capsys.readouterr()

    assert return_code == 0
    assert captured.err == ""

    if verbose:
        assert captured.out.split("\n") == [
            "Pulling image: docker.io/python:alpine",
            "['docker', 'pull', 'docker.io/python:alpine']",
            "Pulling image: docker.io/nginx:alpine",
            "['docker', 'pull', 'docker.io/nginx:alpine']",
            "Forwarding image: docker.io/redis:alpine -> redis",
            "['docker', 'pull', 'docker.io/redis:alpine']",
            "['docker', 'tag', 'docker.io/redis:alpine', 'registry.example.com/foo/redis:latest']",
            "Building image: frontend",
            "['docker', 'build', '-t', 'registry.example.com/foo/frontend:latest', '--no-cache', '-f', 'frontend/Dockerfile', 'frontend']",
            "Building image: backend",
            "['docker', 'build', '-t', 'registry.example.com/foo/backend:latest', '--no-cache', '-f', 'backend/Dockerfile', 'backend']",
            "Pushing image: backend",
            "['docker', 'push', 'registry.example.com/foo/backend:latest']",
            "Pushing image: frontend",
            "['docker', 'push', 'registry.example.com/foo/frontend:latest']",
            "Pushing image: redis",
            "['docker', 'push', 'registry.example.com/foo/redis:latest']",
            "",
        ]

    else:
        assert captured.out.split("\n") == [
            "Pulling image: docker.io/python:alpine",
            "Pulling image: docker.io/nginx:alpine",
            "Forwarding image: docker.io/redis:alpine -> redis",
            "Building image: frontend",
            "Building image: backend",
            "Pushing image: backend",
            "Pushing image: frontend",
            "Pushing image: redis",
            "",
        ]


def test_main_run_example_workspace(
    datadir: pathlib.Path, capsys: pytest.CaptureFixture[str], mocker: MockerFixture
) -> None:
    run_patch = mocker.patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0))

    arguments = ["--config", str(datadir / "example_workspace" / ".builderer.yml"), "--verbose"]
    return_code = builderer.__main__.main(arguments)
    captured = capsys.readouterr()

    assert return_code == 0
    assert captured.err == ""

    assert captured.out.split("\n") == [
        "Pulling image: docker.io/python:alpine",
        "['docker', 'pull', 'docker.io/python:alpine']",
        "Pulling image: docker.io/nginx:alpine",
        "['docker', 'pull', 'docker.io/nginx:alpine']",
        "Forwarding image: docker.io/redis:alpine -> redis",
        "['docker', 'pull', 'docker.io/redis:alpine']",
        "['docker', 'tag', 'docker.io/redis:alpine', 'registry.example.com/foo/redis:latest']",
        "Building image: frontend",
        "['docker', 'build', '-t', 'registry.example.com/foo/frontend:latest', '--no-cache', '-f', 'frontend/Dockerfile', 'frontend']",
        "Building image: backend",
        "['docker', 'build', '-t', 'registry.example.com/foo/backend:latest', '--no-cache', '-f', 'backend/Dockerfile', 'backend']",
        "Pushing image: backend",
        "['docker', 'push', 'registry.example.com/foo/backend:latest']",
        "Pushing image: frontend",
        "['docker', 'push', 'registry.example.com/foo/frontend:latest']",
        "Pushing image: redis",
        "['docker', 'push', 'registry.example.com/foo/redis:latest']",
        "",
    ]

    expected_calls = [
        call(["docker", "pull", "docker.io/python:alpine"]),
        call(["docker", "pull", "docker.io/nginx:alpine"]),
        call(["docker", "pull", "docker.io/redis:alpine"]),
        call(["docker", "tag", "docker.io/redis:alpine", "registry.example.com/foo/redis:latest"]),
        call(
            [
                "docker",
                "build",
                "-t",
                "registry.example.com/foo/frontend:latest",
                "--no-cache",
                "-f",
                "frontend/Dockerfile",
                "frontend",
            ]
        ),
        call(
            [
                "docker",
                "build",
                "-t",
                "registry.example.com/foo/backend:latest",
                "--no-cache",
                "-f",
                "backend/Dockerfile",
                "backend",
            ]
        ),
        call(["docker", "push", "registry.example.com/foo/backend:latest"]),
        call(["docker", "push", "registry.example.com/foo/frontend:latest"]),
        call(["docker", "push", "registry.example.com/foo/redis:latest"]),
    ]

    assert run_patch.call_count == len(expected_calls)
    run_patch.assert_has_calls(expected_calls, any_order=False)


def test_main_run_unknown_workspace(tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    arguments = ["--config", str(tmp_path / ".builderer.yml")]

    return_code = builderer.__main__.main(arguments)
    captured = capsys.readouterr()

    assert return_code == 1
    assert captured.err == ""
    assert "No such file or directory:" in captured.out


def test_main_invalid_config(tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    # A config that loads but fails validation must be handled like a missing
    # file: print the error and return 1 (the pydantic.ValidationError branch).
    config = tmp_path / ".builderer.yml"
    config.write_text("steps:\n  - type: nonsense\n")

    return_code = builderer.__main__.main(["--config", str(config)])
    captured = capsys.readouterr()

    assert return_code == 1
    assert captured.err == ""
    assert "Unknown step type nonsense" in captured.out


def test_main_keyboard_interrupt(
    datadir: pathlib.Path, capsys: pytest.CaptureFixture[str], mocker: MockerFixture
) -> None:
    # A Ctrl-C during execution must be handled gracefully: clean message, exit 130, no traceback.
    mocker.patch("builderer.__main__.Builderer.run", side_effect=KeyboardInterrupt)
    config = datadir / "example_workspace" / ".builderer.yml"

    return_code = builderer.__main__.main(["--config", str(config), "--simulate"])
    captured = capsys.readouterr()

    assert return_code == 130
    assert captured.err == ""
    assert "Aborted!" in captured.out


def test_main_cli_overrides_file_parameters(
    tmp_path: pathlib.Path, capsys: pytest.CaptureFixture[str], mocker: MockerFixture
) -> None:
    # The file sets registry/prefix/backend/tags; the CLI overrides a subset.
    # CLI must win over the file, the file must win over defaults, and file-only
    # parameters (prefix, tags) must still reach the factory.
    config = tmp_path / ".builderer.yml"
    config.write_text(
        "parameters:\n"
        "  registry: file-reg.example.com\n"
        "  prefix: fileprefix\n"
        "  backend: docker\n"
        "  tags:\n"
        "    - filetag\n"
        "steps:\n"
        "  - type: build_image\n"
        "    directory: svc\n"
    )

    run_patch = mocker.patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0))

    arguments = ["--config", str(config), "--verbose", "--registry", "cli-reg.example.com", "--backend", "podman"]
    return_code = builderer.__main__.main(arguments)
    captured = capsys.readouterr()

    assert return_code == 0
    assert captured.err == ""

    image = "cli-reg.example.com/fileprefix/svc:filetag"  # cli registry + file prefix/tag
    expected_calls = [
        call(["podman", "build", "-t", image, "--no-cache", "-f", "svc/Dockerfile", "svc"]),  # cli backend
        call(["podman", "push", image]),
    ]

    assert run_patch.call_count == len(expected_calls)
    run_patch.assert_has_calls(expected_calls, any_order=False)
