from typing import Dict, Any, List, Optional
from datetime import datetime
import pytz
import os

from venue_classifier import classify_venue, VenueTier
from task_generator_v2 import generate_tasks
from risk_generator import generate_risks_by_department, generate_overall_risks

# Optional LLM enhancement
try:
    from llm_generator_v2 import enhance_wbs_with_llm, generate_smart_suggestions
    HAS_LLM = True
except ImportError:
    HAS_LLM = False

USE_LLM_ENHANCEMENT = os.getenv("USE_LLM", "0") in ("1", "true", "True")


def generate_epic_from_department(department: str, epic_id: str) -> Dict[str, Any]:
    """
    Generate epic with standardized title and description based on department
    """
    
    # Mapping department to epic details
    epic_mapping = {
        "hậu cần": {
            "name": "Điều phối vận hành & hậu cần",
            "description": "Quản lý hạ tầng, vật tư, vận chuyển, an ninh hiện trường, phối hợp nhà cung cấp"
        },
        "logistics": {
            "name": "Điều phối vận hành & hậu cần",
            "description": "Quản lý hạ tầng, vật tư, vận chuyển, an ninh hiện trường, phối hợp nhà cung cấp"
        },
        "marketing": {
            "name": "Triển khai truyền thông & marketing",
            "description": "Key Visual, ấn phẩm, kế hoạch truyền thông đa kênh, triển khai social và quảng cáo"
        },
        "media": {
            "name": "Triển khai truyền thông & marketing",
            "description": "Key Visual, ấn phẩm, kế hoạch truyền thông đa kênh, triển khai social và quảng cáo"
        },
        "đối ngoại": {
            "name": "Làm việc với nghệ sĩ & đối tác",
            "description": "Liên hệ, đàm phán, hợp đồng nghệ sĩ/đối tác, quản lý rider và lịch trình"
        },
        "tài chính": {
            "name": "Quản lý tài chính sự kiện",
            "description": "Ngân sách, hợp đồng mua sắm/dịch vụ, thanh toán, quyết toán, kiểm soát chi phí"
        },
        "finance": {
            "name": "Quản lý tài chính sự kiện",
            "description": "Ngân sách, hợp đồng mua sắm/dịch vụ, thanh toán, quyết toán, kiểm soát chi phí"
        },
        "chuyên môn": {
            "name": "Quản lý chuyên môn & kỹ thuật",
            "description": "Hệ thống IT, âm thanh, ánh sáng, streaming, technical support"
        },
        "technical": {
            "name": "Quản lý chuyên môn & kỹ thuật",
            "description": "Hệ thống IT, âm thanh, ánh sáng, streaming, technical support"
        },
    }
    
    dept_lower = department.lower().strip()
    
    # Get epic details or use default
    epic_details = epic_mapping.get(
        dept_lower,
        {
            "name": f"Điều phối {department}",
            "description": f"Quản lý và điều phối công việc cho ban {department}"
        }
    )
    
    return {
        "epic_id": epic_id,
        "name": epic_details["name"],
        "department": department,
        "description": epic_details["description"],
        "start-date": "",  # Will be calculated from tasks
        "end-date": "",    # Will be calculated from tasks
    }


def normalize_department(dept: str) -> str:
    """Normalize department name to standard bucket"""
    dept_lower = dept.lower().strip()
    
    if any(k in dept_lower for k in ["hậu cần", "hau can", "logistics", "vận hành"]):
        return "hậu cần"
    if any(k in dept_lower for k in ["media", "marketing", "truyền thông", "truyen thong"]):
        return "marketing"
    if any(k in dept_lower for k in ["chuyên môn", "chuyen mon", "technical", "it", "kỹ thuật"]):
        return "chuyên môn"
    if any(k in dept_lower for k in ["tài chính", "tai chinh", "finance"]):
        return "tài chính"
    
    return dept  # Return original if can't normalize


