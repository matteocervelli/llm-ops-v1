import fnmatch
import re
from dataclasses import dataclass
from typing import Any, Literal, cast

from redis import Redis

_ARSET_SCRIPT = """
local index_key = KEYS[1]
local value_key = KEYS[2]
local meta_key = KEYS[3]
local start = tonumber(ARGV[1])
local ttl = tonumber(ARGV[2])
local new_slots = 0

for i = 3, #ARGV do
  local idx = start + i - 3
  local field = tostring(idx)
  if redis.call("HEXISTS", value_key, field) == 0 then
    new_slots = new_slots + 1
  end
  redis.call("HSET", value_key, field, ARGV[i])
  redis.call("ZADD", index_key, idx, field)
end

if ttl > 0 then
  redis.call("EXPIRE", index_key, ttl)
  redis.call("EXPIRE", value_key, ttl)
  if redis.call("EXISTS", meta_key) == 1 then
    redis.call("EXPIRE", meta_key, ttl)
  end
end

return new_slots
"""

_ARINSERT_SCRIPT = """
local index_key = KEYS[1]
local value_key = KEYS[2]
local meta_key = KEYS[3]
local ttl = tonumber(ARGV[1])
local last = redis.call("HGET", meta_key, "last_index")
local start = 0

if last then
  start = tonumber(last) + 1
end

local last_written = start
for i = 2, #ARGV do
  local idx = start + i - 2
  local field = tostring(idx)
  redis.call("HSET", value_key, field, ARGV[i])
  redis.call("ZADD", index_key, idx, field)
  last_written = idx
end

redis.call("HSET", meta_key, "last_index", tostring(last_written))

if ttl > 0 then
  redis.call("EXPIRE", index_key, ttl)
  redis.call("EXPIRE", value_key, ttl)
  redis.call("EXPIRE", meta_key, ttl)
end

return last_written
"""

_PREDICATE_TOKENS = {"EXACT", "MATCH", "GLOB", "RE"}
_OPTION_TOKENS = {"AND", "OR", "LIMIT", "WITHVALUES", "NOCASE"}
_BACKREFERENCE_RE = re.compile(r"\\[1-9]")
_MAX_REGEX_BYTES = 2048

PredicateType = Literal["EXACT", "MATCH", "GLOB", "RE"]
CombineMode = Literal["AND", "OR"]
GrepResult = list[int] | list[tuple[int, str]]


@dataclass(frozen=True)
class _Predicate:
    kind: PredicateType
    pattern: str
    regex: re.Pattern[str] | None = None


@dataclass(frozen=True)
class _GrepPlan:
    predicates: tuple[_Predicate, ...]
    combine: CombineMode
    limit: int | None
    with_values: bool
    nocase: bool


class RedisArray:
    def __init__(
        self,
        redis_url: str,
        ttl_seconds: int | None = 604_800,
        key_prefix: str = "llm_ops_v1:array",
    ) -> None:
        if ttl_seconds is not None and ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be greater than zero or None")
        if not key_prefix:
            raise ValueError("key_prefix must not be empty")
        self.redis_url = redis_url
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix
        self._client = Redis.from_url(redis_url, decode_responses=True)

    def arset(self, key: str, index: int, *values: str) -> int:
        self._validate_key(key)
        self._validate_index(index)
        self._validate_values(values)
        result = self._client.eval(
            _ARSET_SCRIPT,
            3,
            self._index_key(key),
            self._value_key(key),
            self._meta_key(key),
            index,
            self._ttl_arg(),
            *values,
        )
        return int(cast(int, result))

    def arinsert(self, key: str, *values: str) -> int:
        self._validate_key(key)
        self._validate_values(values)
        result = self._client.eval(
            _ARINSERT_SCRIPT,
            3,
            self._index_key(key),
            self._value_key(key),
            self._meta_key(key),
            self._ttl_arg(),
            *values,
        )
        return int(cast(int, result))

    def argrep(self, key: str, start: int | str, end: int | str, *args: str | int) -> GrepResult:
        self._validate_key(key)
        plan = _parse_grep_plan(args)
        if plan.limit == 0:
            return []
        resolved_start, resolved_end = self._resolve_bounds(key, start, end)
        if resolved_start is None or resolved_end is None:
            return []

        entries = self._range_entries(key, resolved_start, resolved_end)
        matches: list[int] | list[tuple[int, str]] = []
        for index, value in entries:
            if not _matches_plan(value, plan):
                continue
            if plan.with_values:
                cast(list[tuple[int, str]], matches).append((index, value))
            else:
                cast(list[int], matches).append(index)
            if plan.limit is not None and len(matches) >= plan.limit:
                break
        return matches

    def ping(self) -> None:
        self._client.ping()

    def _range_entries(self, key: str, start: int, end: int) -> list[tuple[int, str]]:
        index_key = self._index_key(key)
        if start <= end:
            raw_indexes = cast(list[Any], self._client.zrangebyscore(index_key, start, end))
        else:
            raw_indexes = cast(list[Any], self._client.zrevrangebyscore(index_key, start, end))
        indexes = [str(index) for index in raw_indexes]
        if not indexes:
            return []
        raw_values = cast(list[Any], self._client.hmget(self._value_key(key), indexes))
        values = [str(value) for value in raw_values]
        return [(int(index), value) for index, value in zip(indexes, values, strict=True)]

    def _resolve_bounds(
        self,
        key: str,
        start: int | str,
        end: int | str,
    ) -> tuple[int | None, int | None]:
        max_index = self._max_index(key)
        if max_index is None:
            return None, None
        return (
            self._resolve_bound(start, max_index),
            self._resolve_bound(end, max_index),
        )

    def _resolve_bound(self, bound: int | str, max_index: int) -> int:
        if bound == "-":
            return 0
        if bound == "+":
            return max_index
        if isinstance(bound, str):
            if not bound.isdigit():
                raise ValueError("array bounds must be non-negative integers, '-' or '+'")
            return int(bound)
        self._validate_index(bound)
        return bound

    def _max_index(self, key: str) -> int | None:
        values = cast(list[Any], self._client.zrevrange(self._index_key(key), 0, 0))
        if not values:
            return None
        return int(str(values[0]))

    def _ttl_arg(self) -> int:
        return 0 if self.ttl_seconds is None else self.ttl_seconds

    def _index_key(self, key: str) -> str:
        return f"{self.key_prefix}:{key}:idx"

    def _value_key(self, key: str) -> str:
        return f"{self.key_prefix}:{key}:values"

    def _meta_key(self, key: str) -> str:
        return f"{self.key_prefix}:{key}:meta"

    @staticmethod
    def _validate_key(key: str) -> None:
        if not key:
            raise ValueError("key must not be empty")

    @staticmethod
    def _validate_index(index: int) -> None:
        if index < 0:
            raise ValueError("array index must be non-negative")

    @staticmethod
    def _validate_values(values: tuple[str, ...]) -> None:
        if not values:
            raise ValueError("at least one value is required")


