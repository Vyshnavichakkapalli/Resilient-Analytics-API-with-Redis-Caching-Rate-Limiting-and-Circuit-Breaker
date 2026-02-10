from typing import List, Dict, Any

# Simple in-memory storage for metrics
metrics_db: List[Dict[str, Any]] = []

def add_metric(metric: Dict[str, Any]):
    metrics_db.append(metric)

def get_all_metrics() -> List[Dict[str, Any]]:
    return metrics_db
