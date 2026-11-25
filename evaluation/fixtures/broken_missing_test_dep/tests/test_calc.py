from freezegun import freeze_time
from calc import add


@freeze_time("2024-01-01")
def test_add():
    assert add(1, 2) == 3
