"""
Task Complexity Calculator
Tính độ phức tạp và suggested_team_size dựa trên:
- Priority, venue tier, dependencies, duration
"""

import random
from typing import Dict, Any
from services.venue_classifier import VenueTier, get_tier_multiplier


def calculate_task_complexity(
    task: Dict[str, Any],
    venue_tier: VenueTier,
    event_type: str = "",
    dependencies: list = None
) -> str:
    """
    Tính độ phức tạp của task: low, medium, high, critical
    
    Args:
        task: Task dict với priority, duration_days, name, etc.
        venue_tier: Venue tier
        event_type: Event type
        dependencies: List dependency task_ids
        
    Returns:
        "low" | "medium" | "high" | "critical"
    """
    priority = task.get("priority", "medium")
    duration = task.get("duration_days", 1)
    dep_count = len(dependencies or [])
    task_name = task.get("name", "").lower()
    
    # Base complexity từ priority
    priority_weights = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1
    }
    base_score = priority_weights.get(priority, 2)
    
    # Venue tier multiplier
    tier_multiplier = get_tier_multiplier(venue_tier)
    base_score *= tier_multiplier
    
    # Duration multiplier (tasks dài hơn = phức tạp hơn)
    if duration >= 7:
        duration_multiplier = 1.5
    elif duration >= 4:
        duration_multiplier = 1.2
    else:
        duration_multiplier = 1.0
    base_score *= duration_multiplier
    
    # Dependency multiplier (nhiều dependencies = phức tạp hơn)
    if dep_count >= 3:
        dep_multiplier = 1.3
    elif dep_count >= 2:
        dep_multiplier = 1.15
    else:
        dep_multiplier = 1.0
    base_score *= dep_multiplier
    
    # Event-type specific keywords
    if event_type == "concert_opening":
        if any(kw in task_name for kw in ["âm thanh", "sound", "nghệ sĩ", "artist"]):
            base_score *= 1.2
    elif event_type == "conference":
        if any(kw in task_name for kw in ["diễn giả", "speaker", "livestream", "streaming"]):
            base_score *= 1.2
    elif event_type == "career_fair":
        if any(kw in task_name for kw in ["nhà tuyển dụng", "recruiter", "gian hàng", "booth"]):
            base_score *= 1.2
    
    # Classify
    if base_score >= 5.0:
        return "critical"
    elif base_score >= 3.5:
        return "high"
    elif base_score >= 2.0:
        return "medium"
    else:
        return "low"


def calculate_suggested_team_size(
    complexity: str,
    duration_days: int = 1,
    venue_tier: VenueTier = None,
    has_critical_dependencies: bool = False,
    department: str = None
) -> int:
    """
    Tính suggested_team_size dựa trên complexity và department
    
    Args:
        complexity: "low" | "medium" | "high" | "critical"
        duration_days: Số ngày thực hiện
        venue_tier: Venue tier
        has_critical_dependencies: Có dependencies trên critical path không
        department: Tên department (để kiểm tra ban tài chính)
        
    Returns:
        int: Team size (1-6, tùy department)
    """
    # Đặc biệt cho ban tài chính/kế toán: 3-6 người
    if department:
        dept_lower = department.lower()
        if any(kw in dept_lower for kw in ["tài chính", "tai chinh", "finance", "kế toán", "ke toan", "accounting"]):
            # Ban tài chính: 3-6 người, random
            return random.randint(3, 6)
    
    # Base team size từ complexity
    # Low: 1 người
    # Medium: 2-3 người (random)
    # High: 4-5 người (random)
    # Critical: 4-5 người (random)
    if complexity == "low":
        team_size = 1
    elif complexity == "medium":
        team_size = random.randint(2, 3)
    elif complexity == "high":
        team_size = random.randint(4, 5)
    elif complexity == "critical":
        team_size = random.randint(4, 5)
    else:
        team_size = 2  # Default
    
    # Venue tier adjustment (chỉ điều chỉnh nhẹ, không thay đổi quá nhiều)
    if venue_tier:
        tier_multiplier = get_tier_multiplier(venue_tier)
        if tier_multiplier >= 1.3:  # XL venue - có thể cần thêm 1 người
            if complexity in ["medium", "high", "critical"]:
                team_size = min(5, team_size + 1)
        elif tier_multiplier <= 0.8:  # S venue - có thể giảm 1 người
            if complexity in ["medium", "high"]:
                team_size = max(1, team_size - 1)
    
    # Duration adjustment (tasks dài cần nhiều người hơn)
    if duration_days >= 7 and complexity in ["medium", "high", "critical"]:
        team_size = min(5, team_size + 1)
    elif duration_days <= 1 and complexity == "medium":
        team_size = max(2, team_size - 1)
    
    # Critical dependencies adjustment
    if has_critical_dependencies and complexity in ["medium", "high"]:
        team_size = min(5, team_size + 1)
    
    # Đảm bảo trong khoảng hợp lý
    if complexity == "low":
        return 1
    elif complexity == "medium":
        return max(2, min(3, team_size))
    else:  # high, critical
        return max(4, min(5, team_size))


def get_complexity_weight(complexity: str) -> float:
    """
    Trọng số để phân bổ nhân lực
    
    Returns:
        float: Weight (1.0 - 5.0)
    """
    weights = {
        "critical": 5.0,
        "high": 3.5,
        "medium": 2.0,
        "low": 1.0
    }
    return weights.get(complexity, 2.0)




