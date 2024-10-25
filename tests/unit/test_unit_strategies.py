from eth.constants import UINT_256_MAX

from moccasin.utils import get_int_bounds

# from moccasin.strategies import strategy # TODO: Test this 

def test_get_int_bounds_uint256():
    lower, upper = get_int_bounds("uint256")
    assert lower == 0
    assert upper == UINT_256_MAX

def test_get_int_bounds_int256():
    lower, upper = get_int_bounds("int256")
    assert lower == -(2 ** 255)
    assert upper == 2 ** 255 - 1
