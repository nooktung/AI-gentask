from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import pytz


def schedule_tasks_backward(event_date: str, tasks: List[Dict[str, Any]], 
                          milestones: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Schedule tasks backward from event_date, respecting dependencies and milestone anchors
    """
    bangkok_tz = pytz.timezone('Asia/Bangkok')
    event_dt = datetime.strptime(event_date, "%Y-%m-%d").date()
    
    # Milestone anchors (days before event)
    milestone_anchors = {
        "Final Rehearsal": 1,  # D-1
        "Site Ready": 2,        # D-2
        "Permits Approved": 8   # D-8
    }
    
    # Initialize task scheduling
    scheduled_tasks = []
    task_dict = {task["task_id"]: task for task in tasks}
    
    # Create dependency graph
    dependencies = {}
    for task in tasks:
        dependencies[task["task_id"]] = task.get("depends_on", [])
    
    # Topological sort for backward scheduling
    visited = set()
    temp_visited = set()
    schedule_order = []
    
    def dfs(node):
        if node in temp_visited:
            return  # Cycle detected
        if node in visited:
            return
        
        temp_visited.add(node)
        for dep in dependencies.get(node, []):
            dfs(dep)
        temp_visited.remove(node)
        visited.add(node)
        schedule_order.append(node)
    
    # Build schedule order
    for task_id in task_dict.keys():
        if task_id not in visited:
            dfs(task_id)
    
    # Schedule tasks backward
    current_date = event_dt
    
    for task_id in reversed(schedule_order):
        task = task_dict[task_id]
        
        # Check if this is a milestone task
        is_milestone = task.get("milestone", False)
        milestone_name = task.get("name", "")
        
        # Calculate start date based on duration
        duration_days = task.get("duration_days", 1)
        start_date = current_date - timedelta(days=duration_days - 1)
        
        # Apply milestone anchors
        for anchor_name, days_before in milestone_anchors.items():
            if anchor_name.lower() in milestone_name.lower():
                anchor_date = event_dt - timedelta(days=days_before)
                if start_date > anchor_date:
                    start_date = anchor_date
                    duration_days = (current_date - start_date).days + 1
                break
        
        # Update task with scheduled dates
        scheduled_task = task.copy()
        scheduled_task["planned_start"] = start_date.strftime("%Y-%m-%d")
        scheduled_task["planned_end"] = current_date.strftime("%Y-%m-%d")
        scheduled_task["duration_days"] = duration_days
        
        scheduled_tasks.append(scheduled_task)
        
        # Move current_date backward
        current_date = start_date - timedelta(days=1)
    
    # Update milestones with actual dates
    updated_milestones = []
    for milestone in milestones:
        task_id = milestone["task_id"]
        for task in scheduled_tasks:
            if task["task_id"] == task_id:
                updated_milestone = milestone.copy()
                updated_milestone["date"] = task["planned_end"]
                updated_milestones.append(updated_milestone)
                break
    
    return scheduled_tasks, updated_milestones


def calculate_critical_path(tasks: List[Dict[str, Any]]) -> List[str]:
    """
    Calculate critical path through tasks
    """
    # Simple critical path: longest dependency chain
    task_dict = {task["task_id"]: task for task in tasks}
    max_chain = []
    max_length = 0
    
    def find_longest_chain(task_id, current_chain):
        nonlocal max_chain, max_length
        
        if len(current_chain) > max_length:
            max_length = len(current_chain)
            max_chain = current_chain.copy()
        
        for dep in task_dict[task_id].get("depends_on", []):
            if dep not in current_chain:  # Avoid cycles
                find_longest_chain(dep, current_chain + [dep])
    
    # Start from tasks with no dependencies
    for task_id, task in task_dict.items():
        if not task.get("depends_on"):
            find_longest_chain(task_id, [task_id])
    
    return max_chain


def check_feasibility(tasks: List[Dict[str, Any]], headcount_total: int) -> Dict[str, Any]:
    """
    Check if the schedule is feasible with given headcount
    """
    # Calculate total effort based on task complexity
    total_effort = 0
    for task in tasks:
        # Estimate effort based on priority and dependencies
        base_effort = 1
        if task.get("priority") == "critical":
            base_effort = 3
        elif task.get("priority") == "high":
            base_effort = 2
        elif task.get("priority") == "medium":
            base_effort = 1.5
        
        # Add complexity based on dependencies
        dep_count = len(task.get("depends_on", []))
        complexity_multiplier = 1 + (dep_count * 0.2)
        
        total_effort += base_effort * complexity_multiplier
    
    # Estimate minimum required headcount
    min_required = max(1, int(total_effort // 10))  # Rough estimate
    
    # Check if feasible
    is_feasible = min_required <= headcount_total
    
    # Find earliest feasible date if not feasible
    earliest_date = None
    if not is_feasible:
        # Calculate how many days we need
        required_days = max(7, int(total_effort // headcount_total))
        earliest_date = (datetime.now(pytz.timezone('Asia/Bangkok')).date() + 
                        timedelta(days=required_days)).strftime("%Y-%m-%d")
    
    return {
        "status": "feasible" if is_feasible else "infeasible",
        "min_required_headcount": min_required,
        "earliest_feasible_event_date": earliest_date,
        "recommended_merges": [],
        "dropped_optional_tasks": []
    }

