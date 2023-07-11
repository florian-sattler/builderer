import pathlib
import sys

import pytest

from builderer.actions import Action, ActionGroup
from builderer.builderer import Builderer


@pytest.fixture
def empty_builderer() -> Builderer:
    return Builderer()


def test_empty_builderer(empty_builderer: Builderer) -> None:
    assert empty_builderer.simulate is False
    assert empty_builderer.verbose is False
    assert empty_builderer.max_parallel is None


@pytest.fixture
def sim_builderer(empty_builderer: Builderer) -> Builderer:
    empty_builderer.simulate = True
    empty_builderer.verbose = True
    return empty_builderer


@pytest.mark.parametrize("value", [-10, -2, -1, 0])
def test_max_parallel_negative(value: int) -> None:
    with pytest.raises(ValueError) as e:
        Builderer(max_parallel=value)

    assert "max_parallel" in str(e)


@pytest.mark.parametrize("name", ["some_name", "another name"])
def test_run_action_sim(sim_builderer: Builderer, capsys: pytest.CaptureFixture[str], name: str) -> None:
    ret, output = sim_builderer.run_action(
        Action(
            name,
            [
                ["command1", "argument1"],
                ["command2"],
                ["command3", "argument2", "argument3"],
            ],
        )
    )
    captured = capsys.readouterr()

    assert ret == 0
    assert output == b""
    assert captured.err == ""
    assert captured.out.split("\n") == [
        name,
        "['command1', 'argument1']",
        "['command2']",
        "['command3', 'argument2', 'argument3']",
        "",
    ]


@pytest.mark.parametrize("name", ["some_name", "another name"])
def test_run_action_empty_sim(sim_builderer: Builderer, capsys: pytest.CaptureFixture[str], name: str) -> None:
    ret, output = sim_builderer.run_action(Action(name, []))
    captured = capsys.readouterr()

    assert ret == 0
    assert output == b""
    assert captured.err == ""
    assert captured.out.split("\n") == [
        name,
        "",
    ]


@pytest.mark.parametrize("name", ["some_name", "another name"])
def test_run_action_successes(empty_builderer: Builderer, capsys: pytest.CaptureFixture[str], name: str) -> None:
    ret, output = empty_builderer.run_action(
        Action(
            name,
            [
                [sys.executable, "-c", "print('ok1'); raise SystemExit(0);"],
                [sys.executable, "-c", "print('ok2'); raise SystemExit(0);"],
                [sys.executable, "-c", "print('ok3'); raise SystemExit(0);"],
            ],
        )
    )
    captured = capsys.readouterr()

    assert ret == 0
    assert output == b""
    assert captured.err == ""
    assert captured.out.split("\n") == [
        name,
        "",
    ]


@pytest.mark.parametrize("num_success_before_fail", range(3))
@pytest.mark.parametrize("name", ["some_name", "another name"])
def test_run_action_failure(
    empty_builderer: Builderer, capsys: pytest.CaptureFixture[str], name: str, num_success_before_fail: int
) -> None:
    ret, output = empty_builderer.run_action(
        Action(
            name,
            [
                *([[sys.executable, "-c", "print('ok1'); raise SystemExit(0);"]] * num_success_before_fail),
                [sys.executable, "-c", "print('fail'); raise SystemExit(1);"],
            ],
        )
    )
    captured = capsys.readouterr()

    assert ret == 1
    assert output == b"fail\n"
    assert captured.err == ""
    assert captured.out.split("\n") == [
        name,
        "",
    ]


def test_run_action_group_sim(sim_builderer: Builderer, capsys: pytest.CaptureFixture[str]) -> None:
    ret, output = sim_builderer.run_action_group(
        ActionGroup(
            actions=[
                Action("Name 1", [["command1a", "argument1a"], ["command2a", "argument2a"]]),
                Action("Name 2", [["command1n", "argument1n"], ["command2n", "argument2n"]]),
                Action("Name 3", [["command1c", "argument1c"], ["command2c", "argument2c"]]),
            ],
            num_parallel=1,
        )
    )
    captured = capsys.readouterr()

    assert ret == 0
    assert output == b""
    assert captured.err == ""
    assert captured.out.split("\n") == [
        "Name 1",
        "['command1a', 'argument1a']",
        "['command2a', 'argument2a']",
        "Name 2",
        "['command1n', 'argument1n']",
        "['command2n', 'argument2n']",
        "Name 3",
        "['command1c', 'argument1c']",
        "['command2c', 'argument2c']",
        "",
    ]


@pytest.mark.parametrize("num_parallel", [1, 2, 3, 4, 5])
def test_run_action_group_empty_sim(
    sim_builderer: Builderer, capsys: pytest.CaptureFixture[str], num_parallel: int
) -> None:
    ret, output = sim_builderer.run_action_group(ActionGroup(actions=[], num_parallel=num_parallel))
    captured = capsys.readouterr()

    assert ret == 0
    assert output == b""
    assert captured.err == ""
    assert captured.out.split("\n") == [""]


@pytest.mark.parametrize("num_parallel", [1, 2, 3, 4, 5])
def test_run_action_group_success(
    sim_builderer: Builderer, capsys: pytest.CaptureFixture[str], num_parallel: int
) -> None:
    ret, output = sim_builderer.run_action_group(ActionGroup(actions=[], num_parallel=num_parallel))
    captured = capsys.readouterr()

    assert ret == 0
    assert output == b""
    assert captured.err == ""
    assert captured.out.split("\n") == [""]


def test_run_error(empty_builderer: Builderer, capsys: pytest.CaptureFixture[str], tmp_path: pathlib.Path) -> None:
    empty_builderer.add_action_likes(
        Action("Failing action", [[sys.executable, "-c", "print('example output'); raise SystemExit(42)"]]),
        None,
    )
    ret = empty_builderer.run()
    captured = capsys.readouterr()

    assert ret == 42
    assert captured.err == ""
    assert captured.out.split("\n") == [
        "Failing action",
        "Encountered error running:",
        "example output",
        "",
        "",
    ]
