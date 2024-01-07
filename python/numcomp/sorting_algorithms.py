""" This module implements various sorting algorithms based on Python's bisect module. It is based on the implementation 
    suggested in https://stackoverflow.com/questions/6628744/search-for-before-and-after-values-in-a-long-sorted-list 
    """

import bisect
from typing import Sequence, Any, Optional


def _check_args(a: Sequence,
                x: Any):
    """ Checks the arguments a and x and raises a RuntimeError for invalid input. """

    if len(a) == 0:
        raise RuntimeError("a is empty.")


def index_eq(a: Sequence,
             x: Any) -> Optional[int]:
    """ Returns the index of the leftmost value in a that is exactly equal to x.
    
    :param a: 
    :param x: an object with '<' and '==' operators.
    :return: the index, or None if the x is not in a.
    """

    _check_args(a=a, x=x)

    i = bisect.bisect_left(a, x)
    if i != len(a) and a[i] == x:
        return i
    else:
        return None


def find_lt(a: Sequence, 
            x: Any) -> Any:
    """ Returns the rightmost value in a that is less than x.
    
    :param a: 
    :param x: an object with '<' and '==' operators.
    :return: 
    """

    _check_args(a=a, x=x)

    i = bisect.bisect_left(a, x)
    if i:
        return a[i-1]
    raise ValueError


def find_le(a: Sequence, 
            x: Any) -> Any:
    """ Returns the rightmost value in a that is less than or equal to x.

    :param a: 
    :param x: an object with '<' and '==' operators.
    :return: 
    """

    _check_args(a=a, x=x)

    i = bisect.bisect_right(a, x)
    if i:
        return a[i-1]
    raise ValueError


def find_gt(a: Sequence, 
            x: Any) -> Any:
    """ Returns the leftmost value in a that is greater than x.

    :param a: 
    :param x: an object with '<' and '==' operators.
    :return: 
    """

    _check_args(a=a, x=x)

    i = bisect.bisect_right(a, x)
    if i != len(a):
        return a[i]
    raise ValueError


def find_ge(a: Sequence, 
            x: Any) -> Any:
    """ Returns the leftmost value in a that is greater than or equal to x.

        Remark: raises a value error if 

    :param a: 
    :param x: an object with '<' and '==' operators.
    :return: 
    """

    _check_args(a=a, x=x)

    i = bisect.bisect_left(a, x)
    if i != len(a):
        return a[i]
    raise ValueError
