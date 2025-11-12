"""
Priority Classifier - Rule-based + Context-based
Phân loại priority của task dựa trên keywords và context
"""

from typing import Dict, Any, List, Literal, Set
from services.venue_service import VenueTier
from datetime import datetime, timedelta


PriorityLevel = Literal["low", "medium", "high", "critical"]


# Rule-based: Bảng keywords cho từng priority
PRIORITY_KEYWORDS = {
    "critical": {
        "vi": [
            "tổng duyệt", "final", "soundcheck", "kiểm tra cuối", "bàn giao",
            "hợp đồng", "contract", "ký kết", "sign", "giấy phép", "permit",
            "phê duyệt", "approval", "critical", "quan trọng", "bắt buộc"
        ],
        "en": [
            "final", "critical", "contract", "sign", "permit", "approval",
            "handover", "rehearsal", "soundcheck", "mandatory"
        ]
    },
    "high": {
        "vi": [
            "setup", "lắp đặt", "install", "thiết kế", "design", "khảo sát",
            "survey", "test", "kiểm tra", "an toàn", "safety", "backup",
            "quan trọng", "important", "chính", "main"
        ],
        "en": [
            "setup", "install", "design", "survey", "test", "safety",
            "backup", "important", "main", "key"
        ]
    },
    "medium": {
        "vi": [
            "chuẩn bị", "prepare", "liên hệ", "contact", "thu thập", "collect",
            "theo dõi", "track", "monitor", "quảng cáo", "advertising"
        ],
        "en": [
            "prepare", "contact", "collect", "track", "monitor", "advertising"
        ]
    },
    "low": {
        "vi": [
            "hoàn thiện", "finalize", "tổng hợp", "summary", "báo cáo", "report",
            "dọn dẹp", "cleanup", "tùy chọn", "optional"
        ],
        "en": [
            "finalize", "summary", "report", "cleanup", "optional"
        ]
    }
}


def classify_priority_rule_based(
    task: Dict[str, Any],
    all_tasks: List[Dict[str, Any]] = None
) -> PriorityLevel:
    """
    Phân loại priority dựa trên rule-based (keywords)
    
    Args:
        task: Task dictionary với name, description
        all_tasks: Tất cả tasks để check context
        
    Returns:
        Priority level
    """
    name = task.get("name", "").lower()
    description = task.get("description", "").lower()
    text = f"{name} {description}"
    
    # Check từ critical → low (ưu tiên mức cao hơn)
    for priority in ["critical", "high", "medium", "low"]:
        keywords = PRIORITY_KEYWORDS[priority]
        all_keywords = keywords["vi"] + keywords["en"]
        
        if any(kw in text for kw in all_keywords):
            return priority
    
    # Default
    return "medium"


def classify_priority_context_based(
    task: Dict[str, Any],
    event_context: Dict[str, Any],
    dependency_context: Dict[str, Any] = None,
    critical_path_tasks: Set[str] = None
) -> PriorityLevel:
    """
    Phân loại priority dựa trên context
    
    Args:
        task: Task dictionary
        event_context: {venue_tier, event_type, event_date, headcount_total}
        dependency_context: {is_on_critical_path, has_critical_deps, days_until_deadline}
        critical_path_tasks: Set các task_id trên critical path
        
    Returns:
        Priority level
    """
    if critical_path_tasks is None:
        critical_path_tasks = set()
    
    task_id = task.get("task_id", "")
    base_priority = task.get("priority", "medium")
    
    # Điểm số ban đầu
    score = {
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4
    }.get(base_priority, 2)
    
    # +2 điểm nếu trên critical path
    if task_id in critical_path_tasks:
        score += 2
    
    # +1 điểm nếu có dependencies là critical
    if dependency_context:
        if dependency_context.get("has_critical_deps", False):
            score += 1
        if dependency_context.get("is_blocking_many", False):
            score += 1
    
    # Deadline pressure (INCREASED weight)
    if dependency_context:
        days_until_deadline = dependency_context.get("days_until_deadline", 999)
        if days_until_deadline < 3:
            score += 2  # Very urgent: +2 (was +1)
        elif days_until_deadline < 7:
            score += 1  # Urgent: +1
    
    # Failure impact: Task này fail thì ảnh hưởng bao nhiêu tasks khác?
    if dependency_context:
        blocking_count = dependency_context.get("blocking_count", 0)
        if blocking_count >= 5:
            score += 2  # Blocks many tasks
        elif blocking_count >= 3:
            score += 1  # Blocks some tasks
    
    # +1 điểm nếu venue tier lớn (XL, L)
    venue_tier = event_context.get("venue_tier", VenueTier.M)
    if venue_tier in [VenueTier.XL, VenueTier.L]:
        score += 1
    
    # +1 điểm nếu event type quan trọng
    event_type = event_context.get("event_type", "")
    important_event_types = ["concert_opening", "conference"]
    if event_type in important_event_types:
        score += 1
    
    # Chuyển score thành priority (with adjusted thresholds)
    if score >= 7:  # Increased threshold (was 6)
        return "critical"
    elif score >= 4:
        return "high"
    elif score >= 2:
        return "medium"
    else:
        return "low"


def classify_priority_hybrid(
    task: Dict[str, Any],
    event_context: Dict[str, Any],
    all_tasks: List[Dict[str, Any]] = None,
    dependency_context: Dict[str, Any] = None,
    critical_path_tasks: Set[str] = None
) -> PriorityLevel:
    """
    Kết hợp rule-based và context-based
    
    Args:
        task: Task dictionary
        event_context: Event context
        all_tasks: Tất cả tasks
        dependency_context: Dependency context
        critical_path_tasks: Critical path tasks
        
    Returns:
        Priority level (ưu tiên mức cao hơn giữa rule và context)
    """
    # Rule-based
    rule_priority = classify_priority_rule_based(task, all_tasks)
    
    # Context-based
    context_priority = classify_priority_context_based(
        task, event_context, dependency_context, critical_path_tasks
    )
    
    # Ưu tiên mức cao hơn
    priority_order = ["low", "medium", "high", "critical"]
    rule_idx = priority_order.index(rule_priority)
    context_idx = priority_order.index(context_priority)
    
    return priority_order[max(rule_idx, context_idx)]


def calculate_priority_score(priority: PriorityLevel) -> int:
    """
    Chuyển priority thành điểm số để tính toán
    
    Returns:
        Score: low=1, medium=2, high=3, critical=4
    """
    return {
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4
    }.get(priority, 2)


def get_priority_weight(priority: PriorityLevel) -> float:
    """
    Trọng số để phân bổ nhân lực
    
    Returns:
        Weight: low=0.5, medium=1.0, high=1.5, critical=2.0
    """
    return {
        "low": 0.5,
        "medium": 1.0,
        "high": 1.5,
        "critical": 2.0
    }.get(priority, 1.0)



