# This file is part of ValAsp which is released under the Apache License, Version 2.0.
# See file README.md for full license details.

"""This module defines domain primitives for class names and predicate names."""
import keyword
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ClassName:
    """A domain primitive for names of classes."""
    value: str

    def __post_init__(self):
        if not(1 <= len(self.value) <= 256):
            raise ValueError("the length of the given value is not in the range 1..256")
        if not re.fullmatch(r"_*[A-Z][A-Za-z0-9_]*", self.value):
            raise ValueError("invalid value")

    def __str__(self):
        return self.value

    def to_predicate(self) -> 'PredicateName':
        """Return the predicate name associated with this class name.

        :return: a predicate name
        """
        for i in range(len(self.value)):
            if self.value[i].isalpha():
                return PredicateName(self.value[:i] + self.value[i].lower() + self.value[i+1:])
        raise ValueError('cannot find an alpha character')


@dataclass(frozen=True)
class PredicateName:
    """A domain primitive for names of predicates."""
    value: str

    def __post_init__(self):
        if not(1 <= len(self.value) <= 256):
            raise ValueError("the length of the given value is not in the range 1..256")
        if not re.fullmatch(r"_*[a-z][A-Za-z0-9_]*", self.value):
            raise ValueError("invalid value")

    def __str__(self):
        return self.value

    def to_class(self) -> ClassName:
        """Return the class name associated with this predicate name.

        :return: a class name
        """
        for i in range(len(self.value)):
            if self.value[i].isalpha():
                return ClassName(self.value[:i] + self.value[i].upper() + self.value[i+1:])
        raise ValueError('cannot find an alpha character')


@dataclass(frozen=True)
class AttributeName(PredicateName):
    """A domain primitive for names of attributes."""
    def __post_init__(self):
        super().__post_init__()
        if keyword.iskeyword(self.value):
            raise ValueError(f"{self.value} is a Python keyword")
