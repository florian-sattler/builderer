import pydantic_argparse

from builderer import __version__
from builderer.builderer import Builderer
from builderer.config import BuildConfig
from builderer.models import Arguments


def main(argv: list[str] | None = None) -> int:
    cli_args = pydantic_argparse.ArgumentParser(
        model=Arguments,
        prog="builderer",
        description="Building and pushing containers.",
        version=__version__,
        epilog="This program is intended to run inside a ci/cd job.",
    ).parse_typed_args(argv)

    try:
        config = BuildConfig.load(cli_args.config)
    except FileNotFoundError as e:
        print(e)
        return 1

    builderer_args = config.parameters.dict(exclude_none=True) | cli_args.dict(exclude={"config"}, exclude_none=True)

    builderer = Builderer(**builderer_args)

    for step in config.steps:
        step.add_to(builderer)

    return builderer.run()


if __name__ == "__main__":
    raise SystemExit(main())
