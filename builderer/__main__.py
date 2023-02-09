import argparse
from typing import Any

from builderer import __version__
from builderer.builderer import Builderer
from builderer.config import BuildConfig


def parse_args(argv: list[str] | None = None) -> tuple[str, dict[str, Any]]:
    parser = argparse.ArgumentParser(
        prog="builderer",
        description="Building and pushing containers. \n\nCommand line arguments take precedence over file configuration which in turn takes precedence over default values",
        epilog="This program is intended to run locally and inside ci/cd jobs.",
    )

    parser.add_argument("--registry", type=str, default=None, help="Registry URL [default='']")
    parser.add_argument("--prefix", type=str, default=None, help="Registry folder / namespace / user [default='']")
    parser.add_argument("--tags", nargs="+", type=str, default=None, help="Tags to use [default=['latest']]")
    parser.add_argument("--no-push", action="store_false", dest="push", default=None, help="Prevent pushing images.")
    parser.add_argument("--cache", action="store_true", default=None, help="Allow using cached images.")
    parser.add_argument("--verbose", action="store_true", default=None, help="Allow verbose output.")
    parser.add_argument("--simulate", action="store_true", default=None, help="Prevent issuing commands.")
    parser.add_argument("--backend", choices=["docker", "podman"], help="Overwrite backend to use [default=docker]")
    parser.add_argument("--config", type=str, default=".builderer.yml", help="Path to %(prog)s config.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    arguments = parser.parse_args(argv)

    return arguments.config, {k: v for k, v in vars(arguments).items() if v is not None and k != "config"}


def main(argv: list[str] | None = None) -> int:
    config_path, cli_args = parse_args(argv)

    try:
        config = BuildConfig.load(config_path)
    except FileNotFoundError as e:
        print(e)
        return 1

    builderer_args = config.parameters.dict(exclude_none=True) | cli_args

    builderer = Builderer(**builderer_args)

    for step in config.steps:
        step.add_to(builderer)

    return builderer.run()


if __name__ == "__main__":
    raise SystemExit(main())
