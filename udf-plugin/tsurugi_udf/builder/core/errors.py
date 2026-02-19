from dataclasses import dataclass


class ToolNotFoundError(RuntimeError):
    pass


@dataclass
class CommandFailedError(RuntimeError):
    cmd: list[str]
    returncode: int
    stderr: str | None = None
