# services/llm_generator.py
import os, json
from typing import List, Dict, Any, Tuple
from datetime import datetime
from dotenv import load_dotenv
from contextlib import suppress

try:
    from openai import OpenAI  # openai>=1.40.0
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
USE_LLM = os.getenv("USE_LLM", "0") in ("1", "true", "True")


def _gen_ids(n_epic: int, n_task: int) -> Tuple[List[str], List[str]]:
    epic_ids = [f"EP-{i:03d}" for i in range(1, n_epic + 1)]
    task_ids = [f"T-{i:03d}" for i in range(1, n_task + 1)]
    return epic_ids, task_ids


def _event_id(ev_date: str) -> str:
    # No longer used; kept for backward compatibility if imported elsewhere
    ymd = ev_date.replace("-", "")
    return f"EVT-{ymd}-{datetime.now().strftime('%H%M%S')}"


def _size_multiplier(headcount: int) -> float:
    # Deprecated: durations are not surfaced in output anymore
    return 1.0


def _templates_for_event_type(event_type: str) -> Dict[str, Any]:
    """Event type templates with comprehensive epic and task catalogs"""
    
    if event_type == "concert_opening":
        return {
            "epics": [
                ("Sân khấu & Âm thanh", "Hậu cần", "Hạ tầng sân khấu, âm thanh, ánh sáng, tổng duyệt"),
                ("Nghệ sĩ & Đối tác", "Đối ngoại", "Booking nghệ sĩ, hợp đồng, rider kỹ thuật"),
                ("Truyền thông & Marketing", "Media/Marketing", "KV, ấn phẩm, chiến dịch đa kênh"),
                ("An ninh & Soát vé", "Chuyên môn", "Phân luồng, cổng soát vé, an ninh"),
                ("Tài chính", "Tài chính", "Ngân sách, hợp đồng, thanh toán, quyết toán"),
                ("Vận hành sân khấu", "Truyền thông sân khấu", "Rundown, cue sheet, tổng duyệt"),
                ("Hậu cần tổng", "Hậu cần", "Vật tư, nước uống, kho bãi, phương tiện"),
                ("Catering & F&B", "Hậu cần", "Đồ ăn thức uống, dịch vụ khách hàng"),
                ("Logistics & Transport", "Hậu cần", "Vận chuyển, bốc xếp, phương tiện"),
                ("IT & Technical", "Chuyên môn", "Hệ thống IT, streaming, backup"),
            ],
            "milestones": [
                "Contracts Signed",
                "Key Visual Approved", 
                "Vendor List Locked",
                "Final Rehearsal Complete",
                "Doors Open",
            ],
        }
    elif event_type == "food_festival":
        return {
            "epics": [
                ("Food Safety & Compliance", "Chuyên môn", "An toàn thực phẩm, giấy phép, kiểm tra"),
                ("Vendor Management", "Đối ngoại", "Tuyển chọn vendor, hợp đồng, quản lý"),
                ("Layout & Infrastructure", "Hậu cần", "Thiết kế layout, điện nước, gian hàng"),
                ("Marketing & Promotion", "Media/Marketing", "Quảng bá, social media, ấn phẩm"),
                ("Security & Crowd Control", "Chuyên môn", "An ninh, phân luồng, kiểm soát"),
                ("Finance & Budget", "Tài chính", "Ngân sách, thu chi, báo cáo"),
                ("Waste Management", "Hậu cần", "Xử lý rác thải, vệ sinh môi trường"),
                ("Entertainment & Activities", "Nội dung", "Chương trình giải trí, hoạt động"),
            ],
            "milestones": [
                "Vendor Contracts Signed",
                "Layout Approved",
                "Health Permits Obtained", 
                "Setup Complete",
                "Festival Opens",
            ],
        }
    elif event_type == "conference":
        return {
            "epics": [
                ("Agenda & Speakers", "Nội dung", "Lên lịch trình, mời diễn giả, nội dung"),
                ("Venue & Facilities", "Hậu cần", "Đặt venue, trang thiết bị, phòng họp"),
                ("Registration & Check-in", "Hậu cần", "Đăng ký, check-in, quản lý khách"),
                ("Sponsor Management", "Đối ngoại", "Tìm kiếm sponsor, hợp đồng, quản lý"),
                ("A/V & Streaming", "Chuyên môn", "Âm thanh, hình ảnh, livestream"),
                ("Marketing & PR", "Media/Marketing", "Quảng bá, PR, media kit"),
                ("Catering & Hospitality", "Hậu cần", "Đồ ăn, nước uống, tiếp đãi"),
                ("Documentation & Materials", "Nội dung", "Tài liệu, name tag, swag"),
            ],
            "milestones": [
                "Speaker Lineup Confirmed",
                "Venue Booked",
                "Registration Opens",
                "Final Agenda Published",
                "Conference Starts",
            ],
        }
    elif event_type == "sport_competition":
        return {
            "epics": [
                ("Athlete Management", "Chuyên môn", "Đăng ký vận động viên, phân loại, lịch thi đấu"),
                ("Venue & Equipment", "Hậu cần", "Sân bãi, trang thiết bị, an toàn"),
                ("Referees & Officials", "Chuyên môn", "Trọng tài, ban giám khảo, quy tắc"),
                ("Medical & Safety", "Chuyên môn", "Y tế, sơ cứu, an toàn"),
                ("Awards & Recognition", "Nội dung", "Giải thưởng, trao huy chương, lễ bế mạc"),
                ("Media & Broadcasting", "Media/Marketing", "Quay phim, livestream, báo chí"),
                ("Crowd Management", "Chuyên môn", "Kiểm soát đám đông, an ninh"),
                ("Logistics & Transport", "Hậu cần", "Vận chuyển, bốc xếp, phương tiện"),
            ],
            "milestones": [
                "Registration Closed",
                "Equipment Ready",
                "Medical Team On-site",
                "Competition Starts",
                "Awards Ceremony",
            ],
        }
    # default generic
    return {
        "epics": [
            ("Planning & Coordination", "Nội dung", "Kế hoạch tổng thể và điều phối"),
            ("Operations & Logistics", "Hậu cần", "Vận hành và logistics"),
            ("Marketing & Communication", "Media/Marketing", "Truyền thông và tiếp thị"),
            ("Finance & Budget", "Tài chính", "Tài chính và ngân sách"),
            ("Technical & IT", "Chuyên môn", "Kỹ thuật và công nghệ"),
        ],
        "milestones": ["Plan Approved", "Setup Complete", "Event Starts"],
    }


