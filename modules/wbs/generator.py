import json
import os
from datetime import datetime
import pytz
from typing import Dict, Any, List
from .scheduler import calculate_critical_path, check_feasibility


def load_concert_template() -> Dict[str, Any]:
    """Load concert_opening template"""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "concert_opening.json")
    with open(template_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_event_id(event_date: str) -> str:
    """Generate event ID in format EVT-YYYYMMDD-<seq> with defensive parsing"""
    try:
        date_obj = datetime.strptime(event_date, "%Y-%m-%d")
        date_str = date_obj.strftime("%Y%m%d")
    except Exception:
        # Fallback: extract digits or use today's date
        digits = "".join(ch for ch in str(event_date) if ch.isdigit())
        if len(digits) >= 8:
            date_str = digits[:8]
        else:
            date_str = datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y%m%d')
    return f"EVT-{date_str}-001"


def generate_epics(departments: List[str]) -> List[Dict[str, Any]]:
    """Generate epics based on departments"""
    template = load_concert_template()
    epics = []
    
    # Map departments to epic templates
    dept_mapping = {
        "Hậu cần": ["Stage & AV Setup", "Security & Access"],
        "Hau can": ["Stage & AV Setup", "Security & Access"],
        "Logistics": ["Stage & AV Setup", "Security & Access"],
        "Đối ngoại": ["Artist Management"],
        "Doi ngoai": ["Artist Management"],
        "External Relations": ["Artist Management"],
        "Media/Marketing": ["Media & Marketing"],
        "Media": ["Media & Marketing"],
        "Tài chính": ["Finance & Budget"],
        "Tai chinh": ["Finance & Budget"],
        "Finance": ["Finance & Budget"]
    }
    
    epic_counter = 1
    for dept in departments:
        if dept in dept_mapping:
            for epic_name in dept_mapping[dept]:
                epics.append({
                    "epic_id": f"EP-{epic_counter:03d}",
                    "name": epic_name,
                    "department": dept,
                    "description": f"Epic for {epic_name} - {dept}"
                })
                epic_counter += 1
    
    return epics


def generate_tasks(epics: List[Dict[str, Any]], headcount_total: int, event_date: str) -> List[Dict[str, Any]]:
    """Generate tasks based on template and assign to epics"""
    template = load_concert_template()
    tasks = []
    
    # Create epic mapping
    epic_mapping = {}
    for epic in epics:
        if "Stage" in epic["name"]:
            epic_mapping["EP-001"] = epic["epic_id"]
        elif "Artist" in epic["name"]:
            epic_mapping["EP-002"] = epic["epic_id"]
        elif "Media" in epic["name"]:
            epic_mapping["EP-003"] = epic["epic_id"]
        elif "Security" in epic["name"]:
            epic_mapping["EP-004"] = epic["epic_id"]
        elif "Finance" in epic["name"]:
            epic_mapping["EP-005"] = epic["epic_id"]
    
    # Calculate deadline dates based on event_date
    from datetime import datetime, timedelta
    event_dt = datetime.strptime(event_date, "%Y-%m-%d")
    
    task_counter = 1
    for template_task in template["tasks"]:
        # Map epic_id
        epic_id = epic_mapping.get(template_task["epic_id"])
        if not epic_id and epics:
            epic_id = epics[0]["epic_id"]
        elif not epic_id:
            epic_id = "EP-001"  # Default fallback
        
        # Calculate deadline based on task category and dependencies
        deadline_days_before = _calculate_deadline_days(template_task, template["tasks"])
        deadline_date = (event_dt - timedelta(days=deadline_days_before)).strftime("%Y-%m-%d")
        
        # Determine priority based on task characteristics
        priority = _determine_priority(template_task)
        
        # Resolve dependencies
        depends_on = []
        for dep_id in template_task.get("depends_on", []):
            # Find the corresponding task_id for this dependency
            for i, t in enumerate(template["tasks"], 1):
                if t["task_id"] == dep_id:
                    depends_on.append(f"T-{i:03d}")
                    break
        
        task = {
            "task_id": f"T-{task_counter:03d}",
            "epic_id": epic_id,
            "name": template_task["name"],
            "depends_on": depends_on,
            "can_parallel": template_task.get("can_parallel", True),
            "deadline": deadline_date,
            "priority": priority
        }
        
        tasks.append(task)
        task_counter += 1
    
    return tasks


def _calculate_deadline_days(template_task: Dict[str, Any], all_tasks: List[Dict[str, Any]]) -> int:
    """Calculate how many days before event this task should be completed"""
    category = template_task.get("category", "")
    is_milestone = template_task.get("milestone", False)
    
    # Base deadlines by category
    category_deadlines = {
        "Stage/AV": 1,      # 1 day before event
        "Artist": 7,        # 1 week before event  
        "Media": 3,         # 3 days before event
        "Security": 2,      # 2 days before event
        "Finance": 1,       # 1 day before event
        "Logistics": 1      # 1 day before event
    }
    
    base_days = category_deadlines.get(category, 3)
    
    # Adjust for milestones
    if is_milestone:
        base_days = max(1, base_days - 1)
    
    # Adjust based on dependencies - if task has many dependencies, it needs more time
    dep_count = len(template_task.get("depends_on", []))
    if dep_count > 2:
        base_days += 2
    elif dep_count > 0:
        base_days += 1
    
    return max(1, base_days)


def _determine_priority(template_task: Dict[str, Any]) -> str:
    """Determine task priority based on characteristics"""
    name = template_task.get("name", "").lower()
    category = template_task.get("category", "")
    is_milestone = template_task.get("milestone", False)
    
    # Critical tasks
    if is_milestone or "contract" in name or "final" in name or "soundcheck" in name:
        return "critical"
    
    # High priority tasks
    if category == "Stage/AV" or "setup" in name or "install" in name:
        return "high"
    
    # Medium priority tasks  
    if category in ["Artist", "Media"] or "design" in name or "create" in name:
        return "medium"
    
    # Default to low priority
    return "low"


def generate_milestones(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate milestones from high priority tasks"""
    milestones = []
    
    for task in tasks:
        # Create milestones for critical tasks
        if task.get("priority") == "critical":
            milestones.append({
                "name": task["name"],
                "task_id": task["task_id"],
                "date": task["deadline"],
                "deadline": task["deadline"],
                "description": f"Milestone: {task['name']}"
            })
    
    return milestones


def generate_wbs(event_input: Dict[str, Any]) -> Dict[str, Any]:
    """Main WBS generation function (rules-only legacy)."""
    # Validation disabled; passthrough
    departments = event_input["departments"]
    
    # Generate components
    event_id = generate_event_id(event_input["event_date"])
    epics = generate_epics(departments)
    # Defensive parse for event_date to ensure downstream YYYY-MM-DD
    safe_event_date = event_input.get("event_date", "")
    try:
        # Normalize to YYYY-MM-DD
        safe_event_date = datetime.strptime(safe_event_date, "%Y-%m-%d").strftime("%Y-%m-%d")
    except Exception:
        # Use today's date (Asia/Bangkok) if malformed
        safe_event_date = datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d')
    tasks = generate_tasks(epics, event_input["headcount_total"], safe_event_date)
    milestones = generate_milestones(tasks)
    
    # Calculate critical path
    critical_path = calculate_critical_path(tasks)
    
    # Check feasibility
    feasibility = check_feasibility(tasks, event_input["headcount_total"])
    
    # Generate meta
    bangkok_tz = pytz.timezone('Asia/Bangkok')
    generated_at = datetime.now(bangkok_tz).strftime('%Y-%m-%d')
    
    meta = {
        "event_name": event_input["event_name"],
        "event_type": event_input["event_type"],
        "event_date": safe_event_date,
        "venue": event_input["venue"],
        "headcount_total": event_input["headcount_total"],
        "generated_at": generated_at
    }
    
    # Generate summary
    summary = {
        "epic_count": len(epics),
        "task_count": len(tasks),
        "critical_path_example": critical_path,
        "feasibility": feasibility
    }
    
    return {
        "status": "ok",
        "event_id": event_id,
        "meta": meta,
        "epics": epics,
        "tasks": tasks
    }
