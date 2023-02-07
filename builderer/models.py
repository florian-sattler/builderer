import pydantic
import typing


class Parameters(pydantic.BaseModel):
    registry: str | None = pydantic.Field(None, description="Registry URL [default='']")
    prefix: str | None = pydantic.Field(None, description="Registry folder / namespace / user [default='']")
    push: bool | None = pydantic.Field(None, description="Push built images [default=True]")
    cache: bool | None = pydantic.Field(None, description="Allow using cached docker images [default=False]")
    verbose: bool | None = pydantic.Field(None, description="Print command output [default=False]")
    tags: list[str] | None = pydantic.Field(None, description="Tags to set [default=['latest']]")
    simulate: bool | None = pydantic.Field(None, description="Simulation: don't issue commands [default=False]")
    backend: typing.Literal["docker", "podman"] | None = pydantic.Field(
        None, description="Build backend to use [default=docker]"
    )

    class Config:
        extra = pydantic.Extra.forbid


class Arguments(Parameters):
    config: str = pydantic.Field(".builderer.yml", description="Path to build config.")