def _seed_tasks_for_epic(epic_name: str) -> List[Tuple[str, int, List[str], bool, bool]]:
    """Comprehensive task catalog for each epic type"""
    catalog: Dict[str, List[Tuple[str, int, List[str], bool, bool]]] = {
        # Concert Opening Tasks
        "Sân khấu & Âm thanh": [
            ("Khảo sát địa điểm & đo đạc", 2, [], False, False),
            ("Thiết kế sân khấu 3D", 3, ["Khảo sát địa điểm & đo đạc"], False, False),
            ("Thiết kế ánh sáng & âm thanh", 2, ["Thiết kế sân khấu 3D"], False, False),
            ("Thuê thiết bị âm thanh", 2, ["Thiết kế ánh sáng & âm thanh"], False, False),
            ("Thuê thiết bị ánh sáng", 2, ["Thiết kế ánh sáng & âm thanh"], False, False),
            ("Lắp đặt sân khấu", 2, ["Thuê thiết bị âm thanh", "Thuê thiết bị ánh sáng"], False, False),
            ("Chạy dây & kết nối", 1, ["Lắp đặt sân khấu"], False, False),
            ("Test âm thanh", 1, ["Chạy dây & kết nối"], False, False),
            ("Test ánh sáng", 1, ["Chạy dây & kết nối"], False, False),
            ("Soundcheck tổng", 0, ["Test âm thanh", "Test ánh sáng"], False, True),
        ],
        "Nghệ sĩ & Đối tác": [
            ("Research & shortlist nghệ sĩ", 3, [], False, False),
            ("Liên hệ & đàm phán", 5, ["Research & shortlist nghệ sĩ"], False, False),
            ("Ký hợp đồng nghệ sĩ", 2, ["Liên hệ & đàm phán"], False, False),
            ("Thu thập rider kỹ thuật", 2, ["Ký hợp đồng nghệ sĩ"], False, False),
            ("Đặt phòng & dịch vụ", 1, ["Ký hợp đồng nghệ sĩ"], True, False),
            ("Arrangement & logistics", 3, ["Thu thập rider kỹ thuật"], False, False),
            ("Contracts Signed", 0, ["Ký hợp đồng nghệ sĩ"], False, True),
        ],
        "Truyền thông & Marketing": [
            ("Lên concept & brief", 2, [], False, False),
            ("Thiết kế Key Visual", 3, ["Lên concept & brief"], False, False),
            ("Thiết kế poster", 2, ["Thiết kế Key Visual"], True, False),
            ("Thiết kế banner", 1, ["Thiết kế Key Visual"], True, False),
            ("Thiết kế social media", 2, ["Thiết kế Key Visual"], True, False),
            ("Sản xuất video teaser", 3, ["Thiết kế Key Visual"], False, False),
            ("Triển khai social media", 5, ["Thiết kế social media"], True, False),
            ("Đặt quảng cáo", 2, ["Thiết kế poster"], True, False),
            ("Key Visual Approved", 0, ["Thiết kế Key Visual"], False, True),
        ],
        "An ninh & Soát vé": [
            ("Phân tích rủi ro", 1, [], False, False),
            ("Lập phương án an ninh", 2, ["Phân tích rủi ro"], False, False),
            ("Phương án phân luồng", 2, ["Lập phương án an ninh"], False, False),
            ("Setup cổng soát vé", 1, ["Phương án phân luồng"], False, False),
            ("Training nhân viên an ninh", 2, ["Setup cổng soát vé"], False, False),
            ("Test hệ thống an ninh", 1, ["Training nhân viên an ninh"], False, False),
        ],
        "Tài chính": [
            ("Lập dự trù ngân sách", 3, [], False, False),
            ("Phê duyệt ngân sách", 1, ["Lập dự trù ngân sách"], False, False),
            ("Hợp đồng mua sắm", 3, ["Phê duyệt ngân sách"], False, False),
            ("Hợp đồng dịch vụ", 2, ["Phê duyệt ngân sách"], True, False),
            ("Thanh toán tạm ứng", 2, ["Hợp đồng mua sắm"], False, False),
            ("Theo dõi chi phí", 5, ["Thanh toán tạm ứng"], True, False),
            ("Quyết toán cuối", 3, ["Theo dõi chi phí"], False, False),
            ("Contracts Signed", 0, ["Hợp đồng mua sắm", "Hợp đồng dịch vụ"], False, True),
        ],
        "Vận hành sân khấu": [
            ("Soạn rundown chi tiết", 2, [], False, False),
            ("Chuẩn bị cue sheet", 1, ["Soạn rundown chi tiết"], False, False),
            ("Chuẩn bị đạo cụ", 2, ["Soạn rundown chi tiết"], True, False),
            ("Training stage manager", 2, ["Chuẩn bị cue sheet"], False, False),
            ("Rehearsal với nghệ sĩ", 2, ["Training stage manager"], False, False),
            ("Tổng duyệt", 0, ["Rehearsal với nghệ sĩ", "Soundcheck tổng"], False, True),
        ],
        "Hậu cần tổng": [
            ("Lập danh sách vật tư", 1, [], False, False),
            ("Mua sắm vật tư tiêu hao", 2, ["Lập danh sách vật tư"], False, False),
            ("Chuẩn bị nước uống", 1, ["Lập danh sách vật tư"], True, False),
            ("Setup y tế", 1, ["Lập danh sách vật tư"], True, False),
            ("Quản lý kho bãi", 2, ["Mua sắm vật tư tiêu hao"], False, False),
            ("Vận chuyển & bốc xếp", 1, ["Quản lý kho bãi"], False, False),
        ],
        "Catering & F&B": [
            ("Lên menu & thực đơn", 2, [], False, False),
            ("Tìm nhà cung cấp F&B", 3, ["Lên menu & thực đơn"], False, False),
            ("Đặt hàng đồ ăn", 2, ["Tìm nhà cung cấp F&B"], False, False),
            ("Setup khu vực ăn uống", 1, ["Đặt hàng đồ ăn"], False, False),
            ("Chuẩn bị dụng cụ ăn uống", 1, ["Setup khu vực ăn uống"], True, False),
        ],
        "Logistics & Transport": [
            ("Lập kế hoạch vận chuyển", 2, [], False, False),
            ("Thuê phương tiện", 2, ["Lập kế hoạch vận chuyển"], False, False),
            ("Chuẩn bị bốc xếp", 1, ["Thuê phương tiện"], False, False),
            ("Vận chuyển thiết bị", 1, ["Chuẩn bị bốc xếp"], False, False),
        ],
        "IT & Technical": [
            ("Setup hệ thống IT", 2, [], False, False),
            ("Chuẩn bị streaming", 2, ["Setup hệ thống IT"], False, False),
            ("Test kết nối mạng", 1, ["Chuẩn bị streaming"], False, False),
            ("Backup & recovery", 1, ["Test kết nối mạng"], False, False),
        ],
        
        # Food Festival Tasks
        "Food Safety & Compliance": [
            ("Xin giấy phép an toàn thực phẩm", 5, [], False, False),
            ("Kiểm tra tiêu chuẩn vendor", 3, ["Xin giấy phép an toàn thực phẩm"], False, False),
            ("Training nhân viên an toàn", 2, ["Kiểm tra tiêu chuẩn vendor"], False, False),
            ("Setup khu vực kiểm tra", 1, ["Training nhân viên an toàn"], False, False),
        ],
        "Vendor Management": [
            ("Tuyển chọn vendor", 5, [], False, False),
            ("Đàm phán hợp đồng", 3, ["Tuyển chọn vendor"], False, False),
            ("Ký hợp đồng vendor", 2, ["Đàm phán hợp đồng"], False, False),
            ("Quản lý vendor", 10, ["Ký hợp đồng vendor"], False, False),
        ],
        "Layout & Infrastructure": [
            ("Thiết kế layout tổng thể", 3, [], False, False),
            ("Setup điện nước", 2, ["Thiết kế layout tổng thể"], False, False),
            ("Setup gian hàng", 3, ["Setup điện nước"], False, False),
            ("Setup khu vực chung", 2, ["Setup gian hàng"], True, False),
        ],
        
        # Conference Tasks  
        "Agenda & Speakers": [
            ("Lên lịch trình sơ bộ", 2, [], False, False),
            ("Mời diễn giả", 5, ["Lên lịch trình sơ bộ"], False, False),
            ("Xác nhận diễn giả", 3, ["Mời diễn giả"], False, False),
            ("Hoàn thiện agenda", 2, ["Xác nhận diễn giả"], False, False),
        ],
        "Venue & Facilities": [
            ("Tìm kiếm venue", 3, [], False, False),
            ("Đặt venue", 2, ["Tìm kiếm venue"], False, False),
            ("Setup phòng họp", 2, ["Đặt venue"], False, False),
            ("Setup trang thiết bị", 1, ["Setup phòng họp"], False, False),
        ],
        
        # Sport Competition Tasks
        "Athlete Management": [
            ("Mở đăng ký vận động viên", 1, [], False, False),
            ("Phân loại vận động viên", 3, ["Mở đăng ký vận động viên"], False, False),
            ("Lập lịch thi đấu", 2, ["Phân loại vận động viên"], False, False),
            ("Thông báo lịch thi đấu", 1, ["Lập lịch thi đấu"], False, False),
        ],
        "Venue & Equipment": [
            ("Kiểm tra sân bãi", 2, [], False, False),
            ("Chuẩn bị trang thiết bị", 3, ["Kiểm tra sân bãi"], False, False),
            ("Setup sân thi đấu", 2, ["Chuẩn bị trang thiết bị"], False, False),
            ("Test thiết bị", 1, ["Setup sân thi đấu"], False, False),
        ],
        
        # Generic fallbacks
        "Planning & Coordination": [("Lập kế hoạch tổng thể", 3, [], False, False)],
        "Operations & Logistics": [("Chuẩn bị logistics", 2, [], False, False)],
        "Marketing & Communication": [("Thiết kế ấn phẩm", 2, [], False, False)],
        "Finance & Budget": [("Lập ngân sách", 2, [], False, False)],
        "Technical & IT": [("Setup hệ thống", 2, [], False, False)],
    }
    return catalog.get(epic_name, [])


