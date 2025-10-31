"""
Pipeline V3 - Hybrid RAG + LLM Task Generation
Combines template reliability with LLM flexibility and RAG context awareness
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import V3 components
from services.rag_engine import SimpleRAGEngine
from services.llm_task_generator import LLMTaskGenerator
from services.task_generator_v3 import (
    calculate_available_workers,
    distribute_workers_to_departments,
    ACTION_TEMPLATES,
    get_tier_multiplier
)
from services.risk_generator import generate_risks_by_department, generate_overall_risks
from venue_classifier import classify_venue, VenueTier
from utils.department_normalizer import normalize_department, normalize_departments, get_department_bucket  # NEW IMPORT

def generate_epic_from_department(department: str, epic_id: str) -> Dict[str, Any]:
    """
    Generate epic with standardized title and description based on department
    Uses centralized department normalizer
    """
    
    # Use centralized normalizer
    normalized_dept = get_department_bucket(department)
    
    # Mapping department to epic details (use normalized names)
    epic_mapping = {
        "hậu cần": {
            "name": "Điều phối vận hành & hậu cần",
            "description": "Quản lý hạ tầng, vật tư, vận chuyển, an ninh hiện trường, phối hợp nhà cung cấp"
        },
        "marketing": {
            "name": "Triển khai truyền thông & marketing",
            "description": "Key Visual, ấn phẩm, kế hoạch truyền thông đa kênh, triển khai social và quảng cáo"
        },
        "chuyên môn": {
            "name": "Quản lý chuyên môn & kỹ thuật",
            "description": "Hệ thống IT, âm thanh, ánh sáng, streaming, technical support"
        },
        "tài chính": {
            "name": "Quản lý tài chính sự kiện",
            "description": "Ngân sách, hợp đồng mua sắm/dịch vụ, thanh toán, quyết toán, kiểm soát chi phí"
        },
        "đối ngoại": {
            "name": "Làm việc với nghệ sĩ & đối tác",
            "description": "Liên hệ, đàm phán, hợp đồng nghệ sĩ/đối tác, quản lý rider và lịch trình"
        },
    }
    
    # Get epic details using normalized department
    epic_details = epic_mapping.get(
        normalized_dept,
        {
            "name": f"Điều phối {department}",
            "description": f"Quản lý và điều phối công việc cho ban {department}"
        }
    )
    
    return {
        "epic_id": epic_id,
        "name": epic_details["name"],
        "department": normalize_department(department),  # Use display name
        "description": epic_details["description"],
        "start-date": "",
        "end-date": "",
    }


def run_pipeline_with_rag(
    event_input: Dict[str, Any],
    use_llm: bool = True,
    llm_mode: str = "enhance"  # "enhance" or "generate"
) -> Dict[str, Any]:
    """
    Main WBS generation pipeline with RAG + LLM
    
    Args:
        event_input: Event details dict
        use_llm: Whether to use LLM (set False to fallback to pure templates)
        llm_mode: "enhance" (lightweight) or "generate" (full generation)
        
    Returns:
        Complete WBS with extracted_info, epics_task, tasks, departments, risks
    """
    
    # Extract input data
    event_name = event_input.get("event_name", "Sự kiện")
    event_type = event_input.get("event_type", "conference")
    event_date = event_input.get("event_date", "")
    venue = event_input.get("venue", "FPT University")
    headcount_total = event_input.get("headcount_total", 50)
    departments = event_input.get("departments", [])
    special_requirements = event_input.get("special_requirements", [])
    
    # Validate event_date
    try:
        datetime.strptime(event_date, "%Y-%m-%d")
    except:
        event_date = datetime.now().strftime("%Y-%m-%d")
    
    # Classify venue
    venue_tier = classify_venue(venue)
    
    # Initialize RAG engine
    rag = SimpleRAGEngine()
    
    # Retrieve similar events
    similar_events = rag.retrieve_similar_events(
        event_type=event_type,
        venue_tier=venue_tier,
        headcount_total=headcount_total,
        departments=departments,
        top_k=3
    )
    
    # Extract best practices
    best_practices = rag.extract_best_practices(similar_events)
    
    # Get venue-specific requirements
    venue_reqs = rag.get_venue_specific_requirements(venue_tier)
    
    # Combine special requirements
    all_special_reqs = list(set(special_requirements + best_practices.get("special_requirements", [])))
    
    # Build RAG context
    rag_context = {
        "key_tasks": best_practices.get("key_tasks", []),
        "lessons_learned": best_practices.get("lessons_learned", []),
        "special_requirements": all_special_reqs,
        "venue_specific_requirements": venue_reqs,
        "similar_events": [e["event"]["event_name"] for e in similar_events]
    }
    
    # Event context for LLM
    event_context = {
        "event_type": event_type,
        "event_name": event_name,
        "venue": venue,
        "venue_tier": venue_tier,
        "headcount_total": headcount_total,
        "event_date": event_date,
        "special_requirements": all_special_reqs
    }
    
    # Generate epics
    normalized_depts = [get_department_bucket(d) for d in departments]
    unique_depts = list(dict.fromkeys(normalized_depts))  # Remove duplicates, keep order
    
    epics = []
    for i, dept in enumerate(departments):
        epic = generate_epic_from_department(dept, f"EP-{i+1:03d}")
        epics.append(epic)
    
    # Calculate worker distribution
    num_departments = len(epics)
    available_workers = calculate_available_workers(headcount_total, num_departments)
    worker_distribution = distribute_workers_to_departments(
        available_workers,
        [e["department"] for e in epics],
        venue_tier
    )
    
    # Initialize LLM generator (optional)
    llm_gen = None
    if use_llm:
        llm_gen = LLMTaskGenerator()
        if not llm_gen.client:
            print("⚠️ LLM not available, falling back to templates")
            use_llm = False
    
    # Generate tasks
    tasks = []
    task_counter = 1
    
    # Parse event date
    try:
        event_dt = datetime.strptime(event_date, "%Y-%m-%d")
    except:
        event_dt = datetime.now() + timedelta(days=30)
    
    for epic in epics:
        epic_id = epic["epic_id"]
        epic_name = epic["name"]
        department = epic["department"]
        normalized_dept = normalize_department(department)
        
        # Get number of workers
        num_workers = worker_distribution.get(department, 1)
        
        # Get base templates
        base_templates = ACTION_TEMPLATES.get(epic_name, [])
        
        # Calculate target task count
        target_count = min(len(base_templates), max(3, num_workers * 2))
        
        # Select base templates
        base_tasks = base_templates[:target_count]
        
        # LLM enhancement or generation
        if use_llm and llm_gen:
            if llm_mode == "generate":
                # Full LLM generation with RAG context
                generated_tasks = llm_gen.generate_tasks_with_rag(
                    epic_name=epic_name,
                    department=department,
                    event_context=event_context,
                    rag_context=rag_context,
                    num_workers=num_workers,
                    base_tasks=base_tasks
                )
                
                if generated_tasks:
                    base_tasks = generated_tasks
            
            elif llm_mode == "enhance":
                # Lightweight enhancement (just make names specific)
                base_tasks = llm_gen.enhance_template_tasks(base_tasks, event_context)
        
        # Convert to final task format
        epic_task_map: Dict[str, str] = {}
        
        for action in base_tasks:
            task_name = action["name"]
            task_id = f"T-{task_counter:03d}"
            task_counter += 1
            
            # Calculate dates
            duration = action.get("duration_days", 2)
            adjusted_duration = max(1, int(duration * get_tier_multiplier(venue_tier)))
            
            priority = action.get("priority", "medium")
            days_before = _calculate_days_before_event(priority, adjusted_duration)
            
            deadline_dt = event_dt - timedelta(days=days_before)
            start_dt = deadline_dt - timedelta(days=adjusted_duration - 1)
            
            # Resolve dependencies
            depends_on_names = action.get("depends_on", [])
            depends_on_ids = [epic_task_map.get(name, "") for name in depends_on_names]
            depends_on_ids = [tid for tid in depends_on_ids if tid]
            
            # Create task
            task = {
                "task_id": task_id,
                "epic_id": epic_id,
                "name": task_name,
                "category": epic_name,
                "description": action.get("description", ""),
                "priority": priority,
                "start-date": start_dt.strftime("%Y-%m-%d"),
                "deadline": deadline_dt.strftime("%Y-%m-%d"),
                "assign": "",  # To be assigned by HOD
                "depends_on": depends_on_ids,
                "complexity": _priority_to_complexity(priority),
            }
            
            tasks.append(task)
            epic_task_map[task_name] = task_id
    
    # Update epic dates based on tasks
    for epic in epics:
        epic_tasks = [t for t in tasks if t["epic_id"] == epic["epic_id"]]
        if epic_tasks:
            start_dates = [datetime.strptime(t["start-date"], "%Y-%m-%d") for t in epic_tasks]
            end_dates = [datetime.strptime(t["deadline"], "%Y-%m-%d") for t in epic_tasks]
            
            epic["start-date"] = min(start_dates).strftime("%Y-%m-%d")
            epic["end-date"] = max(end_dates).strftime("%Y-%m-%d")
    
    # Group tasks by department (normalized)
    departments_output: Dict[str, List[Dict[str, Any]]] = {
        "hậu cần": [],
        "marketing": [],
        "chuyên môn": [],
        "tài chính": [],
        "đối ngoại": [],
    }
    
    # Map epic_id to normalized department
    epic_dept_map = {}
    for e in epics:
        normalized = get_department_bucket(e["department"])
        epic_dept_map[e["epic_id"]] = normalized
    
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
    
    # Generate risks
    risks_by_dept = generate_risks_by_department(
        departments=unique_depts,
        venue_tier=venue_tier,
        event_type=event_type
    )
    
    risks_overall = generate_overall_risks(
        venue_tier=venue_tier,
        event_type=event_type
    )
    
    risks = {
        "by_department": risks_by_dept,
        "overall": risks_overall
    }
    
    # Prepare result
    result = {
        "extracted_info": {
            "event_name": event_name,
            "event_type": event_type,
            "event_date": event_date,
            "venue": venue,
            "headcount_total": headcount_total,
            "departments": departments,
            "venue_tier": venue_tier,
            "available_workers": available_workers,
            "worker_distribution": worker_distribution,
        },
        "epics_task": epics,
        "tasks": tasks,
        "departments": departments_output,
        "risks": risks,
        "rag_insights": {
            "similar_events": [e["event"]["event_name"] for e in similar_events],
            "key_learnings": best_practices.get("lessons_learned", [])[:5],
            "special_requirements": all_special_reqs,
        }
    }
    
    # Add cost info if LLM was used
    if use_llm and llm_gen:
        result["llm_cost"] = llm_gen.get_total_cost()
    
    return result


def _calculate_days_before_event(priority: str, duration: int) -> int:
    """Calculate how many days before event this task should be completed"""
    base_days = {
        "critical": 1,
        "high": 5,
        "medium": 10,
        "low": 15,
    }
    return base_days.get(priority, 7) + duration


def _priority_to_complexity(priority: str) -> str:
    """Map priority to complexity level"""
    mapping = {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
    }
    return mapping.get(priority, "medium")


# Backward compatibility alias
def run_pipeline(event_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Backward compatible wrapper for old run_pipeline calls
    """
    return run_pipeline_with_rag(event_input, use_llm=True, llm_mode="enhance")


