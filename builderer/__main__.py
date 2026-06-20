"""Console entrypoint for builderer both when running as a module as well as when started as a console script."""

import argparse
from typing import Any

import pydantic

import builderer._documentation as docs
from builderer import __version__
from builderer.actions import ActionFactory
from builderer.builderer import Builderer
from builderer.config import BuildererConfig, select_steps


def _max_parallel(value: str) -> int | str:
    """Parse the --max-parallel argument: either "cores" or a positive integer."""
    if value == "cores":
        return value

    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("max-parallel needs to be a positive integer or 'cores'")
    return parsed


def parse_args(argv: list[str] | None = None) -> tuple[str, dict[str, Any]]:
    """Parse commandline arguments.

    Args:
        argv (list[str] | None, optional): List of command line arguments to parse. Defaults to sys.argv.

    Returns:
        tuple[str, dict[str, Any]]: Path to config and a dict of all remaining config options.
    """
    parser = argparse.ArgumentParser(
        prog="builderer",
        description="Building and pushing containers. \n\nCommand line arguments take precedence over file configuration which in turn takes precedence over default values",
        epilog="This program is intended to run locally as well as inside ci/cd jobs.",
    )

    parser.add_argument("--registry", type=str, default=None, help=docs.arg_registry_desc)
    parser.add_argument("--prefix", type=str, default=None, help=docs.arg_prefix_desc)
    parser.add_argument("--tags", nargs="+", type=str, default=None, help=docs.arg_tags_desc)
    parser.add_argument("--no-push", action="store_false", dest="push", default=None, help=docs.arg_cli_config)
    parser.add_argument("--cache", action="store_true", default=None, help=docs.arg_cache_desc)
    parser.add_argument("--verbose", action="store_true", default=None, help=docs.arg_verbose_desc)
    parser.add_argument("--simulate", action="store_true", default=None, help=docs.arg_simulate_desc)
    parser.add_argument("--backend", choices=["docker", "podman"], help=docs.arg_backend_desc)
    parser.add_argument("--max-parallel", type=_max_parallel, default=None, help=docs.arg_max_parallel_desc)
    parser.add_argument("--skip", action="append", default=None, metavar="ID", help=docs.arg_skip_desc)
    parser.add_argument("--only", action="append", default=None, metavar="ID", help=docs.arg_only_desc)
    parser.add_argument("--config", type=str, default=".builderer.yml", help=docs.arg_cli_config)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    arguments = parser.parse_args(argv)

    return arguments.config, {k: v for k, v in vars(arguments).items() if v is not None and k != "config"}


def main(argv: list[str] | None = None) -> int:
    """Run builderer while optionally specifying which cli argument to use.

    Args:
        argv (list[str] | None, optional): List of command line arguments to parse. Defaults to sys.argv.

    Returns:
        int: exit code
    """
    config_path, cli_args = parse_args(argv)

    # --skip / --only select which steps run; they are not factory/runner parameters.
    skip = set(cli_args.pop("skip", None) or [])
    only = set(cli_args.pop("only", None) or [])

    try:
        config = BuildererConfig.load(config_path)
    except (FileNotFoundError, pydantic.ValidationError) as e:
        print(e)
        return 1

    unknown = (skip | only) - config.step_ids
    if unknown:
        print(f"Unknown step id(s): {', '.join(sorted(unknown))}")
        return 1

    builderer_args = config.parameters.model_dump(exclude_none=True) | cli_args

    factory_args = {k: v for k, v in builderer_args.items() if k not in {"verbose", "simulate", "max_parallel"}}
    runner_args = {k: v for k, v in builderer_args.items() if k in {"verbose", "simulate", "max_parallel"}}

    factory = ActionFactory(**factory_args)
    runner = Builderer(**runner_args)

    for step in select_steps(config.steps, only=only, skip=skip):
        runner.add_action_likes(*step.create(factory))

    try:
        return runner.run()
    except KeyboardInterrupt:
        print("Aborted!")
        return 130  # 128 + SIGINT(2), the conventional exit code for a Ctrl-C interrupt


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