def _backward_schedule(tasks: List[Dict[str, Any]], event_date: str) -> None:
    # Compute latest finish backward from event_date
    end = datetime.strptime(event_date, "%Y-%m-%d").date()
    id_to_task = {t["task_id"]: t for t in tasks}

    # Topologically order by dependencies (simple iterative approach)
    remaining = set(id_to_task.keys())
    ordered: List[str] = []
    while remaining:
        progressed = False
        for tid in list(remaining):
            if all(dep in ordered or dep not in id_to_task for dep in id_to_task[tid]["depends_on"]):
                ordered.append(tid)
                remaining.remove(tid)
                progressed = True
        if not progressed:
            # cycle fallback: break ties arbitrarily
            ordered.append(remaining.pop())

    latest_end: Dict[str, date] = {}
    for tid in reversed(ordered):
        task = id_to_task[tid]
        duration = max(0, int(task["duration_days"]))
        if not task["depends_on"]:
            lf = end if duration == 0 else end  # zero-duration ends at end
        else:
            preds = [latest_end.get(d, end) for d in task["depends_on"]]
            lf = min(preds)
        task_end = lf
        task_start = task_end if duration == 0 else (task_end - timedelta(days=duration - 1))
        task["planned_end"] = task_end.strftime("%Y-%m-%d")
        task["planned_start"] = task_start.strftime("%Y-%m-%d")
        latest_end[tid] = task_start - timedelta(days=1) if duration > 0 else task_end


