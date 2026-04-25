import pytest
import datetime
from reconsadfc.reconsadfc import Correlation_Calculator

@pytest.fixture
def calc():
    return Correlation_Calculator()

def test_starts(calc):
    assert calc.starts(10, 10) == 1
    assert calc.starts(10, 11) == 0

def test_equals(calc):
    assert calc.equals(10, 20, 10, 20) == 1
    assert calc.equals(10, 20, 10, 21) == 0

def test_meets(calc):
    assert calc.meets(15, 15) == 1
    assert calc.meets(15, 16) == 0

def test_overlaps(calc):
    assert calc.overlaps(10, 20, 15, 25) == 1
    assert calc.overlaps(10, 20, 20, 30) == 0

def test_during(calc):
    assert calc.during(15, 18, 10, 20) == 1
    assert calc.during(10, 20, 15, 18) == 0

def test_finishes(calc):
    assert calc.finishes(20, 20) == 1
    assert calc.finishes(19, 20) == 0

def test_before(calc):
    e_end = datetime.datetime(2023, 1, 1, 10, 0, 0)
    x_start = datetime.datetime(2023, 1, 1, 10, 0, 10)
    
    assert calc.before(e_end, x_start) == 0.1
    
    # Not before
    x_start_early = datetime.datetime(2023, 1, 1, 9, 59, 50)
    assert calc.before(e_end, x_start_early) == 0

def test_subject_correlation(calc):
    assert calc.subject_correlation([1, 2], [2, 3]) == 0.5
    assert calc.subject_correlation([1, 2], [1, 2]) == 1.0
    assert calc.subject_correlation([], []) == 0.0
    assert calc.subject_correlation(1, 1) == 1.0

def test_object_correlation(calc):
    assert calc.object_correlation([10, 11], [11, 12, 13]) == 1/3
    assert calc.object_correlation(10, 10) == 1.0
