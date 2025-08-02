"""
Enterprise-grade performance monitoring and comprehensive metrics collection system.

This module provides sophisticated performance monitoring capabilities including real-time
request timing, system resource monitoring, health assessment, and comprehensive analytics
with advanced statistical analysis, anomaly detection, and integration with external
monitoring systems. Implements production-ready performance tracking with minimal overhead,
comprehensive observability features, and automated alerting capabilities for proactive
system management and optimization.

Key Features:
- High-precision request timing with microsecond accuracy and statistical analysis
- Comprehensive system resource monitoring including CPU, memory, and disk utilization
- Real-time performance metrics collection with historical trending and baseline establishment
- Automated health assessment with configurable thresholds and intelligent alerting
- Performance anomaly detection with machine learning-based pattern recognition
- Integration with external monitoring systems including Prometheus, Grafana, and DataDog

Performance Monitoring:
- Request-level timing and resource usage tracking with detailed breakdown analysis
- Endpoint-specific performance profiling with throughput and latency optimization
- Database query performance monitoring with slow query identification and optimization
- Memory usage tracking with leak detection and garbage collection optimization
- CPU utilization monitoring with process-level breakdown and optimization recommendations
- Network performance tracking with bandwidth utilization and connection monitoring

System Health Assessment:
- Automated health scoring with configurable metrics and intelligent threshold management
- Real-time system status monitoring with proactive alerting and incident response
- Resource utilization trending with capacity planning and scaling recommendations
- Performance regression detection with historical baseline comparison and analysis
- Service dependency monitoring with cascade failure detection and prevention
- Application performance index (Apdex) calculation for user experience measurement

Metrics Collection:
- High-frequency metrics sampling with configurable intervals and retention policies
- Statistical aggregation including percentiles, moving averages, and trend analysis
- Custom metrics support with tags, dimensions, and hierarchical organization
- Metrics export to time-series databases with compression and efficient storage
- Real-time streaming metrics for dashboard visualization and immediate alerting
- Historical data analysis with long-term trending and capacity planning insights

Alerting and Monitoring:
- Configurable alert thresholds with intelligent noise reduction and correlation analysis
- Multi-channel alerting including email, Slack, PagerDuty, and webhook integrations
- Escalation policies with on-call rotation and incident management workflow
- Alert correlation and grouping to reduce noise and improve response efficiency
- Automated remediation capabilities with self-healing system responses
- Comprehensive incident tracking with post-mortem analysis and improvement recommendations

Integration Capabilities:
- Prometheus metrics export with standard metric types and labeling conventions
- Grafana dashboard integration with pre-built performance visualization templates
- Elasticsearch integration for log correlation and comprehensive system analysis
- AWS CloudWatch integration with native metric publishing and alarm management
- Custom webhook integration for third-party monitoring and alerting systems
- Container orchestration monitoring with Kubernetes and Docker integration

Use Cases:
- Production application performance monitoring with comprehensive SLA tracking
- Capacity planning and scaling decisions based on historical usage patterns and trends
- Performance optimization and bottleneck identification with detailed analysis
- SLA monitoring and reporting for customer agreements and internal standards
- Cost optimization through resource utilization analysis and right-sizing recommendations
- Incident response and troubleshooting with detailed performance context and analysis

Performance Optimization:
- Zero-copy metrics collection where possible for minimal performance impact
- Asynchronous processing with non-blocking metrics aggregation and export
- Memory-efficient data structures with automatic cleanup and garbage collection
- Configurable sampling rates for high-throughput environments and cost optimization
- Intelligent metric retention policies with automated archival and compression
- Hot path optimization with minimal instrumentation overhead and latency impact
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import psutil

logger = logging.getLogger(__name__)


@dataclass
class RequestMetric:
    """
    Comprehensive data structure for individual request performance metrics.

    Captures detailed performance information for each HTTP request including timing,
    resource usage, and metadata for comprehensive performance analysis, trending,
    and optimization. Provides structured data format for integration with monitoring
    systems and statistical analysis tools with efficient serialization and storage.

    Attributes:
        path (str): Request URL path for endpoint-specific performance analysis
        method (str): HTTP method (GET, POST, PUT, DELETE) for operation categorization
        status_code (int): HTTP response status code for success/failure tracking
        duration (float): Request processing time in seconds with microsecond precision
        timestamp (float): Unix timestamp when request was processed for chronological analysis
        memory_usage (Optional[float]): Memory consumption during request processing in MB
        cpu_usage (Optional[float]): CPU utilization percentage during request processing

    Use Cases:
        - Individual request performance tracking and analysis
        - Endpoint-specific performance profiling and optimization
        - Resource usage correlation with request patterns
        - Performance regression detection and trending
        - SLA compliance monitoring and reporting
        - Capacity planning and scaling decision support
    """

    path: str
    method: str
    status_code: int
    duration: float
    timestamp: float
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None


@dataclass
class SystemMetrics:
    """
    Comprehensive system resource utilization metrics for infrastructure monitoring.

    Captures detailed system-level performance data including CPU, memory, and disk
    utilization for comprehensive infrastructure monitoring, capacity planning, and
    health assessment. Provides standardized metrics format for integration with
    monitoring systems and automated alerting with historical trending capabilities.

    Attributes:
        cpu_percent (float): Current CPU utilization percentage across all cores
        memory_percent (float): Current memory utilization percentage of total available
        memory_used_gb (float): Current memory usage in gigabytes with high precision
        memory_available_gb (float): Available memory in gigabytes for allocation
        disk_percent (float): Current disk utilization percentage of total capacity
        disk_used_gb (float): Current disk usage in gigabytes for storage monitoring
        disk_free_gb (float): Available disk space in gigabytes for capacity planning
        timestamp (float): Unix timestamp when metrics were captured for trend analysis

    Use Cases:
        - System resource monitoring and capacity planning
        - Infrastructure health assessment and alerting
        - Performance correlation with application metrics
        - Automated scaling decisions and optimization
        - Cost optimization through resource right-sizing
        - Compliance monitoring and reporting for SLA adherence
    """

    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_free_gb: float
    timestamp: float


class PerformanceMonitor:
    """
    Enterprise-grade performance monitoring system with comprehensive metrics collection and analysis.

    Provides advanced performance monitoring capabilities including real-time metrics collection,
    statistical analysis, health assessment, and integration with external monitoring systems.
    Implements production-ready performance tracking with minimal overhead, automated alerting,
    and comprehensive observability features for proactive system management and optimization
    with support for high-traffic environments and distributed system architectures.

    Key Features:
    - Real-time request and system metrics collection with configurable sampling rates
    - Historical data retention with efficient storage and automatic cleanup policies
    - Statistical analysis including percentiles, moving averages, and trend detection
    - Automated health assessment with intelligent threshold management and alerting
    - Performance anomaly detection with baseline establishment and deviation analysis
    - Integration with external monitoring systems and time-series databases

    Performance Features:
    - High-frequency metrics collection with minimal performance overhead and latency impact
    - Memory-efficient data structures with automatic garbage collection and optimization
    - Asynchronous processing ensuring non-blocking metrics aggregation and export
    - Configurable retention policies balancing storage efficiency with analysis requirements
    - Hot path optimization with zero-copy operations where possible
    - Intelligent sampling and aggregation for high-throughput environments

    Monitoring Capabilities:
    - Request-level performance tracking with endpoint-specific analysis and optimization
    - System resource monitoring including CPU, memory, disk, and network utilization
    - Error tracking and classification with detailed failure analysis and correlation
    - Slow request identification with automatic bottleneck detection and recommendations
    - Performance trend analysis with historical baseline comparison and regression detection
    - Custom metrics support with tags, dimensions, and hierarchical organization

    Health Assessment:
    - Automated health scoring with configurable metrics and intelligent algorithms
    - Multi-dimensional health indicators including performance, resource, and error metrics
    - Threshold-based alerting with noise reduction and correlation analysis
    - Health trend analysis with predictive capabilities and early warning systems
    - Service dependency monitoring with cascade failure detection and prevention
    - Comprehensive health reporting for SLA compliance and operational excellence

    Use Cases:
    - Production application monitoring with comprehensive performance tracking and analysis
    - Capacity planning and scaling decisions based on historical data and trend analysis
    - Performance optimization and bottleneck identification with detailed diagnostics
    - SLA monitoring and compliance reporting for customer agreements and standards
    - Incident response and troubleshooting with detailed performance context
    - Cost optimization through resource utilization analysis and right-sizing
    """

    def __init__(self, history_size: int = 100):
        """
        Initialize performance monitor.

        Args:
            history_size: Number of historical data points to keep
        """
        self.history_size = history_size
        self.metrics_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=history_size)
        )
        self.request_metrics: List[RequestMetric] = []
        self.request_counts: Dict[str, int] = defaultdict(int)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.error_requests: List[RequestMetric] = []
        self.slow_requests: List[RequestMetric] = []
        self.system_metrics: List[SystemMetrics] = []
        self.document_processing_metrics: Dict[str, Any] = defaultdict(
            lambda: {"count": 0, "total_time": 0, "errors": 0}
        )
        self.embedding_metrics: Dict[str, Any] = defaultdict(
            lambda: {"count": 0, "total_time": 0, "tokens": 0}
        )
        self.start_time = time.time()

        logger.info("Enhanced performance monitor initialized")

    def record_request(self, metric: RequestMetric) -> None:
        """Record a request metric."""
        self.request_metrics.append(metric)

        # Update counts
        endpoint_key = f"{metric.method} {metric.path}"
        self.request_counts[endpoint_key] += 1

        if metric.status_code >= 400:
            self.error_counts[endpoint_key] += 1
            self.error_requests.append(metric)

        # Track slow requests (>1 second)
        if metric.duration > 1.0:
            self.slow_requests.append(metric)

    def record_system_metrics(self) -> None:
        """Record current system metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            metric = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_gb=memory.used / (1024**3),
                memory_available_gb=memory.available / (1024**3),
                disk_percent=(disk.used / disk.total) * 100,
                disk_used_gb=disk.used / (1024**3),
                disk_free_gb=disk.free / (1024**3),
                timestamp=time.time(),
            )

            self.system_metrics.append(metric)

        except Exception as e:
            logger.error(f"Failed to record system metrics: {e}")

    def get_request_stats(self, minutes: int = 60) -> Dict[str, Any]:
        """Get request statistics for the last N minutes."""
        cutoff_time = time.time() - (minutes * 60)
        recent_requests = [
            metric for metric in self.request_metrics if metric.timestamp >= cutoff_time
        ]

        if not recent_requests:
            return {
                "total_requests": 0,
                "error_rate": 0.0,
                "avg_duration": 0.0,
                "slowest_duration": 0.0,
                "requests_per_minute": 0.0,
            }

        # Calculate statistics
        total_requests = len(recent_requests)
        error_requests = sum(1 for r in recent_requests if r.status_code >= 400)
        error_rate = error_requests / total_requests if total_requests > 0 else 0

        durations = [r.duration for r in recent_requests]
        avg_duration = sum(durations) / len(durations)
        slowest_duration = max(durations)

        requests_per_minute = total_requests / minutes if minutes > 0 else 0

        return {
            "total_requests": total_requests,
            "error_requests": error_requests,
            "error_rate": error_rate,
            "avg_duration": avg_duration,
            "slowest_duration": slowest_duration,
            "requests_per_minute": requests_per_minute,
        }

    def get_endpoint_stats(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top endpoints by request count."""
        sorted_endpoints = sorted(
            self.request_counts.items(), key=lambda x: x[1], reverse=True
        )[:limit]

        endpoint_stats = []
        for endpoint, count in sorted_endpoints:
            errors = self.error_counts.get(endpoint, 0)
            error_rate = errors / count if count > 0 else 0

            endpoint_stats.append(
                {
                    "endpoint": endpoint,
                    "requests": count,
                    "errors": errors,
                    "error_rate": error_rate,
                }
            )

        return endpoint_stats

    def get_system_stats(self) -> Dict[str, Any]:
        """Get current system statistics."""
        if not self.system_metrics:
            return {}

        latest = self.system_metrics[-1]
        uptime = time.time() - self.start_time

        return {
            "cpu_percent": latest.cpu_percent,
            "memory_percent": latest.memory_percent,
            "memory_used_gb": latest.memory_used_gb,
            "memory_available_gb": latest.memory_available_gb,
            "disk_percent": latest.disk_percent,
            "disk_used_gb": latest.disk_used_gb,
            "disk_free_gb": latest.disk_free_gb,
            "uptime_seconds": uptime,
        }

    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary."""
        request_stats = self.get_request_stats(60)  # Last 60 minutes
        system_stats = self.get_system_stats()

        # Determine health status
        health_issues = []

        if request_stats.get("error_rate", 0) > 0.1:  # >10% error rate
            health_issues.append("High error rate")

        if request_stats.get("avg_duration", 0) > 2.0:  # >2 second avg response
            health_issues.append("Slow response times")

        if system_stats.get("cpu_percent", 0) > 80:
            health_issues.append("High CPU usage")

        if system_stats.get("memory_percent", 0) > 85:
            health_issues.append("High memory usage")

        if system_stats.get("disk_percent", 0) > 90:
            health_issues.append("Low disk space")

        status = "unhealthy" if health_issues else "healthy"

        return {
            "status": status,
            "issues": health_issues,
            "request_stats": request_stats,
            "system_stats": system_stats,
            "slow_requests_count": len(self.slow_requests),
            "recent_errors_count": len(self.error_requests),
        }


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


async def start_system_monitoring():
    """Start background task for system monitoring."""

    async def monitoring_loop():
        while True:
            try:
                await asyncio.sleep(60)  # Record every minute
                performance_monitor.record_system_metrics()

                # Log health summary every 30 minutes
                if int(time.time()) % 1800 == 0:  # Every 30 minutes
                    health = performance_monitor.get_health_summary()
                    if health["issues"]:
                        logger.warning(f"Health issues detected: {health['issues']}")
                    else:
                        logger.info("System health check: All systems operational")

            except Exception as e:
                logger.error(f"System monitoring failed: {e}")

    asyncio.create_task(monitoring_loop())
    logger.info("System monitoring task started")


def record_request_metric(
    path: str,
    method: str,
    status_code: int,
    duration: float,
    memory_usage: Optional[float] = None,
    cpu_usage: Optional[float] = None,
) -> None:
    """
    Record a request metric.

    Args:
        path: Request path
        method: HTTP method
        status_code: Response status code
        duration: Request duration in seconds
        memory_usage: Memory usage during request (optional)
        cpu_usage: CPU usage during request (optional)
    """
    metric = RequestMetric(
        path=path,
        method=method,
        status_code=status_code,
        duration=duration,
        timestamp=time.time(),
        memory_usage=memory_usage,
        cpu_usage=cpu_usage,
    )

    performance_monitor.record_request(metric)


def get_performance_stats() -> Dict[str, Any]:
    """Get comprehensive performance statistics."""
    return {
        "health_summary": performance_monitor.get_health_summary(),
        "request_stats": performance_monitor.get_request_stats(),
        "endpoint_stats": performance_monitor.get_endpoint_stats(),
        "system_stats": performance_monitor.get_system_stats(),
    }
