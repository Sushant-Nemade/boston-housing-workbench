import pytest

from boston_housing.loadcheck import run_load


def test_load_counts_real_requests_and_negative_security_checks():
    report = run_load(users=3, concurrency=2)
    assert report["workflow_requests_observed"] == 9
    assert report["status_counts"] == {200: 6, 404: 3}
    assert report["passed"] and report["failed_workflows"] == 0
    assert 1 <= report["peak_active_workflows"] <= 2
    assert len(report["adversarial_checks"]) == 4


@pytest.mark.parametrize("users,concurrency", [(0, 1), (1001, 1), (1, 33), (1, 0)])
def test_load_is_bounded_and_has_no_target_url_argument(users, concurrency):
    with pytest.raises(ValueError):
        run_load(users, concurrency)
