import argparse
from typing import Any

import pydantic

import builderer._documentation as docs
from builderer import __version__
from builderer.builderer import Builderer
from builderer.config import BuildererConfig


def parse_args(argv: list[str] | None = None) -> tuple[str, dict[str, Any]]:
    parser = argparse.ArgumentParser(
        prog="builderer",
        description="Building and pushing containers. \n\nCommand line arguments take precedence over file configuration which in turn takes precedence over default values",
        epilog="This program is intended to run locally and inside ci/cd jobs.",
    )

    parser.add_argument("--registry", type=str, default=None, help=docs.arg_registry_desc)
    parser.add_argument("--prefix", type=str, default=None, help=docs.arg_prefix_desc)
    parser.add_argument("--tags", nargs="+", type=str, default=None, help=docs.arg_tags_desc)
    parser.add_argument("--no-push", action="store_false", dest="push", default=None, help=docs.arg_cli_config)
    parser.add_argument("--cache", action="store_true", default=None, help=docs.arg_cache_desc)
    parser.add_argument("--verbose", action="store_true", default=None, help=docs.arg_verbose_desc)
    parser.add_argument("--simulate", action="store_true", default=None, help=docs.arg_simulate_desc)
    parser.add_argument("--backend", choices=["docker", "podman"], help=docs.arg_backend_desc)
    parser.add_argument("--config", type=str, default=".builderer.yml", help=docs.arg_cli_config)
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    arguments = parser.parse_args(argv)

    return arguments.config, {k: v for k, v in vars(arguments).items() if v is not None and k != "config"}


def main(argv: list[str] | None = None) -> int:
    config_path, cli_args = parse_args(argv)

    try:
        config = BuildererConfig.load(config_path)
    except (FileNotFoundError, pydantic.ValidationError) as e:
        print(e)
        return 1

    builderer_args = config.parameters.dict(exclude_none=True) | cli_args

    builderer = Builderer(**builderer_args)

    for step in config.steps:
        step.add_to(builderer)

    return builderer.run()


if __name__ == "__main__":
    raise SystemExit(main())  # pragma: no cover
