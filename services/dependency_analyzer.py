"""
Dependency Analyzer
Phân tích 4 nhóm phụ thuộc: Logical, Resource, Preferential, Time-based
"""

from typing import Dict, Any, List, Set, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque


class DependencyType:
    """Các loại dependency"""
    LOGICAL = "logical"          # Logic: thiết kế → lắp đặt
    RESOURCE = "resource"         # Resource: chung người/thiết bị/địa điểm
    PREFERENTIAL = "preferential"  # Best practice: ký hợp đồng trước quảng cáo
    TIME_BASED = "time_based"     # Lead time: giấy phép 30 ngày


def analyze_dependencies(
    tasks: List[Dict[str, Any]],
    event_context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Phân tích dependencies cho tất cả tasks
    
    Args:
        tasks: List các task dictionaries
        event_context: Context của event (venue, event_type, etc.)
        
    Returns:
        Dict với:
        - dependency_graph: {task_id: [dep_task_ids]}
        - dependency_types: {task_id: {dep_task_id: DependencyType}}
        - lead_times: {task_id: {dep_task_id: days}}
        - dependency_chains: List các chains
    """
    task_dict = {t["task_id"]: t for t in tasks}
    
    # Build dependency graph
    dependency_graph = defaultdict(list)
    dependency_types = defaultdict(dict)
    lead_times = defaultdict(dict)
    
    for task in tasks:
        task_id = task["task_id"]
        depends_on = task.get("depends_on", [])
        
        for dep_id in depends_on:
            if dep_id in task_dict:
                dependency_graph[task_id].append(dep_id)
                
                # Phân loại dependency type
                dep_type = _classify_dependency_type(
                    task, task_dict[dep_id], event_context
                )
                dependency_types[task_id][dep_id] = dep_type
                
                # Tính lead time nếu là time-based
                if dep_type == DependencyType.TIME_BASED:
                    lead_time = _calculate_lead_time(
                        task, task_dict[dep_id], event_context
                    )
                    lead_times[task_id][dep_id] = lead_time
    
    # Tìm dependency chains
    chains = _find_dependency_chains(dependency_graph, task_dict)
    
    # Detect cycles
    cycles = _detect_cycles(dependency_graph)
    
    return {
        "dependency_graph": dict(dependency_graph),
        "dependency_types": dict(dependency_types),
        "lead_times": dict(lead_times),
        "dependency_chains": chains,
        "cycles": cycles,
        "has_cycles": len(cycles) > 0
    }


def _classify_dependency_type(
    task: Dict[str, Any],
    dep_task: Dict[str, Any],
    event_context: Dict[str, Any] = None
) -> str:
    """
    Phân loại loại dependency giữa task và dep_task
    
    Returns:
        DependencyType: logical, resource, preferential, time_based
    """
    task_name = task.get("name", "").lower()
    dep_name = dep_task.get("name", "").lower()
    
    # Logical dependencies (thiết kế → lắp đặt, xin phép → triển khai)
    logical_patterns = [
        ("thiết kế", "lắp đặt"), ("design", "install"),
        ("khảo sát", "thiết kế"), ("survey", "design"),
        ("xin phép", "triển khai"), ("permit", "implement"),
        ("phê duyệt", "thực hiện"), ("approval", "execute"),
        ("test", "tổng duyệt"), ("test", "final")
    ]
    
    for pattern in logical_patterns:
        if pattern[0] in dep_name and pattern[1] in task_name:
            return DependencyType.LOGICAL
    
    # Resource dependencies (chung người/thiết bị/địa điểm)
    resource_keywords = ["thiết bị", "equipment", "người", "person", "địa điểm", "venue"]
    if any(kw in task_name for kw in resource_keywords) and \
       any(kw in dep_name for kw in resource_keywords):
        return DependencyType.RESOURCE
    
    # Preferential/Best practice (ký hợp đồng trước quảng cáo)
    preferential_patterns = [
        ("hợp đồng", "quảng cáo"), ("contract", "advertising"),
        ("ký kết", "triển khai"), ("sign", "implement"),
        ("phê duyệt", "chi tiêu"), ("approval", "spend")
    ]
    
    for pattern in preferential_patterns:
        if pattern[0] in dep_name and pattern[1] in task_name:
            return DependencyType.PREFERENTIAL
    
    # Time-based (giấy phép 30 ngày, in ấn 2-3 ngày)
    time_keywords = ["giấy phép", "permit", "in ấn", "printing", "sản xuất", "production"]
    if any(kw in dep_name for kw in time_keywords):
        return DependencyType.TIME_BASED
    
    # Default: logical
    return DependencyType.LOGICAL


def _calculate_lead_time(
    task: Dict[str, Any],
    dep_task: Dict[str, Any],
    event_context: Dict[str, Any] = None
) -> int:
    """
    Tính lead time (số ngày cần thiết) cho time-based dependencies
    
    Returns:
        Số ngày lead time
    """
    dep_name = dep_task.get("name", "").lower()
    
    # Lead times mặc định theo loại task
    lead_times = {
        "giấy phép": 30,
        "permit": 30,
        "approval": 14,
        "phê duyệt": 14,
        "in ấn": 3,
        "printing": 3,
        "sản xuất": 5,
        "production": 5,
        "hợp đồng": 7,
        "contract": 7
    }
    
    for keyword, days in lead_times.items():
        if keyword in dep_name:
            return days
    
    # Default: duration của dep_task
    return dep_task.get("duration_days", 1)


def _find_dependency_chains(
    dependency_graph: Dict[str, List[str]],
    task_dict: Dict[str, Dict[str, Any]]
) -> List[List[str]]:
    """
    Tìm các dependency chains (đường dẫn phụ thuộc)
    
    Returns:
        List các chains (mỗi chain là list task_ids)
    """
    chains = []
    visited = set()
    
    def dfs(node: str, current_chain: List[str]):
        if node in visited:
            return
        
        visited.add(node)
        current_chain.append(node)
        
        # Nếu không có dependencies, đây là đầu chain
        if node not in dependency_graph or not dependency_graph[node]:
            if len(current_chain) > 1:
                chains.append(current_chain.copy())
        else:
            for dep in dependency_graph[node]:
                dfs(dep, current_chain)
        
        current_chain.pop()
        visited.remove(node)
    
    # Tìm chains từ các tasks không có dependencies
    for task_id in task_dict.keys():
        if task_id not in dependency_graph or not dependency_graph[task_id]:
            dfs(task_id, [])
    
    return chains


def _detect_cycles(dependency_graph: Dict[str, List[str]]) -> List[List[str]]:
    """
    Phát hiện cycles trong dependency graph
    
    Returns:
        List các cycles (mỗi cycle là list task_ids)
    """
    cycles = []
    visited = set()
    rec_stack = set()
    
    def dfs(node: str, path: List[str]):
        if node in rec_stack:
            # Tìm thấy cycle
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            cycles.append(cycle)
            return
        
        if node in visited:
            return
        
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for dep in dependency_graph.get(node, []):
            dfs(dep, path)
        
        rec_stack.remove(node)
        path.pop()
    
    for node in dependency_graph.keys():
        if node not in visited:
            dfs(node, [])
    
    return cycles


def build_dependency_graph(tasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Xây dựng dependency graph từ tasks
    
    Returns:
        Dict {task_id: [dep_task_ids]}
    """
    graph = defaultdict(list)
    
    for task in tasks:
        task_id = task.get("task_id")
        depends_on = task.get("depends_on", [])
        graph[task_id] = depends_on
    
    return dict(graph)


def topological_sort(dependency_graph: Dict[str, List[str]]) -> List[str]:
    """
    Topological sort để sắp xếp thứ tự tasks
    
    Returns:
        List task_ids theo thứ tự thực hiện
    """
    # Tính in-degree
    in_degree = defaultdict(int)
    for task_id, deps in dependency_graph.items():
        in_degree[task_id] = len(deps)
        for dep in deps:
            if dep not in in_degree:
                in_degree[dep] = 0
    
    # BFS từ các nodes có in-degree = 0
    queue = deque([node for node, degree in in_degree.items() if degree == 0])
    result = []
    
    while queue:
        node = queue.popleft()
        result.append(node)
        
        # Giảm in-degree của các nodes phụ thuộc vào node này
        for task_id, deps in dependency_graph.items():
            if node in deps:
                in_degree[task_id] -= 1
                if in_degree[task_id] == 0:
                    queue.append(task_id)
    
    return result


def find_parallel_tasks(
    tasks: List[Dict[str, Any]],
    dependency_graph: Dict[str, List[str]]
) -> List[List[str]]:
    """
    Tìm các tasks có thể chạy song song
    
    Returns:
        List các nhóm tasks có thể chạy song song
    """
    # Tasks không có dependencies hoặc dependencies đã hoàn thành → có thể song song
    parallel_groups = []
    
    # Group theo level (tasks cùng level có thể song song)
    levels = defaultdict(list)
    task_level = {}
    
    def calculate_level(task_id: str) -> int:
        if task_id in task_level:
            return task_level[task_id]
        
        deps = dependency_graph.get(task_id, [])
        if not deps:
            level = 0
        else:
            level = max(calculate_level(dep) for dep in deps) + 1
        
        task_level[task_id] = level
        return level
    
    for task in tasks:
        task_id = task.get("task_id")
        level = calculate_level(task_id)
        levels[level].append(task_id)
    
    # Mỗi level là một nhóm song song
    for level in sorted(levels.keys()):
        if len(levels[level]) > 1:
            parallel_groups.append(levels[level])
    
    return parallel_groups



