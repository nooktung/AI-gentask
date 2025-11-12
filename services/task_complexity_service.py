"""
Task Complexity Calculator
Tính độ phức tạp và suggested_team_size dựa trên:
- Priority, venue tier, dependencies, duration
"""

from typing import Dict, Any
from services.venue_service import VenueTier, get_tier_multiplier


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
    
    # Skill requirement: Tasks requiring high skills = more complex
    skill_keywords = {
        "chuyên nghiệp": 1.3,
        "cao cấp": 1.3,
        "đặc biệt": 1.2,
        "professional": 1.3,
        "advanced": 1.3,
        "specialized": 1.2,
        "expert": 1.3,
        "certified": 1.2
    }
    for keyword, multiplier in skill_keywords.items():
        if keyword in task_name:
            base_score *= multiplier
            break
    
    # Resource availability: Tasks requiring rare/expensive resources = more complex
    resource_keywords = {
        "vendor độc quyền": 1.3,
        "exclusive": 1.3,
        "thiết bị hiếm": 1.2,
        "rare equipment": 1.2,
        "custom": 1.2,
        "tùy chỉnh": 1.2
    }
    for keyword, multiplier in resource_keywords.items():
        if keyword in task_name:
            base_score *= multiplier
            break
    
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
    department: str = None,
    headcount_total: int = 50,
    event_context: Dict[str, Any] = None,
    priority: str = "medium"
) -> int:
    """
    Tính suggested_team_size dựa trên complexity, quy mô sự kiện và đặc thù ban.
    """
    base_min_map = {
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4,
    }
    base_min = base_min_map.get(complexity, 2)

    # Headcount scaling (REDUCED multipliers for more realistic team sizes)
    if headcount_total >= 100:
        headcount_multiplier = 2.0  # Reduced from 2.5-3.2
        max_cap = 12
    elif headcount_total >= 50:
        headcount_multiplier = 1.5  # Reduced from 2.0
        max_cap = 10
    elif headcount_total >= 30:
        headcount_multiplier = 1.3
        max_cap = 8
    elif headcount_total >= 20:
        headcount_multiplier = 1.2
        max_cap = 6
    else:
        headcount_multiplier = 1.0
        max_cap = 5

    is_finance = False
    if department:
        dept_lower = department.lower()
        if any(kw in dept_lower for kw in ["tài chính", "tai chinh", "finance", "kế toán", "ke toan", "accounting"]):
            is_finance = True
            base_min = max(base_min, 3)
            max_cap = max(max_cap, 8 if headcount_total >= 150 else 6)

    team_size = base_min * headcount_multiplier

    if venue_tier:
        tier_multiplier = get_tier_multiplier(venue_tier)
        if tier_multiplier >= 1.3:
            team_size *= 1.25
        elif tier_multiplier <= 0.8:
            team_size *= 0.9

    # Duration multiplier
    if duration_days >= 10:
        team_size *= 1.25
    elif duration_days >= 5:
        team_size *= 1.1
    elif duration_days <= 1:
        team_size *= 1.2
    
    # Urgency multiplier: Tasks with < 7 days to deadline need more people (rush jobs)
    if event_context:
        event_date = event_context.get("event_date")
        if event_date:
            try:
                from datetime import datetime
                base_days = {
                    "critical": 8,
                    "high": 10,
                    "medium": 18,
                    "low": 25,
                }
                days_until_event = (datetime.strptime(event_date, "%Y-%m-%d") - datetime.now()).days
                task_deadline_days = days_until_event - (base_days.get(priority, 10) + duration_days)
                if task_deadline_days < 7 and priority in ["critical", "high"]:
                    team_size *= 1.3  # Rush job needs more people
            except:
                pass

    if has_critical_dependencies and complexity in ["medium", "high", "critical"]:
        team_size *= 1.15

    if is_finance:
        team_size = max(team_size, 3)

    team_size = int(round(team_size))
    team_size = max(base_min, team_size)
    team_size = min(max_cap, team_size)
    return team_size


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




