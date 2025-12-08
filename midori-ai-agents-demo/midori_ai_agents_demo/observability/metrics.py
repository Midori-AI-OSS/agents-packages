"""Metrics collection for the reasoning pipeline.

This demonstrates how to instrument code for observability,
including timing, counters, and gauges.
"""

from dataclasses import dataclass
from dataclasses import field

from typing import Dict
from typing import List

from ..enums import StageType


@dataclass
class MetricPoint:
    """A single metric data point.
    
    Attributes:
        name: Metric name (e.g., "stage_duration_ms")
        value: Metric value
        labels: Optional labels for grouping (e.g., {"stage": "preprocessing"})
    """

    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Collector for pipeline metrics.
    
    This demonstrates basic metrics collection patterns:
    - Timing measurements
    - Counters (increments only)
    - Gauges (arbitrary values)
    - Labels for grouping
    
    In production, integrate with:
    - Prometheus
    - StatsD
    - DataDog
    - CloudWatch
    - OpenTelemetry
    
    This demo collector:
    - Stores metrics in memory
    - Provides basic aggregation
    - Shows the metrics collection pattern
    - Can be exported to external systems
    """

    def __init__(self):
        """Initialize the metrics collector."""
        self._metrics: List[MetricPoint] = []

    def record_duration(self, stage_type: StageType, duration_ms: float) -> None:
        """Record a stage duration.
        
        Args:
            stage_type: Which stage this duration is for
            duration_ms: Duration in milliseconds
        """
        self._metrics.append(MetricPoint(name="stage_duration_ms", value=duration_ms, labels={"stage": stage_type.value}))

    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] | None = None) -> None:
        """Increment a counter metric.
        
        Args:
            name: Counter name
            value: Amount to increment by (default 1.0)
            labels: Optional labels for grouping
        """
        self._metrics.append(MetricPoint(name=name, value=value, labels=labels or {}))

    def record_gauge(self, name: str, value: float, labels: Dict[str, str] | None = None) -> None:
        """Record a gauge metric (arbitrary value).
        
        Args:
            name: Gauge name
            value: Current value
            labels: Optional labels for grouping
        """
        self._metrics.append(MetricPoint(name=name, value=value, labels=labels or {}))

    def get_metrics(self) -> List[MetricPoint]:
        """Get all collected metrics.
        
        Returns:
            List of all metric points collected
        """
        return self._metrics.copy()

    def get_summary(self) -> Dict[str, float]:
        """Get a summary of key metrics.
        
        This demonstrates basic metric aggregation.
        In production, use proper time-series databases.
        
        Returns:
            Dictionary of aggregated metrics
        """
        summary = {}

        for stage_type in StageType:
            stage_metrics = [m.value for m in self._metrics if m.name == "stage_duration_ms" and m.labels.get("stage") == stage_type.value]

            if stage_metrics:
                summary[f"{stage_type.value}_avg_ms"] = sum(stage_metrics) / len(stage_metrics)

                summary[f"{stage_type.value}_max_ms"] = max(stage_metrics)

                summary[f"{stage_type.value}_min_ms"] = min(stage_metrics)

        return summary

    def clear(self) -> None:
        """Clear all collected metrics."""
        self._metrics.clear()
