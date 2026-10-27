import math

import pytest
from pydantic import ValidationError

from boston_housing.contracts import FEATURES, FEATURE_NAMES, Scenario


def scenario():
    return {name: spec["default"] for name, spec in FEATURES.items()}


@pytest.mark.parametrize("extra", ["B", "LSTAT", "MEDV", "__proto__"])
def test_unknown_or_excluded_features_rejected(extra):
    with pytest.raises(ValidationError):
        Scenario.model_validate({**scenario(), extra: 1})


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf, True, "6.4", -1, 100])
def test_room_inputs_are_strict_finite_and_bounded(value):
    with pytest.raises(ValidationError):
        Scenario.model_validate({**scenario(), "RM": value})


def test_named_vector_does_not_depend_on_json_key_order():
    values = scenario()
    assert Scenario.model_validate(dict(reversed(list(values.items())))).vector() == [
        values[name] for name in FEATURE_NAMES
    ]
    assert "B" not in FEATURE_NAMES and "LSTAT" not in FEATURE_NAMES


@pytest.mark.parametrize("key,value", [("RAD", 2.5), ("CHAS", True), ("CHAS", 2)])
def test_categorical_values_are_not_coerced(key, value):
    with pytest.raises(ValidationError):
        Scenario.model_validate({**scenario(), key: value})
