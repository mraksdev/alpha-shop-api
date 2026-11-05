"""Task 1: generate the sequence 122333444455555...

The sequence contains the natural numbers in ascending order, where every
number ``n`` is repeated ``n`` times:

    1, 2, 2, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 5, ...

Run the module to print the beginning of the sequence:

    python task1_sequence.py
    python task1_sequence.py --count 25
"""

import argparse
from collections.abc import Iterator


def generate_sequence(count: int | None = None) -> Iterator[int]:
    """Yield the sequence 1, 2, 2, 3, 3, 3, ... item by item.

    When ``count`` is ``None`` the generator is infinite. Otherwise it
    yields exactly ``count`` items.
    """
    if count is not None and count < 0:
        raise ValueError('count must not be negative')

    yielded = 0
    number = 1
    while count is None or yielded < count:
        for _ in range(number):
            if count is not None and yielded >= count:
                return
            yield number
            yielded += 1
        number += 1


def build_sequence(count: int) -> str:
    """Return the first ``count`` items of the sequence as a string."""
    return ''.join(str(number) for number in generate_sequence(count))


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Print the sequence 122333444455555...',
    )
    parser.add_argument(
        '--count',
        type=int,
        default=15,
        help='number of items to print (default: 15)',
    )
    return parser.parse_args()


def main() -> None:
    """Print the requested number of sequence items."""
    args = parse_args()
    print(build_sequence(args.count))


if __name__ == '__main__':
    main()
