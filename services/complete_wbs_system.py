"""
Complete WBS System - Tích hợp tất cả modules
Dynamic Task Generation + CPM + Dependency Analysis + Priority Classification
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.task_template_service import (
    calculate_available_workers,
    ACTION_TEMPLATES
)
from services.dependency_service import (
    analyze_dependencies,
    build_dependency_graph,
    topological_sort,
    find_parallel_tasks
)
from services.priority_service import (
    classify_priority_hybrid,
    calculate_priority_score
)
from services.task_complexity_service import (
    calculate_task_complexity,
    calculate_suggested_team_size
)
from modules.wbs.cpm_scheduler import calculate_cpm, detect_parallel_opportunities
from services.venue_service import classify_venue, VenueTier
from utils.department_normalizer import get_department_bucket


def generate_complete_wbs(
    event_input: Dict[str, Any],
    use_cpm: bool = True,
    use_dependency_analysis: bool = True
) -> Dict[str, Any]:
    """
    Generate complete WBS với tất cả tính năng:
    - Dynamic task generation với suggested_team_size
    - CPM scheduling (ES/EF/LS/LF/Slack)
    - Dependency analysis (4 nhóm)
    - Priority classification (rule + context)
    - Task complexity calculation
    
    Args:
        event_input: {
            event_name, event_type, event_date, venue,
            headcount_total, departments, special_requirements
        }
        use_cpm: Có dùng CPM không
        use_dependency_analysis: Có phân tích dependencies không
        
    Returns:
        Complete WBS với tất cả thông tin
    """
    # Extract input
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
        event_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
    
    # Classify venue
    venue_tier = classify_venue(venue)
    
    # Event context
    event_context = {
        "event_name": event_name,
        "event_type": event_type,
        "event_date": event_date,
        "venue": venue,
        "venue_tier": venue_tier,
        "headcount_total": headcount_total,
        "special_requirements": special_requirements
    }
    
    # Generate epics
    epics = []
    for i, dept in enumerate(departments):
        normalized_dept = get_department_bucket(dept)
        
        epic_mapping = {
            "hậu cần": "Điều phối vận hành & hậu cần",
            "marketing": "Triển khai truyền thông & marketing",
            "chuyên môn": "Quản lý chuyên môn & kỹ thuật",
            "tài chính": "Quản lý tài chính sự kiện",
            "đối ngoại": "Làm việc với nghệ sĩ & đối tác",
            "thiết kế": "Thiết kế & sáng tạo nội dung"
        }
        
        epic_name = epic_mapping.get(normalized_dept, f"Điều phối {dept}")
        
        epic = {
            "epic_id": f"EP-{i+1:03d}",
            "name": epic_name,
            "department": dept,
            "description": f"Epic cho {dept}"
        }
        epics.append(epic)
    
    # Generate tasks với dynamic sizing
    # Lưu ý: generate_tasks_with_dynamic_sizing trả về tasks với depends_on là names
    # Cần resolve thành IDs sau
    tasks, sizing_stats = generate_tasks_with_dynamic_sizing(
        epics=epics,
        event_context=event_context,
        venue_tier=venue_tier,
        headcount_total=headcount_total
    )
    
    # Resolve dependencies từ names sang IDs
    task_name_to_id = {t["name"]: t["task_id"] for t in tasks}
    for task in tasks:
        depends_on_names = task.get("depends_on", [])
        if depends_on_names and isinstance(depends_on_names[0], str):
            # Nếu là names, convert sang IDs
            depends_on_ids = [
                task_name_to_id.get(name, "") 
                for name in depends_on_names
                if task_name_to_id.get(name, "")
            ]
            task["depends_on"] = depends_on_ids
    
    # Dependency Analysis
    dependency_analysis = None
    if use_dependency_analysis and tasks:
        dependency_analysis = analyze_dependencies(tasks, event_context)
    
    # Priority Classification (rule + context)
    # Critical path sẽ được tính từ CPM, tạm thời dùng empty set
    critical_path_tasks = set()
    
    # Priority classification sẽ được cập nhật sau khi có CPM
    # Tạm thời classify với critical_path_tasks = empty
    for task in tasks:
        # Classify priority (sẽ được cập nhật lại sau khi có CPM)
        priority = classify_priority_hybrid(
            task=task,
            event_context=event_context,
            all_tasks=tasks,
            dependency_context={
                "is_on_critical_path": task["task_id"] in critical_path_tasks,
                "has_critical_deps": any(
                    dep_id in critical_path_tasks 
                    for dep_id in task.get("depends_on", [])
                ),
                "is_blocking_many": len([
                    t for t in tasks 
                    if task["task_id"] in t.get("depends_on", [])
                ]) > 2
            },
            critical_path_tasks=critical_path_tasks
        )
        task["priority"] = priority
        
        # Calculate complexity
        complexity = calculate_task_complexity(
            task=task,
            venue_tier=venue_tier,
            event_type=event_type,
            dependencies=task.get("depends_on", [])
        )
        task["complexity"] = complexity
        
        # Calculate suggested_team_size nếu chưa có
        if "suggested_team_size" not in task:
            has_critical_deps = any(
                dep_id in critical_path_tasks 
                for dep_id in task.get("depends_on", [])
            )
            # Get department from task (could be in category, department, or epic_id)
            task_department = task.get("department") or task.get("category") or None
            
            task["suggested_team_size"] = calculate_suggested_team_size(
                complexity=complexity,
                duration_days=task.get("duration_days", 1),
                venue_tier=venue_tier,
                has_critical_dependencies=has_critical_deps,
                department=task_department  # Pass department for special handling
            )
    
    # Re-assign team sizes với dependency context
    num_departments = len(epics)
    available_workers = calculate_available_workers(headcount_total, num_departments)
    
    tasks, sizing_stats = assign_team_sizes_to_tasks(
        tasks=tasks,
        available_workers=available_workers,
        venue_tier=venue_tier,
        event_context=event_context,
        dependency_analysis=dependency_analysis
    )
    
    # CPM Scheduling
    cpm_result = None
    if use_cpm and tasks:
        cpm_result = calculate_cpm(
            tasks=tasks,
            event_date=event_date
        )
        
        # Lấy critical path từ CPM
        critical_path_tasks = set(cpm_result.get("critical_path", []))
        
        # Cập nhật lại priority với critical path đã biết
        for task in tasks:
            # Re-classify priority với critical path
            priority = classify_priority_hybrid(
                task=task,
                event_context=event_context,
                all_tasks=tasks,
                dependency_context={
                    "is_on_critical_path": task["task_id"] in critical_path_tasks,
                    "has_critical_deps": any(
                        dep_id in critical_path_tasks 
                        for dep_id in task.get("depends_on", [])
                    ),
                    "is_blocking_many": len([
                        t for t in tasks 
                        if task["task_id"] in t.get("depends_on", [])
                    ]) > 2
                },
                critical_path_tasks=critical_path_tasks
            )
            task["priority"] = priority
        
        # Cập nhật tasks với CPM data
        tasks_with_cpm = {t["task_id"]: t for t in cpm_result["tasks_with_cpm"]}
        for task in tasks:
            task_id = task["task_id"]
            if task_id in tasks_with_cpm:
                cpm_data = tasks_with_cpm[task_id]
                task["ES"] = cpm_data.get("ES")
                task["EF"] = cpm_data.get("EF")
                task["LS"] = cpm_data.get("LS")
                task["LF"] = cpm_data.get("LF")
                task["slack"] = cpm_data.get("slack", 0)
                task["is_critical"] = cpm_data.get("is_critical", False)
                task["planned_start"] = cpm_data.get("ES")
                task["planned_end"] = cpm_data.get("EF")
    
    # Parallel opportunities
    parallel_opportunities = []
    if cpm_result:
        parallel_opportunities = detect_parallel_opportunities(tasks, cpm_result)
    
    # Prepare result
    result = {
        "status": "ok",
        "event_id": f"EVT-{datetime.now().strftime('%Y%m%d')}-001",
        "meta": {
            "event_name": event_name,
            "event_type": event_type,
            "event_date": event_date,
            "venue": venue,
            "venue_tier": venue_tier.value if isinstance(venue_tier, VenueTier) else venue_tier,
            "headcount_total": headcount_total,
            "available_workers": available_workers,
            "generated_at": datetime.now().strftime("%Y-%m-%d")
        },
        "epics": epics,
        "tasks": tasks,
        "sizing_stats": sizing_stats,
        "cpm": cpm_result,
        "dependency_analysis": dependency_analysis,
        "parallel_opportunities": parallel_opportunities,
        "summary": {
            "epic_count": len(epics),
            "task_count": len(tasks),
            "total_team_size": sizing_stats.get("total_team_size", 0),
            "available_workers": available_workers,
            "is_balanced": sizing_stats.get("is_balanced", False),
            "critical_path_length": len(cpm_result["critical_path"]) if cpm_result else 0,
            "project_duration": cpm_result.get("project_duration", 0) if cpm_result else 0
        }
    }
    
    return result


def generate_wbs_legacy_compatible(
    event_input: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate WBS tương thích với legacy format
    
    Returns format tương tự như run_pipeline()
    """
    complete_wbs = generate_complete_wbs(event_input)
    
    # Convert to legacy format
    legacy_tasks = []
    for task in complete_wbs["tasks"]:
        legacy_task = {
            "task_id": task["task_id"],
            "epic_id": task["epic_id"],
            "name": task["name"],
            "depends_on": task.get("depends_on", []),
            "can_parallel": task.get("slack", 0) > 0,
            "planned_start": task.get("planned_start", task.get("ES", "")),
            "planned_end": task.get("planned_end", task.get("EF", "")),
            "deadline": task.get("deadline", task.get("EF", "")),
            "priority": task.get("priority", "medium"),
            "suggested_team_size": task.get("suggested_team_size", 1),
            "complexity": task.get("complexity", "medium"),
            "slack": task.get("slack", 0),
            "is_critical": task.get("is_critical", False)
        }
        legacy_tasks.append(legacy_task)
    
    # Generate milestones từ critical tasks
    milestones = []
    for task in complete_wbs["tasks"]:
        if task.get("is_critical") and task.get("priority") == "critical":
            milestones.append({
                "name": task["name"],
                "task_id": task["task_id"],
                "date": task.get("planned_end", task.get("EF", ""))
            })
    
    return {
        "status": "ok",
        "event_id": complete_wbs["event_id"],
        "meta": complete_wbs["meta"],
        "epics": complete_wbs["epics"],
        "tasks": legacy_tasks,
        "milestones": milestones,
        "summary": {
            **complete_wbs["summary"],
            "critical_path_example": complete_wbs["cpm"]["critical_path"] if complete_wbs["cpm"] else [],
            "feasibility": {
                "status": "feasible" if complete_wbs["sizing_stats"].get("is_balanced") else "needs_review",
                "min_required_headcount": complete_wbs["sizing_stats"].get("total_team_size", 0)
            }
        }
    }

