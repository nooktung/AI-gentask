from .retriever import retrieve_docs
from .llm_generator import generate_wbs
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta


def _assign_people(num: int) -> List[str]:
    names = [
        "Trần Khánh Tùng",
        "Nguyễn Minh Anh",
        "Phạm Thu Trang",
        "Lê Hoàng Nam",
        "Bùi Hải Yến",
        "Đặng Quang Huy",
        "Hoàng Thuỳ Linh",
        "Vũ Đức Long",
    ]
    out = []
    for i in range(num):
        out.append(names[i % len(names)])
    return out


def _epic_title_and_desc(department: str) -> Tuple[str, str]:
    mapping: Dict[str, Tuple[str, str]] = {
        "Hậu cần": ("Điều phối vận hành & hậu cần", "Quản lý hạ tầng, vật tư, vận chuyển, an ninh hiện trường, phối hợp nhà cung cấp"),
        "Logistics": ("Điều phối vận hành & hậu cần", "Quản lý hạ tầng, vật tư, vận chuyển, an ninh hiện trường, phối hợp nhà cung cấp"),
        "Media": ("Triển khai truyền thông & marketing", "Key Visual, ấn phẩm, kế hoạch truyền thông đa kênh, triển khai social và quảng cáo"),
        "Marketing": ("Triển khai truyền thông & marketing", "Key Visual, ấn phẩm, kế hoạch truyền thông đa kênh, triển khai social và quảng cáo"),
        "Media/Marketing": ("Triển khai truyền thông & marketing", "Key Visual, ấn phẩm, kế hoạch truyền thông đa kênh, triển khai social và quảng cáo"),
        "Đối ngoại": ("Làm việc với nghệ sĩ & đối tác", "Liên hệ, đàm phán, hợp đồng nghệ sĩ/đối tác, quản lý rider và lịch trình"),
        "Doi ngoai": ("Làm việc với nghệ sĩ & đối tác", "Liên hệ, đàm phán, hợp đồng nghệ sĩ/đối tác, quản lý rider và lịch trình"),
        "Tài chính": ("Quản lý tài chính sự kiện", "Ngân sách, hợp đồng mua sắm/dịch vụ, thanh toán, quyết toán, kiểm soát chi phí"),
        "Tai chinh": ("Quản lý tài chính sự kiện", "Ngân sách, hợp đồng mua sắm/dịch vụ, thanh toán, quyết toán, kiểm soát chi phí"),
        "Finance": ("Quản lý tài chính sự kiện", "Ngân sách, hợp đồng mua sắm/dịch vụ, thanh toán, quyết toán, kiểm soát chi phí"),
    }
    title, desc = mapping.get(department, (f"Điều phối {department}", f"Điều phối công việc và nguồn lực cho ban {department}"))
    return title, desc


def _task_name_for(epic_title: str, seq: int) -> str:
    title = epic_title or "Công việc"
    presets: Dict[str, List[str]] = {
        "Truyền thông & Marketing": [
            "Lập kế hoạch truyền thông",
            "Thiết kế key visual",
            "Triển khai chiến dịch",
            "Theo dõi hiệu quả",
        ],
        "Vận hành & Hậu cần": [
            "Khảo sát hiện trường",
            "Lập phương án vận hành",
            "Chuẩn bị vật tư",
            "Bố trí nhân sự",
        ],
        "Nghệ sĩ & Đối tác": [
            "Liên hệ nghệ sĩ",
            "Đàm phán điều khoản",
            "Ký hợp đồng nghệ sĩ",
            "Sắp xếp lịch trình",
        ],
        "Quản lý tài chính": [
            "Lập dự trù ngân sách",
            "Phê duyệt chi phí",
            "Theo dõi thanh toán",
            "Quyết toán sự kiện",
        ],
    }
    verbs = presets.get(title, [
        "Lập kế hoạch",
        "Triển khai",
        "Kiểm tra chất lượng",
        "Báo cáo tổng kết",
    ])
    base = verbs[seq % len(verbs)]
    # Ensure action is specific to the epic context
    if title not in base:
        return f"{base} - {title}"
    return base


