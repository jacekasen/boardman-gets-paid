"""Unit tests for historical apron clustering and bunching analysis."""

import pandas as pd
import pytest

from boardman.clustering import (
    build_clustering_plot,
    calculate_historical_apron_clustering,
    summarize_clustering_evidence,
)


def test_calculate_historical_apron_clustering():
    """Verify historical payroll aggregation and threshold distance calculations."""
    df_clust = calculate_historical_apron_clustering()

    assert not df_clust.empty
    assert len(df_clust) == 180  # 30 franchises * 6 seasons
    assert "dist_to_second_apron" in df_clust.columns
    assert "is_bunching_under_second_apron" in df_clust.columns

    # Verify post-CBA bunching presence
    post_cba = df_clust[df_clust["is_post_cba"]]
    assert post_cba["is_bunching_under_second_apron"].sum() >= 4


def test_second_apron_attrition_trend():
    """Verify that teams above the Second Apron decline over time (4 -> 3 -> 1)."""
    df_clust = calculate_historical_apron_clustering()
    summary = summarize_clustering_evidence(df_clust)

    trend = summary["second_apron_attrition_trend"]
    assert trend["2023-24"] == 4
    assert trend["2024-25"] == 3
    assert trend["2025-26"] == 1


def test_build_clustering_plot():
    """Verify Plotly figure generation for apron clustering distribution."""
    df_clust = calculate_historical_apron_clustering()
    fig = build_clustering_plot(df_clust)

    assert fig is not None
    assert len(fig.data) == 2  # Pre-CBA and Post-CBA traces