def run_pipeline(event_input: Dict[str, Any], retrieved_docs: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Main WBS generation pipeline
    
    Args:
        event_input: Dict containing event details
        retrieved_docs: Optional retrieved documents for LLM context
        
    Returns:
        Dict with extracted_info, epics_task, tasks, departments structure
    """
    
    # Extract input data
    event_name = event_input.get("event_name", "")
    event_type = event_input.get("event_type", "")
    event_date = event_input.get("event_date", "")
    venue = event_input.get("venue", "")
    headcount_total = int(event_input.get("headcount_total", 0))
    departments = event_input.get("departments", [])
    
    # Validate event_date format
    try:
        datetime.strptime(event_date, "%Y-%m-%d")
    except:
        # Use today's date if invalid
        event_date = datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d')
    
    # Classify venue tier
    venue_tier = classify_venue(venue)
    
    # Generate epics (one per department)
    epics = []
    for idx, dept in enumerate(departments, start=1):
        epic = generate_epic_from_department(dept, f"EP-{idx:03d}")
        epics.append(epic)
    
    # Generate tasks (NO DUPLICATION, synced with action templates)
    tasks = generate_tasks(epics, event_date, venue_tier, headcount_total)
    
    # Optional: LLM enhancement for intelligent suggestions
    llm_suggestions = None
    smart_tips = None
    if USE_LLM_ENHANCEMENT and HAS_LLM and retrieved_docs:
        try:
            llm_suggestions = enhance_wbs_with_llm(
                {**event_input, "venue_tier": venue_tier},
                epics,
                tasks,
                retrieved_docs
            )
            smart_tips = generate_smart_suggestions(
                {**event_input, "venue_tier": venue_tier},
                retrieved_docs
            )
        except Exception as e:
            print(f"LLM enhancement error: {e}")
    
    # Calculate epic start/end dates from tasks
    for epic in epics:
        epic_tasks = [t for t in tasks if t["epic_id"] == epic["epic_id"]]
        if epic_tasks:
            start_dates = [t["start-date"] for t in epic_tasks if t.get("start-date")]
            end_dates = [t["deadline"] for t in epic_tasks if t.get("deadline")]
            epic["start-date"] = min(start_dates) if start_dates else ""
            epic["end-date"] = max(end_dates) if end_dates else ""
    
    # Group tasks by department for department output
    departments_output: Dict[str, List[Dict[str, Any]]] = {
        "hậu cần": [],
        "marketing": [],
        "chuyên môn": [],
        "tài chính": [],
    }
    
    epic_dept_map = {e["epic_id"]: normalize_department(e["department"]) for e in epics}
    
    for task in tasks:
        dept_bucket = epic_dept_map.get(task["epic_id"], "hậu cần")
        
        dept_task = {
            "task_id": task["task_id"],
            "name": task["name"],
            "start_date": task["start-date"],
            "deadline": task["deadline"],
            "depends_on": task.get("depends_on", []),
            "complexity": task.get("complexity", "medium"),
        }
        
        departments_output[dept_bucket].append(dept_task)
    
    # Generate risks (by department + overall, scaled by venue tier)
    dept_risks = generate_risks_by_department(departments, venue_tier, event_type)
    overall_risks = generate_overall_risks(venue_tier, event_type)
    
    # Build risks structure
    risks = {
        "by_department": dept_risks,
        "overall": overall_risks,
    }
    
    # Build final output
    output = {
        "extracted_info": {
            "event_name": event_name,
            "event_type": event_type,
            "event_date": event_date,
            "venue": venue,
            "headcount_total": headcount_total,
            "departments": departments,
            "venue_tier": venue_tier,  # Added for debugging
        },
        "epics_task": epics,
        "tasks": tasks,
        "departments": departments_output,
        "risks": risks,  # Added risks output
    }
    
    # Optional: Add LLM suggestions if available
    if llm_suggestions:
        output["llm_suggestions"] = llm_suggestions
    if smart_tips:
        output["smart_tips"] = smart_tips
    
    return output


# Example usage
if __name__ == "__main__":
    test_input = {
        "event_name": "Concert Khai Giảng 2025",
        "event_type": "concert_opening",
        "event_date": "2024-12-25",
        "venue": "đường 30m",
        "headcount_total": 50,
        "departments": ["Hậu cần", "Marketing", "Tài chính"],
    }
    
    result = run_pipeline(test_input)
    
    print("=== EXTRACTED INFO ===")
    print(result["extracted_info"])
    
    print("\n=== EPICS ===")
    for epic in result["epics_task"]:
        print(f"{epic['epic_id']}: {epic['name']} ({epic['department']})")
    
    print(f"\n=== TASKS ({len(result['tasks'])} total) ===")
    for task in result["tasks"][:5]:  # Show first 5
        print(f"{task['task_id']} | {task['name']:40} | {task['priority']:8} | {task['start-date']} -> {task['deadline']}")
    print("...")
    
    print("\n=== DEPARTMENTS ===")
    for dept, tasks in result["departments"].items():
        print(f"{dept}: {len(tasks)} tasks")
    
    print("\n=== RISKS ===")
    print(f"By department: {len(result['risks']['by_department'])} departments")
    print(f"Overall: {len(result['risks']['overall'])} risks")