import sys
from unittest.mock import MagicMock, call, patch

import pytest

from builderer import Action, ActionGroup, Builderer


@pytest.fixture
def builderer_sim() -> Builderer:
    return Builderer(verbose=False, simulate=True, max_parallel=2)


@pytest.fixture
def builderer() -> Builderer:
    return Builderer(verbose=False, simulate=False, max_parallel=2)


@pytest.fixture
def action_success_1() -> Action:
    return Action(name="Test Action", commands=[["echo", "Hello!"]])


@pytest.fixture
def action_success_2() -> Action:
    return Action(name="Test Action", commands=[["echo", "World!"]])


@pytest.fixture
def action_error() -> Action:
    return Action(name="Test Action", commands=[[sys.executable, "-c", "print('error'); raise SystemExit(1)"]])


@pytest.fixture
def action_invalid() -> Action:
    return Action(name="Test Action", commands=[["invalid_command"]])


@pytest.fixture
def action_group_success_success(action_success_1: Action, action_success_2: Action) -> ActionGroup:
    return ActionGroup(actions=[action_success_1, action_success_2], num_parallel=1)


@pytest.fixture
def action_group_success_error(action_success_1: Action, action_error: Action) -> ActionGroup:
    return ActionGroup(actions=[action_success_1, action_error], num_parallel=1)


@pytest.fixture
def action_group_success_invalid(action_success_1: Action, action_invalid: Action) -> ActionGroup:
    return ActionGroup(actions=[action_success_1, action_invalid], num_parallel=1)


def test_run_cmd_simulate(builderer_sim: Builderer) -> None:
    returncode, stdout = builderer_sim.run_cmd(["echo", "Hello, World!"])
    assert returncode == 0
    assert stdout == b""


@patch("subprocess.run")
def test_run_cmd_verbose(mock_subprocess_run: MagicMock, builderer: Builderer) -> None:
    mock_subprocess_run.return_value = MagicMock(returncode=0, stdout=b"Hello, World!")
    returncode, stdout = builderer.run_cmd(["echo", "Hello, World!"])

    assert returncode == 0
    assert stdout == b"Hello, World!"


def test_run_action_success_sim(builderer_sim: Builderer, action_success_1: Action) -> None:
    returncode, stdout = builderer_sim.run_action(action_success_1)

    assert returncode == 0
    assert stdout == b""


def test_run_action_success(builderer: Builderer, action_success_1: Action) -> None:
    returncode, stdout = builderer.run_action(action_success_1)

    assert returncode == 0
    assert stdout == b""


def test_run_action_failure_sim(builderer_sim: Builderer, action_error: Action) -> None:
    returncode, stdout = builderer_sim.run_action(action_error)

    assert returncode == 0
    assert stdout == b""


def test_run_action_failure(builderer: Builderer, action_error: Action) -> None:
    returncode, stdout = builderer.run_action(action_error)

    assert returncode != 0
    assert stdout == b"error\n"


def test_run_action_error(builderer: Builderer, action_invalid: Action) -> None:
    with pytest.raises(FileNotFoundError):
        builderer.run_action(action_invalid)


def test_run_action_group_success_sim(builderer_sim: Builderer, action_group_success_success: ActionGroup) -> None:
    returncode, stdout = builderer_sim.run_action_group(action_group_success_success)

    assert returncode == 0
    assert stdout == b""


def test_run_action_group_success(builderer: Builderer, action_group_success_success: ActionGroup) -> None:
    returncode, stdout = builderer.run_action_group(action_group_success_success)

    assert returncode == 0
    assert stdout == b""


def test_run_action_group_success_mocked(builderer: Builderer, action_group_success_success: ActionGroup) -> None:
    with patch.object(Builderer, "run_action", return_value=(0, b"")) as mock_run_action:
        returncode, stdout = builderer.run_action_group(action_group_success_success)

        assert returncode == 0
        assert stdout == b""
        assert mock_run_action.call_count == 2


def test_run_action_group_failure(builderer: Builderer, action_group_success_error: ActionGroup) -> None:
    returncode, stdout = builderer.run_action_group(action_group_success_error)

    assert returncode != 0
    assert stdout == b"error\n"


def test_run_action_group_failure_mocked(builderer: Builderer, action_group_success_error: ActionGroup) -> None:
    with patch.object(Builderer, "run_action", side_effect=[(0, b""), (1, b"Error")]) as mock_run_action:
        returncode, stdout = builderer.run_action_group(action_group_success_error)

        assert returncode == 1
        assert stdout == b"Error"
        assert mock_run_action.call_count == 2


@pytest.mark.parametrize("num_parallel", [1, 2, 3])
def test_run_action_group_exception_mocked(
    num_parallel: int, builderer: Builderer, action_group_success_success: ActionGroup
) -> None:
    action_group_success_success.num_parallel = num_parallel
    with patch.object(
        Builderer, "run_action", side_effect=[(0, b""), FileNotFoundError("Something went wrong")]
    ) as mock_run_action:
        returncode, stdout = builderer.run_action_group(action_group_success_success)

        assert returncode == 1
        assert stdout == b"Something went wrong"
        assert mock_run_action.call_count == 2


@pytest.mark.parametrize("num_parallel", [1, 2])
def test_run_action_group_no_further_actions(num_parallel: int, builderer: Builderer) -> None:
    action1 = Action(name="Action 1", commands=[["echo", "Hello"]])
    action2 = Action(name="Action 2", commands=[["false"]])
    action3 = Action(name="Action 3", commands=[["echo", "World"]])
    group = ActionGroup(actions=[action1, action2, action3], num_parallel=num_parallel)

    with patch.object(Builderer, "run_action") as mock_run_action:
        mock_run_action.side_effect = [(0, b""), (1, b"Error"), (0, b"")]

        returncode, stdout = builderer.run_action_group(group)

        assert returncode == 1
        assert stdout == b"Error"

        assert mock_run_action.call_count == 2
        assert call(action1) in mock_run_action.mock_calls
        assert call(action2) in mock_run_action.mock_calls

        assert call(action3) not in mock_run_action.mock_calls


def test_run_success(builderer_sim: Builderer, action_group_success_success: ActionGroup) -> None:
    builderer_sim.add_action_likes(main=action_group_success_success, post=None)
    returncode = builderer_sim.run()
    assert returncode == 0


def test_run_failure(builderer: Builderer, action_group_success_invalid: ActionGroup) -> None:
    builderer.add_action_likes(main=action_group_success_invalid, post=None)
    returncode = builderer.run()
    assert returncode != 0
