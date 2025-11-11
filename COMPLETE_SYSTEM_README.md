# Complete WBS System - Hệ thống WBS đầy đủ

## Tổng quan

Hệ thống này tích hợp 3 giải pháp chính để giải quyết các vấn đề được nêu ra:

1. **Dynamic Task Generation + Complexity** - Phân công người thực tế
2. **CPM/Critical Path Method** - Timeline tối ưu
3. **Full RAG + LLM + Dependency Analysis** - Task generation theo context

## Cấu trúc Modules

### 1. Task Complexity (`services/task_complexity.py`)

Tính toán độ phức tạp và `suggested_team_size` cho từng task.

**Chức năng:**
- `calculate_task_complexity()` - Tính complexity dựa trên priority, venue tier, dependencies, duration
- `calculate_suggested_team_size()` - Tính team size (1-5) dựa trên complexity
- `get_complexity_weight()` - Trọng số để phân bổ nhân lực

**Sử dụng:**
```python
from services.task_complexity import calculate_task_complexity, calculate_suggested_team_size
from services.venue_classifier import VenueTier

complexity = calculate_task_complexity(
    task={"priority": "high", "duration_days": 3, "name": "Setup sân khấu"},
    venue_tier=VenueTier.L,
    event_type="concert_opening"
)

team_size = calculate_suggested_team_size(
    complexity=complexity,
    duration_days=3,
    venue_tier=VenueTier.L
)
```

### 2. Priority Classifier (`services/priority_classifier.py`)

Phân loại priority dựa trên rule-based và context-based.

**Chức năng:**
- `classify_priority_rule_based()` - Phân loại theo keywords
- `classify_priority_context_based()` - Phân loại theo context (venue, dependencies, deadline)
- `classify_priority_hybrid()` - Kết hợp cả hai

**Sử dụng:**
```python
from services.priority_classifier import classify_priority_hybrid

priority = classify_priority_hybrid(
    task={"name": "Ký hợp đồng", "description": "..."},
    event_context={"venue_tier": "XL", "event_type": "concert"},
    all_tasks=tasks,
    critical_path_tasks={"T-001", "T-002"}
)
```

### 3. Dependency Analyzer (`services/dependency_analyzer.py`)

Phân tích 4 nhóm dependencies: Logical, Resource, Preferential, Time-based.

**Chức năng:**
- `analyze_dependencies()` - Phân tích tất cả dependencies
- `build_dependency_graph()` - Xây dependency graph
- `topological_sort()` - Sắp xếp thứ tự tasks
- `find_parallel_tasks()` - Tìm tasks có thể chạy song song

**Sử dụng:**
```python
from services.dependency_analyzer import analyze_dependencies

dependency_analysis = analyze_dependencies(tasks, event_context)

# Kết quả:
# - dependency_graph: {task_id: [dep_task_ids]}
# - dependency_types: {task_id: {dep_task_id: "logical|resource|preferential|time_based"}}
# - lead_times: {task_id: {dep_task_id: days}}
# - dependency_chains: List các chains
# - cycles: List cycles (nếu có)
```

### 4. Dynamic Task Generator (`services/dynamic_task_generator.py`)

Tạo tasks với dynamic team sizing và ràng buộc.

**Ràng buộc:**
- `sum(suggested_team_size) = headcount_total - 1(HOOC) - số_ban(HODs)`
- `1 ≤ suggested_team_size ≤ 5` cho mỗi task

**Chức năng:**
- `calculate_available_workers()` - Tính workers khả dụng
- `assign_team_sizes_to_tasks()` - Gán team size với ràng buộc
- `expand_tasks_if_needed()` - Expand tasks nếu quá ít
- `merge_tasks_if_needed()` - Merge tasks nếu quá nhiều

**Sử dụng:**
```python
from services.dynamic_task_generator import assign_team_sizes_to_tasks

tasks_with_size, stats = assign_team_sizes_to_tasks(
    tasks=tasks,
    available_workers=95,  # 100 - 1(HOOC) - 4(HODs)
    venue_tier=VenueTier.XL,
    event_context=event_context,
    dependency_analysis=dependency_analysis
)

# stats chứa:
# - total_team_size: Tổng team size
# - available_workers: Workers khả dụng
# - is_balanced: Có khớp không
# - adjustments: Các điều chỉnh đã thực hiện
```

### 5. CPM Scheduler (`modules/wbs/cpm_scheduler.py`)

Tính CPM đầy đủ: ES/EF, LS/LF, Slack, Critical Path.

