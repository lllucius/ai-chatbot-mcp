"Utility functions for performance operations."

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
    "RequestMetric class for specialized functionality."

    path: str
    method: str
    status_code: int
    duration: float
    timestamp: float
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None


@dataclass
class SystemMetrics:
    "SystemMetrics class for specialized functionality."

    cpu_percent: float
    memory_percent: float
    memory_used_gb: float
    memory_available_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_free_gb: float
    timestamp: float


class PerformanceMonitor:
    "PerformanceMonitor class for specialized functionality."

    def __init__(self, history_size: int = 100):
        "Initialize class instance."
        self.history_size = history_size
        self.metrics_history: Dict[(str, deque)] = defaultdict(
            (lambda: deque(maxlen=history_size))
        )
        self.request_metrics: List[RequestMetric] = []
        self.request_counts: Dict[(str, int)] = defaultdict(int)
        self.error_counts: Dict[(str, int)] = defaultdict(int)
        self.error_requests: List[RequestMetric] = []
        self.slow_requests: List[RequestMetric] = []
        self.system_metrics: List[SystemMetrics] = []
        self.document_processing_metrics: Dict[(str, Any)] = defaultdict(
            (lambda: {"count": 0, "total_time": 0, "errors": 0})
        )
        self.embedding_metrics: Dict[(str, Any)] = defaultdict(
            (lambda: {"count": 0, "total_time": 0, "tokens": 0})
        )
        self.start_time = time.time()
        logger.info("Enhanced performance monitor initialized")

    def record_request(self, metric: RequestMetric) -> None:
        "Record Request operation."
        self.request_metrics.append(metric)
        endpoint_key = f"{metric.method} {metric.path}"
        self.request_counts[endpoint_key] += 1
        if metric.status_code >= 400:
            self.error_counts[endpoint_key] += 1
            self.error_requests.append(metric)
        if metric.duration > 1.0:
            self.slow_requests.append(metric)

    def record_system_metrics(self) -> None:
        "Record System Metrics operation."
        try:
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")
            metric = SystemMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_gb=(memory.used / (1024**3)),
                memory_available_gb=(memory.available / (1024**3)),
                disk_percent=((disk.used / disk.total) * 100),
                disk_used_gb=(disk.used / (1024**3)),
                disk_free_gb=(disk.free / (1024**3)),
                timestamp=time.time(),
            )
            self.system_metrics.append(metric)
        except Exception as e:
            logger.error(f"Failed to record system metrics: {e}")

    def get_request_stats(self, minutes: int = 60) -> Dict[(str, Any)]:
        "Get request stats data."
        cutoff_time = time.time() - (minutes * 60)
        recent_requests = [
            metric
            for metric in self.request_metrics
            if (metric.timestamp >= cutoff_time)
        ]
        if not recent_requests:
            return {
                "total_requests": 0,
                "error_rate": 0.0,
                "avg_duration": 0.0,
                "slowest_duration": 0.0,
                "requests_per_minute": 0.0,
            }
        total_requests = len(recent_requests)
        error_requests = sum((1 for r in recent_requests if (r.status_code >= 400)))
        error_rate = (error_requests / total_requests) if (total_requests > 0) else 0
        durations = [r.duration for r in recent_requests]
        avg_duration = sum(durations) / len(durations)
        slowest_duration = max(durations)
        requests_per_minute = (total_requests / minutes) if (minutes > 0) else 0
        return {
            "total_requests": total_requests,
            "error_requests": error_requests,
            "error_rate": error_rate,
            "avg_duration": avg_duration,
            "slowest_duration": slowest_duration,
            "requests_per_minute": requests_per_minute,
        }

    def get_endpoint_stats(self, limit: int = 10) -> List[Dict[(str, Any)]]:
        "Get endpoint stats data."
        sorted_endpoints = sorted(
            self.request_counts.items(), key=(lambda x: x[1]), reverse=True
        )[:limit]
        endpoint_stats = []
        for endpoint, count in sorted_endpoints:
            errors = self.error_counts.get(endpoint, 0)
            error_rate = (errors / count) if (count > 0) else 0
            endpoint_stats.append(
                {
                    "endpoint": endpoint,
                    "requests": count,
                    "errors": errors,
                    "error_rate": error_rate,
                }
            )
        return endpoint_stats

    def get_system_stats(self) -> Dict[(str, Any)]:
        "Get system stats data."
        if not self.system_metrics:
            return {}
        latest = self.system_metrics[(-1)]
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

    def get_health_summary(self) -> Dict[(str, Any)]:
        "Get health summary data."
        request_stats = self.get_request_stats(60)
        system_stats = self.get_system_stats()
        health_issues = []
        if request_stats.get("error_rate", 0) > 0.1:
            health_issues.append("High error rate")
        if request_stats.get("avg_duration", 0) > 2.0:
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


performance_monitor = PerformanceMonitor()


async def start_system_monitoring():
    "Start System Monitoring operation."

    async def monitoring_loop():
        "Monitoring Loop operation."
        while True:
            try:
                (await asyncio.sleep(60))
                performance_monitor.record_system_metrics()
                if (int(time.time()) % 1800) == 0:
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
    "Record Request Metric operation."
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


def get_performance_stats() -> Dict[(str, Any)]:
    "Get performance stats data."
    return {
        "health_summary": performance_monitor.get_health_summary(),
        "request_stats": performance_monitor.get_request_stats(),
        "endpoint_stats": performance_monitor.get_endpoint_stats(),
        "system_stats": performance_monitor.get_system_stats(),
    }