def _action_templates_for_epic(title: str) -> List[Dict[str, str]]:
    """Return standardized actions with description and priority for a given epic title."""
    templates: Dict[str, List[Dict[str, str]]] = {
        "Truyền thông & Marketing": [
            {"name": "Lập kế hoạch truyền thông", "description": "Xác định mục tiêu, kênh, timeline truyền thông", "priority": "high"},
            {"name": "Thiết kế key visual", "description": "Thiết kế chủ đạo cho toàn bộ ấn phẩm", "priority": "medium"},
            {"name": "Triển khai chiến dịch", "description": "Đăng tải nội dung, chạy quảng cáo theo kế hoạch", "priority": "medium"},
            {"name": "Theo dõi hiệu quả", "description": "Theo dõi KPI, tối ưu ngân sách và nội dung", "priority": "low"},
        ],
        "Vận hành & Hậu cần": [
            {"name": "Khảo sát hiện trường", "description": "Đo đạc, đánh giá hạ tầng, điểm đặt thiết bị", "priority": "high"},
            {"name": "Lập phương án vận hành", "description": "Phân luồng, phương án an toàn, checklist vận hành", "priority": "high"},
            {"name": "Chuẩn bị vật tư", "description": "Sắp xếp vật tư, kho bãi, phương tiện vận chuyển", "priority": "medium"},
            {"name": "Bố trí nhân sự", "description": "Phân công ca làm, briefing nhiệm vụ", "priority": "low"},
        ],
        "Nghệ sĩ & Đối tác": [
            {"name": "Liên hệ nghệ sĩ", "description": "Tiếp cận danh sách nghệ sĩ mục tiêu", "priority": "medium"},
            {"name": "Đàm phán điều khoản", "description": "Thống nhất cát-xê, điều khoản kỹ thuật", "priority": "high"},
            {"name": "Ký hợp đồng nghệ sĩ", "description": "Hoàn tất thủ tục pháp lý, chữ ký", "priority": "high"},
            {"name": "Sắp xếp lịch trình", "description": "Lên lịch di chuyển, rehearsal, biểu diễn", "priority": "medium"},
        ],
        "Quản lý tài chính": [
            {"name": "Lập dự trù ngân sách", "description": "Xây dựng ngân sách theo hạng mục", "priority": "high"},
            {"name": "Phê duyệt chi phí", "description": "Trình phê duyệt các đề nghị chi", "priority": "medium"},
            {"name": "Theo dõi thanh toán", "description": "Theo dõi tiến độ thanh toán nhà cung cấp", "priority": "medium"},
            {"name": "Quyết toán sự kiện", "description": "Tổng hợp chứng từ, báo cáo quyết toán", "priority": "low"},
        ],
    }
    return templates.get(title, [
        {"name": "Lập kế hoạch", "description": "Xác định mục tiêu và phạm vi công việc", "priority": "high"},
        {"name": "Triển khai", "description": "Thực hiện công việc theo kế hoạch", "priority": "medium"},
        {"name": "Kiểm tra chất lượng", "description": "Đánh giá kết quả, khắc phục lỗi", "priority": "medium"},
        {"name": "Báo cáo tổng kết", "description": "Tổng hợp kết quả và bài học kinh nghiệm", "priority": "low"},
    ])


def _duration_days_for_priority(priority: str) -> int:
    if priority == "high":
        return 3
    if priority == "medium":
        return 2
    return 1