**Chức năng:**
- `calculate_cpm()` - Tính CPM đầy đủ
- `detect_parallel_opportunities()` - Phát hiện cơ hội chạy song song

**Sử dụng:**
```python
from modules.wbs.cpm_scheduler import calculate_cpm

cpm_result = calculate_cpm(
    tasks=tasks,
    event_date="2025-12-25"
)

# Kết quả:
# - tasks_with_cpm: Tasks có ES/EF/LS/LF/Slack
# - critical_path: List task_ids trên critical path
# - parallel_groups: Các nhóm tasks có thể chạy song song
# - project_duration: Tổng thời gian dự án
```

### 6. Complete WBS System (`services/complete_wbs_system.py`)

Tích hợp tất cả modules.

**Sử dụng:**
```python
from services.complete_wbs_system import generate_complete_wbs

event_input = {
    "event_name": "Concert Khai Giảng",
    "event_type": "concert_opening",
    "event_date": "2025-12-25",
    "venue": "Đường 30m FPT",
    "headcount_total": 100,
    "departments": ["Hậu cần", "Marketing", "Chuyên môn", "Tài chính"]
}

wbs = generate_complete_wbs(event_input)

# Kết quả bao gồm:
# - epics: List epics
# - tasks: Tasks với suggested_team_size, ES/EF/LS/LF/Slack, complexity, priority
# - sizing_stats: Thống kê phân bổ nhân lực
# - cpm: Kết quả CPM
# - dependency_analysis: Phân tích dependencies
# - parallel_opportunities: Cơ hội chạy song song
# - summary: Tóm tắt
```

## Workflow

1. **Generate Tasks** - Tạo tasks từ templates
2. **Resolve Dependencies** - Chuyển dependencies từ names sang IDs
3. **Dependency Analysis** - Phân tích 4 nhóm dependencies
4. **Priority Classification** - Phân loại priority (rule + context)
5. **Complexity Calculation** - Tính complexity và suggested_team_size
6. **Team Size Assignment** - Gán team size với ràng buộc
7. **CPM Scheduling** - Tính ES/EF/LS/LF/Slack và critical path
8. **Update Priority** - Cập nhật lại priority với critical path
9. **Parallel Detection** - Phát hiện cơ hội chạy song song

## Ràng buộc

### Team Size
- `sum(suggested_team_size) = headcount_total - 1(HOOC) - số_ban(HODs)`
- `1 ≤ suggested_team_size ≤ 5` cho mỗi task

### Dependencies
- 4 nhóm: Logical, Resource, Preferential, Time-based
- Topological sort để sắp xếp thứ tự
- Phát hiện cycles

### CPM
- Forward pass: ES = max(EF của predecessors), EF = ES + duration - 1
- Backward pass: LF = min(LS của successors), LS = LF - duration + 1
- Slack = LS - ES = LF - EF
- Critical path: Tasks có slack = 0

## Ví dụ Output

```json
{
  "status": "ok",
  "epics": [...],
  "tasks": [
    {
      "task_id": "T-001",
      "name": "Khảo sát địa điểm",
      "suggested_team_size": 2,
      "complexity": "high",
      "priority": "high",
      "ES": "2025-12-01",
      "EF": "2025-12-02",
      "LS": "2025-12-01",
      "LF": "2025-12-02",
      "slack": 0,
      "is_critical": true
    }
  ],
  "sizing_stats": {
    "total_team_size": 95,
    "available_workers": 95,
    "is_balanced": true
  },
  "cpm": {
    "critical_path": ["T-001", "T-002", "T-015"],
    "project_duration": 30
  }
}
```

## Tích hợp với hệ thống hiện tại

Để sử dụng với API hiện tại:

```python
from services.complete_wbs_system import generate_wbs_legacy_compatible

# Tương thích với format cũ
wbs = generate_wbs_legacy_compatible(event_input)
```

## Lưu ý

1. **Dependencies**: Tasks ban đầu có `depends_on` là names, cần resolve sang IDs
2. **Critical Path**: Được tính từ CPM, không phải từ dependency_analysis
3. **Team Size**: Được điều chỉnh tự động để khớp với available_workers
4. **Priority**: Được cập nhật 2 lần (trước và sau CPM)

## Testing

Chạy test từng module:

```bash
# Test task complexity
python -m services.task_complexity

# Test priority classifier
python -m services.priority_classifier

# Test dependency analyzer
python -m services.dependency_analyzer

# Test dynamic task generator
python -m services.dynamic_task_generator

# Test CPM scheduler
python -m modules.wbs.cpm_scheduler

# Test complete system
python -m services.complete_wbs_system
```



