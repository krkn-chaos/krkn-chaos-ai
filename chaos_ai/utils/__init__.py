# Simple Counter
from typing import Dict, Iterator


def id_generator() -> Iterator[int]:
    i = 1
    while True:
        yield i
        i += 1
