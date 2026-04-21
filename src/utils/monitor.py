import time
import psutil
import threading
from typing import Dict, Any
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json
import os

from .logger import get_logger

logger = get_logger()


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.metrics = defaultdict(lambda: defaultdict(list))
        self.lock = threading.Lock()
        self.start_time = time.time()
        
        # 应用指标
        self.app_metrics = {
            "query_count": 0,
            "query_latency": deque(maxlen=100),
            "tool_usage": defaultdict(int),
            "errors": defaultdict(int)
        }
    
    def record_query(self, query: str, latency: float, success: bool = True):
        """记录查询指标"""
        with self.lock:
            self.app_metrics["query_count"] += 1
            self.app_metrics["query_latency"].append(latency)
            
            if not success:
                self.app_metrics["errors"]["query_failed"] += 1
    
    def record_tool_usage(self, tool_name: str, success: bool = True):
        """记录工具使用指标"""
        with self.lock:
            self.app_metrics["tool_usage"][tool_name] += 1
            
            if not success:
                self.app_metrics["errors"]["tool_failed"] += 1
    
    def record_error(self, error_type: str):
        """记录错误"""
        with self.lock:
            self.app_metrics["errors"][error_type] += 1
    
    def record_api_call(self, api_url: str, status_code: int, response_time: float, success: bool = True):
        """记录API调用指标"""
        with self.lock:
            # 简化实现，只记录成功/失败
            if success:
                self.app_metrics["tool_usage"]["api_call_success"] += 1
            else:
                self.app_metrics["errors"]["api_call_failed"] += 1
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.5)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": memory.used / (1024**3),
                "memory_total_gb": memory.total / (1024**3),
                "disk_percent": disk.percent,
                "disk_used_gb": disk.used / (1024**3),
                "disk_total_gb": disk.total / (1024**3),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            return {"error": str(e)}
    
    def get_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        with self.lock:
            # 计算查询延迟统计
            query_latencies = list(self.app_metrics["query_latency"])
            latency_stats = {
                "count": len(query_latencies),
                "avg": sum(query_latencies) / len(query_latencies) if query_latencies else 0,
                "min": min(query_latencies) if query_latencies else 0,
                "max": max(query_latencies) if query_latencies else 0,
            }
            
            # 获取系统指标
            system_metrics = self.get_system_metrics()
            
            summary = {
                "uptime_seconds": time.time() - self.start_time,
                "query_stats": {
                    "total_queries": self.app_metrics["query_count"],
                    "latency_stats": latency_stats,
                },
                "tool_usage": dict(self.app_metrics["tool_usage"]),
                "errors": dict(self.app_metrics["errors"]),
                "system_metrics": system_metrics,
                "timestamp": datetime.now().isoformat()
            }
            
            return summary
    
    def export_metrics(self, filepath: str = "metrics.json") -> Dict[str, Any]:
        """导出指标到文件，返回指标数据"""
        try:
            summary = self.get_summary()
            
            # 构建完整的指标数据
            metrics_data = {
                "summary": summary,
                "app_metrics": dict(self.app_metrics),
                "timestamp": datetime.now().isoformat()
            }
            
            # 将列表类型转换为可序列化的格式
            for key, value in metrics_data["app_metrics"].items():
                if isinstance(value, deque):
                    metrics_data["app_metrics"][key] = list(value)
                elif isinstance(value, defaultdict):
                    metrics_data["app_metrics"][key] = dict(value)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(metrics_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Metrics exported to {filepath}")
            return metrics_data
            
        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            return {"error": str(e)}


class SystemMonitor:
    """系统监控器"""
    
    def __init__(self, metrics_collector: MetricsCollector, interval: int = 60):
        self.metrics_collector = metrics_collector
        self.interval = interval
        self.monitoring = False
        self.monitor_thread = None
    
    def start(self):
        """启动监控"""
        if self.monitoring:
            logger.warning("Monitor is already running")
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"System monitor started with {self.interval}s interval")
    
    def stop(self):
        """停止监控"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("System monitor stopped")
    
    def _monitor_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                # 定期记录系统指标
                system_metrics = self.metrics_collector.get_system_metrics()
                
                # 检查系统健康度
                if system_metrics.get("cpu_percent", 0) > 80:
                    logger.warning(f"High CPU usage: {system_metrics['cpu_percent']}%")
                if system_metrics.get("memory_percent", 0) > 80:
                    logger.warning(f"High memory usage: {system_metrics['memory_percent']}%")
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
            
            time.sleep(self.interval)


# 全局实例
_metrics_collector = None
_system_monitor = None


def get_metrics_collector() -> MetricsCollector:
    """获取全局指标收集器实例"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def get_system_monitor(interval: int = 60) -> SystemMonitor:
    """获取全局系统监控器实例"""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor(get_metrics_collector(), interval)
    return _system_monitor


def start_monitoring(interval: int = 60):
    """启动监控"""
    monitor = get_system_monitor(interval)
    monitor.start()


def stop_monitoring():
    """停止监控"""
    if _system_monitor:
        _system_monitor.stop()


def get_system_summary() -> Dict[str, Any]:
    """获取系统摘要"""
    return get_metrics_collector().get_summary()


def export_metrics(filepath: str = "metrics.json") -> Dict[str, Any]:
    """导出指标"""
    return get_metrics_collector().export_metrics(filepath)
