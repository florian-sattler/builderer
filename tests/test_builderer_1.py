import pathlib
import sys

import pytest
from pytest_mock import MockerFixture

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


def test_add_action_likes_main_only(empty_builderer: Builderer) -> None:
    action = Action("only main", [])
    empty_builderer.add_action_likes(action, None)

    assert empty_builderer.actions_main == [action]
    assert empty_builderer.actions_post == []


def test_add_action_likes_post_only(empty_builderer: Builderer) -> None:
    action = Action("only post", [])
    empty_builderer.add_action_likes(None, action)

    assert empty_builderer.actions_main == []
    assert empty_builderer.actions_post == [action]


def test_run_main_then_post_lifo(empty_builderer: Builderer, mocker: MockerFixture) -> None:
    # run() processes the main queue in order, then the post queue in reverse
    # (LIFO), dispatching Actions and ActionGroups to the right handler.
    order: list[str] = []

    def fake_run_action(_self: Builderer, action: Action) -> tuple[int, bytes]:
        order.append(f"action:{action.name}")
        return 0, b""

    def fake_run_action_group(_self: Builderer, group: ActionGroup) -> tuple[int, bytes]:
        order.append(f"group:{group.actions[0].name}")
        return 0, b""

    mocker.patch.object(Builderer, "run_action", fake_run_action)
    mocker.patch.object(Builderer, "run_action_group", fake_run_action_group)

    empty_builderer.add_action_likes(Action("main-1", []), Action("post-1", []))
    empty_builderer.add_action_likes(ActionGroup([Action("main-group", [])], 1), Action("post-2", []))

    ret = empty_builderer.run()

    assert ret == 0
    assert order == ["action:main-1", "group:main-group", "action:post-2", "action:post-1"]


def test_run_unexpected_queue_entry(empty_builderer: Builderer) -> None:
    empty_builderer.actions_main.append("not an action")  # type: ignore[arg-type]

    with pytest.raises(ValueError) as e:
        empty_builderer.run()

    assert "Unexpected queue entry" in str(e.value)


def test_run_error_verbose(empty_builderer: Builderer, capsys: pytest.CaptureFixture[str]) -> None:
    # In verbose mode run_cmd does not capture output, so run() must not print a
    # separate captured-stdout block on error (the not-verbose branch is skipped).
    empty_builderer.verbose = True
    empty_builderer.add_action_likes(
        Action("Failing action", [[sys.executable, "-c", "raise SystemExit(7)"]]),
        None,
    )
    ret = empty_builderer.run()
    captured = capsys.readouterr()

    assert ret == 7
    assert captured.out.split("\n") == [
        "Failing action",
        f"['{sys.executable}', '-c', 'raise SystemExit(7)']",
        "Encountered error running:",
        "",
    ]
