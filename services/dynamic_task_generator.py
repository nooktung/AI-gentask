"""
Dynamic Task Generator
Tạo/sửa số task để khớp nhân lực; phân bổ suggested_team_size theo ràng buộc
"""

from typing import List, Dict, Any, Tuple
from services.task_complexity import (
    calculate_task_complexity,
    calculate_suggested_team_size,
    get_complexity_weight
)
from services.priority_classifier import (
    classify_priority_hybrid,
    get_priority_weight
)
from services.venue_classifier import VenueTier
from services.task_generator import ACTION_TEMPLATES


def calculate_available_workers(headcount_total: int, num_departments: int) -> int:
    """
    Tính số workers khả dụng
    
    Formula: Available = Total - 1 HOOC - Number of HODs
    
    Args:
        headcount_total: Tổng số người
        num_departments: Số ban (mỗi ban có 1 HOD)
        
    Returns:
        Số workers khả dụng
    """
    if headcount_total <= 0:
        return 0
    
    hooc_count = 1  # 1 HOOC
    hod_count = num_departments  # Mỗi ban có 1 HOD
    
    available = headcount_total - hooc_count - hod_count
    
    # Minimum 1 worker
    return max(1, available)


def assign_team_sizes_to_tasks(
    tasks: List[Dict[str, Any]],
    available_workers: int,
    venue_tier: VenueTier,
    event_context: Dict[str, Any],
    dependency_analysis: Dict[str, Any] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Gán suggested_team_size cho từng task với ràng buộc:
    - sum(suggested_team_size) = available_workers
    - 1 ≤ team_size ≤ 5 cho mỗi task
    
    Args:
        tasks: List các tasks (chưa có suggested_team_size)
        available_workers: Số workers khả dụng
        venue_tier: Venue tier
        event_context: Event context
        dependency_analysis: Kết quả từ dependency_analyzer
        
    Returns:
        Tuple (tasks_with_team_size, stats)
    """
    if not tasks:
        return [], {"total_team_size": 0, "adjustments": []}
    
    # Tính complexity và suggested_team_size ban đầu cho mỗi task
    tasks_with_size = []
    critical_path_tasks = set()
    
    if dependency_analysis:
        # Lấy critical path tasks
        critical_path = dependency_analysis.get("critical_path", [])
        critical_path_tasks = set(critical_path)
    
    for task in tasks:
        # Tính complexity
        complexity = calculate_task_complexity(
            task=task,
            venue_tier=venue_tier,
            event_type=event_context.get("event_type", ""),
            dependencies=task.get("depends_on", [])
        )
        task["complexity"] = complexity
        
        # Tính suggested_team_size ban đầu
        has_critical_deps = any(
            dep_id in critical_path_tasks 
            for dep_id in task.get("depends_on", [])
        )
        
        # Get department from task (could be in category, department, or normalized_dept field)
        task_department = task.get("department") or task.get("category") or None
        
        suggested_size = calculate_suggested_team_size(
            complexity=complexity,
            duration_days=task.get("duration_days", 1),
            venue_tier=venue_tier,
            has_critical_dependencies=has_critical_deps,
            department=task_department  # Pass department for special handling
        )
        
        task["suggested_team_size"] = suggested_size
        tasks_with_size.append(task)
    
    # Tính tổng suggested_team_size hiện tại
    total_team_size = sum(t["suggested_team_size"] for t in tasks_with_size)
    
    # Điều chỉnh để khớp với available_workers
    adjustments = []
    
    if total_team_size < available_workers:
        # Thiếu người → expand tasks hoặc tăng team_size
        diff = available_workers - total_team_size
        adjustments.append(f"Thiếu {diff} người, cần expand hoặc tăng team_size")
        
        # Phân bổ thêm vào các task quan trọng
        tasks_with_size = _distribute_excess_workers(
            tasks_with_size, diff, available_workers
        )
        
    elif total_team_size > available_workers:
        # Thừa người → merge tasks hoặc giảm team_size
        diff = total_team_size - available_workers
        adjustments.append(f"Thừa {diff} người, cần merge hoặc giảm team_size")
        
        # Giảm team_size từ các task ít quan trọng
        tasks_with_size = _reduce_team_sizes(
            tasks_with_size, diff, available_workers
        )
    
    # Verify ràng buộc
    final_total = sum(t["suggested_team_size"] for t in tasks_with_size)
    
    # Đảm bảo mỗi task: 1 ≤ team_size ≤ 5
    for task in tasks_with_size:
        task["suggested_team_size"] = max(1, min(5, task["suggested_team_size"]))
    
    stats = {
        "total_team_size": final_total,
        "available_workers": available_workers,
        "adjustments": adjustments,
        "is_balanced": abs(final_total - available_workers) <= 1
    }
    
    return tasks_with_size, stats


def _distribute_excess_workers(
    tasks: List[Dict[str, Any]],
    excess: int,
    available_workers: int
) -> List[Dict[str, Any]]:
    """
    Phân bổ workers dư vào các task quan trọng
    
    Strategy: Ưu tiên critical/high priority tasks
    """
    # Sắp xếp theo priority và complexity
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (
            {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(
                t.get("priority", "medium"), 2
            ),
            {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(
                t.get("complexity", "medium"), 2
            )
        ),
        reverse=True
    )
    
    remaining = excess
    for task in sorted_tasks:
        if remaining <= 0:
            break
        
        current_size = task["suggested_team_size"]
        if current_size < 5:  # Chưa đạt max
            add = min(remaining, 5 - current_size)
            task["suggested_team_size"] += add
            remaining -= add
    
    # Nếu vẫn còn dư, có thể expand tasks (tạo thêm subtasks)
    # Hoặc tăng team_size của các task hiện có
    if remaining > 0:
        # Tăng đều cho tất cả tasks
        per_task = remaining // len(tasks)
        remainder = remaining % len(tasks)
        
        for i, task in enumerate(tasks):
            add = per_task + (1 if i < remainder else 0)
            task["suggested_team_size"] = min(5, task["suggested_team_size"] + add)
    
    return tasks


def _reduce_team_sizes(
    tasks: List[Dict[str, Any]],
    excess: int,
    available_workers: int
) -> List[Dict[str, Any]]:
    """
    Giảm team_size từ các task ít quan trọng
    
    Strategy: Giảm từ low/medium priority tasks trước
    """
    # Sắp xếp theo priority (thấp trước)
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (
            {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(
                t.get("priority", "medium"), 2
            ),
            {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(
                t.get("complexity", "medium"), 2
            )
        )
    )
    
    remaining = excess
    for task in sorted_tasks:
        if remaining <= 0:
            break
        
        current_size = task["suggested_team_size"]
        if current_size > 1:  # Chưa đạt min
            reduce = min(remaining, current_size - 1)
            task["suggested_team_size"] -= reduce
            remaining -= reduce
    
    # Nếu vẫn còn thừa, có thể merge tasks
    # Hoặc giảm thêm team_size (nhưng không dưới 1)
    if remaining > 0:
        # Giảm đều từ các task có thể giảm
        reducible_tasks = [t for t in tasks if t["suggested_team_size"] > 1]
        if reducible_tasks:
            per_task = remaining // len(reducible_tasks)
            remainder = remaining % len(reducible_tasks)
            
            for i, task in enumerate(reducible_tasks):
                reduce = per_task + (1 if i < remainder else 0)
                task["suggested_team_size"] = max(1, task["suggested_team_size"] - reduce)
    
    return tasks


def expand_tasks_if_needed(
    tasks: List[Dict[str, Any]],
    available_workers: int,
    epic_name: str
) -> List[Dict[str, Any]]:
    """
    Expand (bẻ nhỏ) tasks nếu quá ít task so với số người
    
    Args:
        tasks: List tasks hiện tại
        available_workers: Số workers khả dụng
        epic_name: Tên epic để lấy templates
        
    Returns:
        Expanded tasks
    """
    current_task_count = len(tasks)
    
    # Nếu số task quá ít so với workers (mỗi task tối đa 5 người)
    max_workers_used = current_task_count * 5
    
    if max_workers_used < available_workers:
        # Cần expand: thêm tasks từ templates
        templates = ACTION_TEMPLATES.get(epic_name, [])
        used_names = {t["name"] for t in tasks}
        
        # Thêm tasks mới từ templates chưa dùng
        for template in templates:
            if len(tasks) * 5 >= available_workers:
                break
            
            if template["name"] not in used_names:
                # Tạo task mới từ template
                new_task = {
                    "name": template["name"],
                    "description": template.get("description", ""),
                    "priority": template.get("priority", "medium"),
                    "duration_days": template.get("duration_days", 1),
                    "depends_on": template.get("depends_on", []),
                    "suggested_team_size": 1  # Sẽ được tính lại sau
                }
                tasks.append(new_task)
                used_names.add(template["name"])
    
    return tasks


def merge_tasks_if_needed(
    tasks: List[Dict[str, Any]],
    available_workers: int
) -> List[Dict[str, Any]]:
    """
    Merge (gộp) tasks nếu quá nhiều task so với số người
    
    Args:
        tasks: List tasks hiện tại
        available_workers: Số workers khả dụng
        
    Returns:
        Merged tasks
    """
    # Nếu số task > available_workers (mỗi task tối thiểu 1 người)
    if len(tasks) > available_workers:
        # Merge các tasks ít quan trọng lại
        sorted_tasks = sorted(
            tasks,
            key=lambda t: (
                {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(
                    t.get("priority", "medium"), 2
                )
            )
        )
        
        # Gộp các tasks low priority
        low_priority_tasks = [t for t in sorted_tasks if t.get("priority") == "low"]
        medium_priority_tasks = [t for t in sorted_tasks if t.get("priority") == "medium"]
        
        merged_tasks = []
        merged_count = 0
        
        # Giữ lại các tasks quan trọng
        for task in sorted_tasks:
            if task.get("priority") in ["critical", "high"]:
                merged_tasks.append(task)
            elif task.get("priority") == "medium" and merged_count < available_workers - len([t for t in sorted_tasks if t.get("priority") in ["critical", "high"]]):
                merged_tasks.append(task)
                merged_count += 1
        
        # Gộp các tasks low priority thành 1 task
        if low_priority_tasks and len(merged_tasks) < available_workers:
            merged_low_task = {
                "name": f"Hoàn thiện các công việc phụ ({len(low_priority_tasks)} tasks)",
                "description": f"Gộp {len(low_priority_tasks)} tasks phụ",
                "priority": "low",
                "duration_days": max(t.get("duration_days", 1) for t in low_priority_tasks),
                "depends_on": [],
                "suggested_team_size": 1
            }
            merged_tasks.append(merged_low_task)
        
        return merged_tasks
    
    return tasks


def generate_tasks_with_dynamic_sizing(
    epics: List[Dict[str, Any]],
    event_context: Dict[str, Any],
    venue_tier: VenueTier,
    headcount_total: int,
    dependency_analysis: Dict[str, Any] = None
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Generate tasks với dynamic team sizing
    
    Args:
        epics: List epics
        event_context: Event context
        venue_tier: Venue tier
        headcount_total: Tổng số người
        dependency_analysis: Dependency analysis result
        
    Returns:
        Tuple (tasks, stats)
    """
    num_departments = len(epics)
    available_workers = calculate_available_workers(headcount_total, num_departments)
    
    all_tasks = []
    task_counter = 1
    
    for epic in epics:
        epic_id = epic["epic_id"]
        epic_name = epic["name"]
        
        # Lấy templates
        templates = ACTION_TEMPLATES.get(epic_name, [])
        
        # Tạo tasks từ templates
        epic_tasks = []
        for template in templates:
            task = {
                "task_id": f"T-{task_counter:03d}",
                "epic_id": epic_id,
                "name": template["name"],
                "description": template.get("description", ""),
                "priority": template.get("priority", "medium"),
                "duration_days": template.get("duration_days", 1),
                "depends_on": template.get("depends_on", []),
                "category": epic_name
            }
            epic_tasks.append(task)
            task_counter += 1
        
        all_tasks.extend(epic_tasks)
    
    # Expand hoặc merge nếu cần
    # (Logic này có thể được cải thiện để expand/merge theo từng epic)
    
    # Gán team_size với ràng buộc
    tasks_with_size, stats = assign_team_sizes_to_tasks(
        tasks=all_tasks,
        available_workers=available_workers,
        venue_tier=venue_tier,
        event_context=event_context,
        dependency_analysis=dependency_analysis
    )
    
    return tasks_with_size, stats



