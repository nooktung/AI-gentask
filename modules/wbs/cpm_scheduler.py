"""
CPM Scheduler - Critical Path Method
Tính ES/EF, LS/LF, Slack, Critical Path đầy đủ
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import defaultdict, deque


def calculate_cpm(
    tasks: List[Dict[str, Any]],
    event_date: str,
    start_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tính CPM đầy đủ: ES/EF, LS/LF, Slack, Critical Path
    
    Args:
        tasks: List tasks với depends_on, duration_days
        event_date: Ngày event (deadline cuối cùng)
        start_date: Ngày bắt đầu (nếu None thì tính từ đầu)
        
    Returns:
        Dict với:
        - tasks_with_cpm: Tasks có thêm ES/EF/LS/LF/Slack
        - critical_path: List task_ids trên critical path
        - parallel_groups: Các nhóm tasks có thể chạy song song
        - project_duration: Tổng thời gian dự án
    """
    if not tasks:
        return {
            "tasks_with_cpm": [],
            "critical_path": [],
            "parallel_groups": [],
            "project_duration": 0
        }
    
    # Parse dates
    try:
        event_dt = datetime.strptime(event_date, "%Y-%m-%d").date()
    except:
        event_dt = datetime.now().date()
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
        except:
            start_dt = datetime.now().date()
    else:
        # Tính start_date từ event_date và dependencies
        start_dt = _calculate_earliest_start(tasks, event_dt)
    
    # Build dependency graph
    task_dict = {t["task_id"]: t for t in tasks}
    dependency_graph = defaultdict(list)
    reverse_graph = defaultdict(list)  # Để tìm predecessors
    
    for task in tasks:
        task_id = task["task_id"]
        depends_on = task.get("depends_on", [])
        dependency_graph[task_id] = depends_on
        
        for dep_id in depends_on:
            reverse_graph[dep_id].append(task_id)
    
    # FORWARD PASS: Tính ES (Earliest Start) và EF (Earliest Finish)
    es = {}  # {task_id: date}
    ef = {}  # {task_id: date}
    
    # Topological sort để xử lý theo thứ tự
    sorted_tasks = _topological_sort(dependency_graph)
    
    for task_id in sorted_tasks:
        task = task_dict[task_id]
        duration = task.get("duration_days", 1)
        depends_on = task.get("depends_on", [])
        
        if not depends_on:
            # Không có dependencies → ES = start_date
            es[task_id] = start_dt
        else:
            # ES = max(EF của tất cả predecessors)
            max_ef = max(ef.get(dep_id, start_dt) for dep_id in depends_on)
            # Buffer 1 ngày giữa các dependencies để an toàn
            es[task_id] = max_ef + timedelta(days=1)
        
        # EF = ES + duration - 1 (nếu tính theo ngày)
        ef[task_id] = es[task_id] + timedelta(days=duration - 1)
    
    # Project duration = max(EF của tất cả tasks)
    project_duration_days = max(
        (ef[task_id] - start_dt).days + 1 
        for task_id in sorted_tasks
    ) if sorted_tasks else 0
    
    # BACKWARD PASS: Tính LS (Latest Start) và LF (Latest Finish)
    lf = {}  # {task_id: date}
    ls = {}  # {task_id: date}
    
    # Tính từ cuối về đầu
    project_end_date = start_dt + timedelta(days=project_duration_days - 1)
    
    # Reverse topological sort (từ cuối về đầu)
    reverse_sorted = list(reversed(sorted_tasks))
    
    # Initialize LF cho tất cả tasks = project_end_date (tạm thời)
    for task_id in sorted_tasks:
        lf[task_id] = project_end_date
    
    # Tính từ cuối về đầu
    for task_id in reverse_sorted:
        task = task_dict[task_id]
        duration = task.get("duration_days", 1)
        successors = reverse_graph.get(task_id, [])
        
        if successors:
            # LF = min(LS của tất cả successors)
            # LS của successor = LF của successor - duration của successor + 1
            # Vì có buffer 1 ngày ở forward pass, ở backward pass giữ buffer tương ứng
            min_successor_lf = min(lf.get(succ_id, project_end_date) for succ_id in successors)
            # LF của task này = min(LF của successors) - 2 (1 ngày hoàn tất + 1 ngày buffer)
            lf[task_id] = min_successor_lf - timedelta(days=2)
        # Nếu không có successors, giữ nguyên project_end_date
        
        # LS = LF - duration + 1
        ls[task_id] = lf[task_id] - timedelta(days=duration - 1)
    
    # Tính SLACK (Total Float)
    slack = {}
    for task_id in sorted_tasks:
        # Slack = LS - ES = LF - EF
        slack_days = (ls[task_id] - es[task_id]).days
        slack[task_id] = slack_days
    
    # CRITICAL PATH: Tasks có slack = 0
    critical_path = [task_id for task_id in sorted_tasks if slack[task_id] == 0]
    
    # PARALLEL GROUPS: Tasks có thể chạy song song (cùng ES hoặc không phụ thuộc nhau)
    parallel_groups = _find_parallel_groups(tasks, dependency_graph, es)
    
    # Cập nhật tasks với CPM data
    tasks_with_cpm = []
    for task in tasks:
        task_id = task["task_id"]
        task_cpm = task.copy()
        task_cpm["ES"] = es.get(task_id, start_dt).strftime("%Y-%m-%d")
        task_cpm["EF"] = ef.get(task_id, start_dt).strftime("%Y-%m-%d")
        task_cpm["LS"] = ls.get(task_id, start_dt).strftime("%Y-%m-%d")
        task_cpm["LF"] = lf.get(task_id, start_dt).strftime("%Y-%m-%d")
        task_cpm["slack"] = slack.get(task_id, 0)
        task_cpm["is_critical"] = slack.get(task_id, 0) == 0
        tasks_with_cpm.append(task_cpm)
    
    return {
        "tasks_with_cpm": tasks_with_cpm,
        "critical_path": critical_path,
        "parallel_groups": parallel_groups,
        "project_duration": project_duration_days,
        "start_date": start_dt.strftime("%Y-%m-%d"),
        "end_date": project_end_date.strftime("%Y-%m-%d")
    }


