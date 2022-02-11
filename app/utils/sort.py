from itertools import tee
from typing import Iterable, List


def _try_to_float(value):
    try:
        float(value)
    except ValueError:
        return False
    else:
        return True


def smart_sort(items: Iterable[str]) -> List[str]:
    original_items, test_items = tee(items)

    _can_float = True
    for item in test_items:
        if not _try_to_float(item):
            _can_float = False
            break

    return sorted(original_items, key=float if _can_float else str)