# Example usage
if __name__ == "__main__":
    print("="*80)
    print("PIPELINE V3 - HYBRID RAG + LLM")
    print("="*80)
    
    # Test event
    event_input = {
        "event_name": "FPT Concert Khai Giảng 2025",
        "event_type": "concert_opening",
        "event_date": "2025-12-29",
        "venue": "Đường 30m FPT",
        "headcount_total": 100,
        "departments": ["hậu cần", "marketing", "chuyên môn", "tài chính"],
        "special_requirements": []
    }
    
    print("\n📝 Event Input:")
    for key, value in event_input.items():
        print(f"  {key}: {value}")
    
    print("\n" + "="*80)
    print("Running Pipeline...")
    print("="*80)
    
    result = run_pipeline_with_rag(event_input, use_llm=False)
    
    print(f"\n✅ Generated:")
    print(f"  Epics: {len(result['epics_task'])}")
    print(f"  Tasks: {len(result['tasks'])}")
    print(f"  Available workers: {result['extracted_info']['available_workers']}")
    print(f"\n📚 RAG Insights:")
    print(f"  Similar events: {', '.join(result['rag_insights']['similar_events'])}")
    print(f"  Key learnings: {len(result['rag_insights']['key_learnings'])}")
    
    print("\n✅ PIPELINE V3 READY!")