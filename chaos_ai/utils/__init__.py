# Simple Counter
from typing import Iterator


def id_generator() -> Iterator[int]:
    i = 1
    while True:
        yield i
        i += 1