def run_pipeline(event_input: dict) -> Dict[str, Any]:
    # Retrieve KB and generate MINIMAL epics (1 per department)
    retrieved = retrieve_docs(event_input)
    full = generate_wbs(event_input, retrieved)

    epics = full.get("epics", [])

    # Ensure epic count equals number of departments with generalized titles/descriptions
    departments = event_input.get("departments") or []
    if len(epics) != len(departments):
        epics = []
        for idx, dept in enumerate(departments, start=1):
            title, desc = _epic_title_and_desc(dept)
            epics.append({
                "epic_id": f"EP-{idx:03d}",
                "name": title,
                "department": dept,
                "description": desc,
            })
    else:
        # Rewrite names/descriptions even if counts match
        updated = []
        for e in epics:
            dept = e.get("department") or e.get("name")
            title, desc = _epic_title_and_desc(str(dept))
            updated.append({
                "epic_id": e.get("epic_id"),
                "name": title,
                "department": dept,
                "description": desc,
            })
        epics = updated

    # Create exactly headcount_total tasks, distribute across epics with parallelizable phases
    headcount = int(event_input.get("headcount_total") or 0)
    owners = _assign_people(headcount)
    event_date = event_input.get("event_date")
    plan_start = event_input.get("start_date") or event_input.get("start-date")
    try:
        ev_dt = datetime.strptime(event_date, "%Y-%m-%d")
    except Exception:
        ev_dt = datetime.utcnow()
    ps_dt = None
    if plan_start:
        try:
            ps_dt = datetime.strptime(plan_start, "%Y-%m-%d")
        except Exception:
            ps_dt = None

    # Build actions per epic, then interleave to reach headcount_total
    per_epic_actions: Dict[str, List[Dict[str, str]]] = {}
    for e in epics:
        per_epic_actions[e["epic_id"]] = _action_templates_for_epic(e["name"])[:]

    # Compose tasks with unique names and richer fields
    tasks_out: List[Dict[str, Any]] = []
    used_names: set = set()
    i = 0
    while len(tasks_out) < headcount:
        epic = epics[i % len(epics)] if epics else {"epic_id": "EP-001", "name": ""}
        epic_id = epic.get("epic_id")
        epic_title = epic.get("name", "")
        action_list = per_epic_actions.get(epic_id) or _action_templates_for_epic(epic_title)
        action = action_list[(len([t for t in tasks_out if t["epic_id"] == epic_id])) % len(action_list)]

        base_name = action["name"]
        # Ensure unique task names across the whole plan
        name = base_name
        suffix = 2
        while name in used_names:
            name = f"{base_name} #{suffix}"
            suffix += 1
        used_names.add(name)

        priority = action.get("priority", "medium")
        duration_days = _duration_days_for_priority(priority)
        # Compute start/finish dates: place tasks in the window up to event date, longer tasks start earlier
        idx_from_end = headcount - len(tasks_out)
        # If user provides a plan start, schedule forward from it; otherwise schedule backward from event date
        if ps_dt:
            start_date = (ps_dt + timedelta(days=(len(tasks_out)))).strftime("%Y-%m-%d")
        else:
            start_date = (ev_dt - timedelta(days=idx_from_end + duration_days - 1)).strftime("%Y-%m-%d")
        deadline = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=duration_days - 1)).strftime("%Y-%m-%d")

        # Dependencies: allow fan-in from previous two tasks within the same epic if available
        same_epic_tasks = [t for t in tasks_out if t["epic_id"] == epic_id]
        depends_on_ids = []
        if same_epic_tasks:
            depends_on_ids.append(same_epic_tasks[-1]["task_id"])  # immediate predecessor
            if len(same_epic_tasks) >= 2:
                depends_on_ids.append(same_epic_tasks[-2]["task_id"])  # one more to create multiple deps

        tasks_out.append({
            "task_id": f"T-{len(tasks_out)+1:03d}",
            "epic_id": epic_id,
            "name": name,
            "category": epic_title,
            "description": action.get("description", ""),
            "priority": priority,
            "start-date": start_date,
            "deadline": deadline,
            "assign": owners[len(tasks_out)] if len(tasks_out) < len(owners) else owners[len(tasks_out) % len(owners)] if owners else "",
            "depends_on": depends_on_ids,
        })
        i += 1

    # Compute epic start/end from its tasks
    epics_out: List[Dict[str, Any]] = []
    for e in epics:
        etasks = [t for t in tasks_out if t["epic_id"] == e["epic_id"]]
        dates = [t["deadline"] for t in etasks if t.get("deadline")]
        start_date = min(dates) if dates else None
        end_date = max(dates) if dates else None
        epics_out.append({
            "epic_id": e.get("epic_id"),
            "name": e.get("name"),
            "start-date": start_date,
            "end-date": end_date,
            "department": e.get("department"),
            "description": e.get("description"),
        })

    return {"epics task": epics_out, "tasks": tasks_out}
