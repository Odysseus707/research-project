import typing as t

from src.system import Env, Request

RoutingAlgorithm: t.TypeAlias = t.Callable[
    [Env, list[Request]], dict[tuple[int, int], bool]
]
