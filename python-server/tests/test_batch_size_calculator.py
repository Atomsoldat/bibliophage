"""Unit tests for batch_size_calculator.py."""

import pytest

from ingestion.batch_size_calculator import calculate_batch_size


@pytest.mark.unit
def test_normal_case():
    result = calculate_batch_size(available_ram_gb=8.0)
    assert result["recommended_batch_size"] >= 1
    assert result["available_ram_gb"] == 8.0
    assert result["peak_memory_gb"] > 0


@pytest.mark.unit
def test_math_is_correct():
    # With 8GB RAM, 0.5GB overhead, 67.8MB/page, 80% safety margin:
    # usable = 7.5 GB = 7680 MB
    # theoretical_max = 7680 / 67.8 ≈ 113.3 pages
    # safe_max = 113.3 * 0.8 ≈ 90 pages
    result = calculate_batch_size(
        available_ram_gb=8.0,
        memory_per_page_mb=67.8,
        overhead_gb=0.5,
        safety_margin=0.8,
    )
    assert result["recommended_batch_size"] == 90


@pytest.mark.unit
def test_insufficient_ram_raises():
    with pytest.raises(ValueError, match="Insufficient RAM"):
        calculate_batch_size(available_ram_gb=0.5, overhead_gb=1.0)


@pytest.mark.unit
def test_exactly_at_overhead_raises():
    with pytest.raises(ValueError):
        calculate_batch_size(available_ram_gb=1.0, overhead_gb=1.0)


@pytest.mark.unit
def test_clamp_to_min_batch_size():
    # Very little RAM → calculated batch would be < min
    result = calculate_batch_size(
        available_ram_gb=0.6,
        overhead_gb=0.5,
        memory_per_page_mb=67.8,
        min_batch_size=1,
    )
    assert result["recommended_batch_size"] == 1


@pytest.mark.unit
def test_clamp_to_max_batch_size():
    # Enormous RAM → calculated batch would exceed max
    result = calculate_batch_size(
        available_ram_gb=1000.0,
        max_batch_size=500,
    )
    assert result["recommended_batch_size"] == 500


@pytest.mark.unit
def test_safety_margin_reduces_batch_size():
    conservative = calculate_batch_size(available_ram_gb=8.0, safety_margin=0.5)
    aggressive = calculate_batch_size(available_ram_gb=8.0, safety_margin=1.0)
    assert conservative["recommended_batch_size"] < aggressive["recommended_batch_size"]


@pytest.mark.unit
def test_higher_memory_per_page_reduces_batch_size():
    light = calculate_batch_size(available_ram_gb=8.0, memory_per_page_mb=30.0)
    heavy = calculate_batch_size(available_ram_gb=8.0, memory_per_page_mb=150.0)
    assert light["recommended_batch_size"] > heavy["recommended_batch_size"]


@pytest.mark.unit
def test_return_keys_present():
    result = calculate_batch_size(available_ram_gb=8.0)
    assert "recommended_batch_size" in result
    assert "peak_memory_gb" in result
    assert "available_ram_gb" in result
    assert "memory_per_page_mb" in result
    assert "usable_ram_gb" in result
    assert "safety_margin" in result


@pytest.mark.unit
def test_peak_memory_accounts_for_batch_size():
    result = calculate_batch_size(
        available_ram_gb=8.0,
        memory_per_page_mb=67.8,
        overhead_gb=0.5,
    )
    expected_peak = 0.5 + (result["recommended_batch_size"] * 67.8 / 1024)
    assert result["peak_memory_gb"] == round(expected_peak, 2)
