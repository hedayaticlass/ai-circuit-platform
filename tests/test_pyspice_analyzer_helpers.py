import numpy as np

from services.spice_analyzer.pyspice_analyzer import _to_scalar_float


def test_to_scalar_float_plain_number():
    assert _to_scalar_float(3.14) == 3.14


def test_to_scalar_float_0d_array():
    assert _to_scalar_float(np.array(5.0)) == 5.0


def test_to_scalar_float_1d_single_element_array():
    """این دقیقاً همان حالتی است که در نسخه‌های جدید numpy باعث
    'TypeError: only 0-dimensional arrays can be converted to Python
    scalars' می‌شد (وقتی float() مستقیماً روی خروجی PySpice صدا زده
    می‌شد)."""
    assert _to_scalar_float(np.array([2.718])) == 2.718


def test_to_scalar_float_int():
    assert _to_scalar_float(7) == 7.0