def _calculate_earliest_start(
    tasks: List[Dict[str, Any]],
    event_date: datetime.date
) -> datetime.date:
    """
    Tính earliest start date từ event_date và dependencies
    """
    # Tính tổng duration của longest path
    task_dict = {t["task_id"]: t for t in tasks}
    dependency_graph = defaultdict(list)
    
    for task in tasks:
        dependency_graph[task["task_id"]] = task.get("depends_on", [])
    
    # Tìm longest path
    max_duration = 0
    
    def dfs(node: str, current_duration: int):
        nonlocal max_duration
        task = task_dict[node]
        duration = task.get("duration_days", 1)
        new_duration = current_duration + duration
        
        if new_duration > max_duration:
            max_duration = new_duration
        
        for dep in dependency_graph[node]:
            dfs(dep, new_duration)
    
    # Start từ tasks không có dependencies
    for task_id, task in task_dict.items():
        if not dependency_graph[task_id]:
            dfs(task_id, 0)
    
    # Start date = event_date - max_duration
    # Nhưng cần buffer, nên trừ thêm 7 ngày
    start_date = event_date - timedelta(days=max_duration + 7)
    
    # Không được quá khứ
    today = datetime.now().date()
    return max(start_date, today)


def _topological_sort(dependency_graph: Dict[str, List[str]]) -> List[str]:
    """
    Topological sort của dependency graph
    """
    in_degree = defaultdict(int)
    all_nodes = set()
    
    for node, deps in dependency_graph.items():
        all_nodes.add(node)
        in_degree[node] = len(deps)
        for dep in deps:
            all_nodes.add(dep)
            if dep not in in_degree:
                in_degree[dep] = 0
    
    queue = deque([node for node in all_nodes if in_degree[node] == 0])
    result = []
    
    while queue:
        node = queue.popleft()
        result.append(node)
        
        for other_node, deps in dependency_graph.items():
            if node in deps:
                in_degree[other_node] -= 1
                if in_degree[other_node] == 0:
                    queue.append(other_node)
    
    return result


def _find_parallel_groups(
    tasks: List[Dict[str, Any]],
    dependency_graph: Dict[str, List[str]],
    es: Dict[str, datetime.date]
) -> List[List[str]]:
    """
    Tìm các nhóm tasks có thể chạy song song
    """
    # Group theo ES date
    es_groups = defaultdict(list)
    
    for task in tasks:
        task_id = task["task_id"]
        es_date = es.get(task_id)
        if es_date:
            es_groups[es_date].append(task_id)
    
    # Các tasks cùng ES và không phụ thuộc nhau → có thể song song
    parallel_groups = []
    
    for es_date, task_ids in es_groups.items():
        if len(task_ids) > 1:
            # Check xem có tasks nào phụ thuộc nhau không
            independent_tasks = []
            for task_id in task_ids:
                deps = dependency_graph.get(task_id, [])
                # Nếu không có dependencies hoặc dependencies không trong cùng group
                if not any(dep in task_ids for dep in deps):
                    independent_tasks.append(task_id)
            
            if len(independent_tasks) > 1:
                parallel_groups.append(independent_tasks)
    
    return parallel_groups


def detect_parallel_opportunities(
    tasks: List[Dict[str, Any]],
    cpm_result: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Phát hiện cơ hội chạy song song
    
    Returns:
        List các opportunities với lý do
    """
    opportunities = []
    parallel_groups = cpm_result.get("parallel_groups", [])
    
    for group in parallel_groups:
        if len(group) > 1:
            opportunities.append({
                "task_ids": group,
                "reason": "Cùng ES date và không phụ thuộc nhau",
                "potential_time_saving": "Có thể tiết kiệm thời gian bằng cách chạy song song"
            })
    
    return opportunities