def _parse_grep_plan(args: tuple[str | int, ...]) -> _GrepPlan:
    if not args:
        raise ValueError("ARGREP requires at least one predicate")

    predicates: list[_Predicate] = []
    combine: CombineMode = "OR"
    limit: int | None = None
    with_values = False
    nocase = False
    index = 0
    while index < len(args):
        token = str(args[index]).upper()
        if token in _PREDICATE_TOKENS:
            if index + 1 >= len(args):
                raise ValueError(f"{token} requires a pattern")
            predicates.append(
                _build_predicate(cast(PredicateType, token), str(args[index + 1]), nocase)
            )
            index += 2
        elif token in {"AND", "OR"}:
            combine = cast(CombineMode, token)
            index += 1
        elif token == "LIMIT":
            if index + 1 >= len(args):
                raise ValueError("LIMIT requires a count")
            limit = _parse_limit(args[index + 1])
            index += 2
        elif token == "WITHVALUES":
            with_values = True
            index += 1
        elif token == "NOCASE":
            nocase = True
            predicates = [_rebuild_predicate(predicate, nocase=True) for predicate in predicates]
            index += 1
        else:
            raise ValueError(f"unsupported ARGREP token: {args[index]}")

    if not predicates:
        raise ValueError("ARGREP requires at least one predicate")
    return _GrepPlan(tuple(predicates), combine, limit, with_values, nocase)


def _build_predicate(kind: PredicateType, pattern: str, nocase: bool) -> _Predicate:
    if kind != "RE":
        return _Predicate(kind=kind, pattern=pattern)
    _validate_regex_pattern(pattern)
    flags = re.IGNORECASE if nocase else 0
    try:
        return _Predicate(kind=kind, pattern=pattern, regex=re.compile(pattern, flags))
    except re.error as exc:
        raise ValueError("invalid regular expression") from exc


def _rebuild_predicate(predicate: _Predicate, nocase: bool) -> _Predicate:
    return _build_predicate(predicate.kind, predicate.pattern, nocase)


def _validate_regex_pattern(pattern: str) -> None:
    if not pattern:
        raise ValueError("regular expression is empty")
    if len(pattern.encode("utf-8")) > _MAX_REGEX_BYTES:
        raise ValueError("regular expression is too long, maximum is 2048 bytes")
    if _BACKREFERENCE_RE.search(pattern):
        raise ValueError("backreferences are not supported")


def _parse_limit(value: str | int) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("LIMIT must be a non-negative integer") from exc
    if limit < 0:
        raise ValueError("LIMIT must be a non-negative integer")
    return limit


def _matches_plan(value: str, plan: _GrepPlan) -> bool:
    results = [_matches_predicate(value, predicate, plan.nocase) for predicate in plan.predicates]
    if plan.combine == "AND":
        return all(results)
    return any(results)


def _matches_predicate(value: str, predicate: _Predicate, nocase: bool) -> bool:
    candidate = value.casefold() if nocase else value
    pattern = predicate.pattern.casefold() if nocase else predicate.pattern
    if predicate.kind == "EXACT":
        return candidate == pattern
    if predicate.kind == "MATCH":
        return pattern in candidate
    if predicate.kind == "GLOB":
        return fnmatch.fnmatchcase(candidate, pattern)
    if predicate.regex is None:
        raise RuntimeError("compiled regex missing from RE predicate")
    return predicate.regex.search(value) is not None