def _smart_department_assignment(epic_seeds: List[Tuple[str, str, str]], 
                                available_departments: List[str], 
                                headcount: int,
                                strict: bool = False) -> List[Tuple[str, str, str]]:
    """Smart assignment of epics to departments based on available resources"""
    
    if not available_departments:
        return epic_seeds
    
    # Department priority mapping (most critical first)
    priority_mapping = {
        "Tài chính": 1, "Finance": 1,
        "Hậu cần": 2, "Logistics": 2, "Operations": 2,
        "Media/Marketing": 3, "Media": 3, "Marketing": 3,
        "Đối ngoại": 4, "Partnership": 4, "External": 4,
        "Chuyên môn": 5, "Technical": 5, "Professional": 5,
        "Nội dung": 6, "Content": 6, "Program": 6,
        "Truyền thông sân khấu": 7, "Stage": 7, "Production": 7
    }
    
    # If we have more epics than departments, consolidate
    if len(epic_seeds) > len(available_departments):
        if strict:
            # Raise to let caller handle as an error (pipeline can convert to HTTP 400)
            raise ValueError("Not enough departments provided for strict assignment")
        # Strategy 1: Merge related epics
        merged_epics = []
        dept_usage = {dept: 0 for dept in available_departments}
        
        # Sort epics by priority
        sorted_epics = sorted(epic_seeds, key=lambda x: priority_mapping.get(x[1], 999))
        
        for epic_name, default_dept, desc in sorted_epics:
            # Find best matching department
            best_dept = None
            best_score = 0
            
            for dept in available_departments:
                score = 0
                # Exact match
                if dept.lower() in default_dept.lower() or default_dept.lower() in dept.lower():
                    score += 100
                # Keyword match
                for keyword in dept.lower().split():
                    if keyword in epic_name.lower() or keyword in default_dept.lower():
                        score += 50
                # Usage balance (prefer less used departments)
                score += (10 - dept_usage[dept])
                
                if score > best_score:
                    best_score = score
                    best_dept = dept
            
            if best_dept:
                dept_usage[best_dept] += 1
                merged_epics.append((epic_name, best_dept, desc))
            else:
                # Fallback to least used department
                least_used = min(available_departments, key=lambda d: dept_usage[d])
                dept_usage[least_used] += 1
                merged_epics.append((epic_name, least_used, desc))
        
        return merged_epics
    
    # If we have enough departments, use normal mapping
    return epic_seeds


