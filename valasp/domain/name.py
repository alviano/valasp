# This file is part of ValAsp which is released under the Apache License, Version 2.0.
# See file README.md for full license details.

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ClassName:
    value: str

    def __post_init__(self):
        if not(1 <= len(self.value) <= 256):
            raise ValueError("the length of the given value is not in the range 1..256")
        if not re.fullmatch(r'_*[A-Z][A-Za-z0-9_]*', self.value):
            raise ValueError("invalid value")

    def __str__(self):
        return self.value

    def to_predicate(self) -> 'PredicateName':
        return PredicateName(self.value[0].lower() + self.value[1:])


@dataclass(frozen=True)
class PredicateName:
    value: str

    def __post_init__(self):
        if not(1 <= len(self.value) <= 256):
            raise ValueError("the length of the given value is not in the range 1..256")
        if not re.fullmatch(r'_*[a-z][A-Za-z0-9_]*', self.value):
            raise ValueError("invalid value")

    def __str__(self):
        return self.value

    def to_class(self) -> ClassName:
        return ClassName(self.value[0].upper() + self.value[1:])