def _adjust_tasks_for_team_size(tasks: List[Dict[str, Any]], 
                               headcount: int, 
                               epic_count: int) -> List[Dict[str, Any]]:
    """Adjust task complexity and duration based on team size"""
    
    if headcount <= 0:
        return tasks
    
    # Calculate tasks per person
    tasks_per_person = len(tasks) / max(headcount, 1)
    
    # If too many tasks per person, merge low-priority tasks into consolidated tasks
    if tasks_per_person > 8:  # More than 8 tasks per person
        # Score tasks: milestone high, name keywords next, else low
        critical_keywords = ["hợp đồng", "tổng duyệt", "soundcheck", "test", "thiết kế", "setup"]
        scored = []
        for t in tasks:
            score = 0
            if t.get("milestone", False):
                score += 100
            name_l = t["name"].lower()
            for k in critical_keywords:
                if k in name_l:
                    score += 20
            # shorter duration slightly higher priority
            score += max(0, 5 - int(t.get("duration_days", 0)))
            scored.append((score, t))

        # Sort by descending priority
        scored.sort(key=lambda x: x[0], reverse=True)
        keep_limit = max(1, headcount * 6)
        kept = [t for _, t in scored[:keep_limit]]

        # Merge remaining into consolidated tasks grouped by epic
        remaining = [t for _, t in scored[keep_limit:]]
        merged_by_epic: Dict[str, List[str]] = {}
        for t in remaining:
            merged_by_epic.setdefault(t["epic_id"], []).append(t["name"])

        merged_tasks = []
        for epic_id, names in merged_by_epic.items():
            merged_name = "; ".join(names[:5])
            merged_task = {
                "task_id": f"MERGE-{epic_id}",
                "epic_id": epic_id,
                "name": f"Merged tasks: {merged_name}",
                "duration_days": max(1, len(names) // 2),
                "depends_on": [],
                "can_parallel": True,
                "planned_start": "",
                "planned_end": "",
                "milestone": False,
            }
            merged_tasks.append(merged_task)

        result = kept + merged_tasks
        return result
    
    # If too few tasks, add more detail
    elif tasks_per_person < 3:
        # Add more granular tasks
        enhanced_tasks = []
        for task in tasks:
            enhanced_tasks.append(task)
            # Add sub-tasks for complex tasks
            if task["duration_days"] > 3:
                sub_task = task.copy()
                sub_task["name"] = f"Chi tiết {task['name']}"
                sub_task["duration_days"] = max(1, task["duration_days"] // 2)
                sub_task["task_id"] = f"{task['task_id']}-A"
                enhanced_tasks.append(sub_task)
        
        return enhanced_tasks
    
    return tasks


def _build_llm_messages(event_input: Dict[str, Any], retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    # Compose brief context from retrieved documents
    context_snippets: List[str] = []
    for d in (retrieved_docs or [])[:3]:
        snippet = (d.get("metadata", {}).get("title") or d.get("doc_id") or "KB")
        text = (d.get("text") or "").strip().replace("\n", " ")
        if len(text) > 800:
            text = text[:800] + "…"
        context_snippets.append(f"[{snippet}] {text}")

    system_prompt = (
        "Bạn là Trợ lý Lập kế hoạch Sự kiện. Nhiệm vụ: ĐỀ XUẤT NHỮNG ĐIỀU CHỈNH TỐI THIỂU cho danh sách EPIC và TASK dựa trên ngữ cảnh.\n"
        "QUY TẮC XUẤT RA (BẮT BUỘC):\n"
        "1) Trả về CHỈ MỘT JSON OBJECT, KHÔNG văn bản tự do, KHÔNG giải thích.\n"
        "2) JSON phải có đúng 2 khóa: epic_overrides (array) và extra_tasks (array).\n"
        "3) Định nghĩa:\n"
        "   - epic_overrides: array các object {name, department?, description?}.\n"
        "       + name: tên epic (tiếng Việt).\n"
        "       + department (tùy chọn): tên ban phù hợp với danh sách 'departments' nếu có (giữ nguyên chính tả).\n"
        "       + description (tùy chọn): mô tả ngắn gọn mục tiêu epic (<= 120 ký tự).\n"
        "   - extra_tasks: array các object {epic_name, name, is_milestone?}.\n"
        "       + name: tên task (tiếng Việt tự nhiên, hành động cụ thể, <= 80 ký tự).\n"
        "       + is_milestone (tùy chọn): true/false; chỉ dùng khi thực sự là mốc quan trọng.\n"
        "4) KHÔNG thêm bất kỳ trường nào khác (không được thêm id, date, deadline, duration, planned_start, planned_end, can_parallel, priority, budget, v.v.).\n"
        "5) KHÔNG nhắc lại ngữ cảnh, KHÔNG bình luận, KHÔNG markdown.\n"
        "6) Tư duy tối giản: chỉ đề xuất thay đổi KHI CẦN THIẾT dựa trên event_type, departments và kb_context. Tránh trùng lặp, tránh tên quá chung chung (ví dụ: 'Xử lý công việc chung').\n"
        "7) Ưu tiên dùng từ vựng ngành sự kiện, tiếng Việt rõ ràng, ngắn gọn.\n"
        "8) Ràng buộc tính nhất quán: nếu đổi department của một epic, đảm bảo epic_name vẫn đúng ngữ nghĩa của department đó.\n"
        "9) Không tạo quá nhiều extra_tasks: tối đa 8 task; chỉ những task thực sự thêm giá trị theo kb_context.\n"
        "10) Nếu kb_context mâu thuẫn, chọn phương án an toàn/chuẩn mực.\n"
        "Ví dụ JSON hợp lệ: {\n"
        "  \"epic_overrides\": [\n"
        "    {\"name\": \"Truyền thông & Marketing\", \"description\": \"Bộ KV, media plan, triển khai đa kênh\"}\n"
        "  ],\n"
        "  \"extra_tasks\": [\n"
        "    {\"epic_name\": \"Sân khấu & Âm thanh\", \"name\": \"Checklist an toàn điện\"}\n"
        "  ]\n"
        "}"
    )

    user_prompt = {
        "event": {
            "event_name": event_input.get("event_name"),
            "event_type": event_input.get("event_type"),
            "event_date": event_input.get("event_date"),
            "start_date": event_input.get("start_date") or event_input.get("start-date"),
            "venue": event_input.get("venue"),
            "departments": event_input.get("departments", []),
        },
        "kb_context": context_snippets,
        "contract": {
            "epic_overrides": [{"name": "string", "department": "string", "description": "string"}],
            "extra_tasks": [{"epic_name": "string", "name": "string", "is_milestone": False}],
        },
    }

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
    ]


def _call_llm_for_overrides(event_input: Dict[str, Any], retrieved_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not USE_LLM or OpenAI is None or not os.getenv("OPENAI_API_KEY"):
        return {}
    messages = _build_llm_messages(event_input, retrieved_docs)
    try:
        client = OpenAI()
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.2, # càng cao càng sáng tạo 
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
        with suppress(Exception):
            return json.loads(content)
        return {}
    except Exception:
        return {}


def generate_wbs(event_input: Dict[str, Any], retrieved_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate comprehensive WBS with improved task mapping and dependencies"""
    
    # Build epics from template and departments
    templates = _templates_for_event_type(event_input.get("event_type", ""))
    epic_seeds = templates["epics"]
    departments = event_input.get("departments") or []
    headcount = event_input.get("headcount_total") or 0

    # Smart department assignment (non-strict)
    assigned_epics = _smart_department_assignment(epic_seeds, departments, headcount, strict=False)

    # Optionally query LLM for overrides/extra tasks
    llm_out = _call_llm_for_overrides(event_input, retrieved_docs)
    override_by_name: Dict[str, Dict[str, Any]] = {}
    for it in llm_out.get("epic_overrides", []) or []:
        name = str(it.get("name") or "").strip()
        if name:
            override_by_name[name] = it

    epics: List[Dict[str, Any]] = []
    for idx, (ename, assigned_dept, desc) in enumerate(assigned_epics, start=1):
        override = override_by_name.get(ename)
        final_dept = override.get("department") if override and override.get("department") else assigned_dept
        final_desc = override.get("description") if override and override.get("description") else desc
        epics.append({
            "epic_id": f"EP-{idx:03d}",
            "name": ename,
            "department": final_dept,
            "description": final_desc,
        })

    # Expand tasks from seeds (no durations/timing surfaced)
    task_defs: List[Tuple[str, str, List[str]]] = []
    
    for epic in epics:
        seed = _seed_tasks_for_epic(epic["name"])
        for name, base_dur, dep_names, can_parallel, is_milestone in seed:
            task_defs.append((epic["epic_id"], name, dep_names))

    # Extra tasks suggested by LLM
    if llm_out.get("extra_tasks"):
        name_to_epic_id = {e["name"]: e["epic_id"] for e in epics}
        for t in llm_out["extra_tasks"]:
            epic_name = str(t.get("epic_name") or "").strip()
            task_name = str(t.get("name") or "").strip()
            if not task_name:
                continue
            epic_id = name_to_epic_id.get(epic_name)
            if not epic_id and epic_name:
                with suppress(Exception):
                    for ename, eid in name_to_epic_id.items():
                        if epic_name.lower() in ename.lower() or ename.lower() in epic_name.lower():
                            epic_id = eid
                            break
            if not epic_id and epics:
                epic_id = epics[0]["epic_id"]
            if epic_id:
                task_defs.append((epic_id, task_name, []))

    # Assign task IDs and build task objects
    _, task_ids = _gen_ids(len(epics), len(task_defs))
    tasks: List[Dict[str, Any]] = []
    name_to_id: Dict[Tuple[str, str], str] = {}
    
    for i, (epic_id, name, dep_names) in enumerate(task_defs, start=1):
        tid = task_ids[i - 1]
        task = {
            "task_id": tid,
            "epic_id": epic_id,
            "name": name,
            "depends_on": [],
        }
        tasks.append(task)
        name_to_id[(epic_id, name)] = tid

    # Resolve cross-epic dependencies
    for task in tasks:
        epic_id = task["epic_id"]
        epic_name = next(e["name"] for e in epics if e["epic_id"] == epic_id)
        seed = _seed_tasks_for_epic(epic_name)
        dep_names_for_task = next((d[2] for d in seed if d[0] == task["name"]), [])
        
        # Resolve dependencies within same epic
        task["depends_on"] = [name_to_id[(epic_id, n)] for n in dep_names_for_task if (epic_id, n) in name_to_id]
        
        # Cross-epic milestone wiring removed in minimal output

    # No team-size adjustment or scheduling in minimal output; keep dependencies only

    return {
        "epics": epics,
        "tasks": tasks,
    }
