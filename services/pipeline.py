"""
Pipeline V3 - Hybrid RAG + LLM Task Generation
Combines template reliability with LLM flexibility and RAG context awareness

UPDATED: Only returns 'departments' with full task info (no separate 'tasks' field)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import V3 components
from services.rag_engine import SimpleRAGEngine
from services.llm_generator import LLMGenerator
from services.task_generator import (
    calculate_available_workers,
    distribute_workers_to_departments,
    ACTION_TEMPLATES,
)
from services.risk_generator import generate_risks_by_department, generate_overall_risks
from services.venue_classifier import classify_venue, VenueTier, get_tier_multiplier
from utils.department_normalizer import normalize_department, normalize_departments, get_department_bucket
from services.task_complexity import (
    calculate_task_complexity,
    calculate_suggested_team_size
)
from services.dependency_analyzer import analyze_dependencies
from modules.wbs.cpm_scheduler import calculate_cpm, detect_parallel_opportunities
from services.dynamic_task_generator import assign_team_sizes_to_tasks
from services.priority_classifier import classify_priority_hybrid

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
        "thiết kế": {
            "name": "Thiết kế & sáng tạo nội dung",
            "description": "Thiết kế Key Visual, ấn phẩm, banner, poster, social media graphics, video content"
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
    
    UPDATED: Returns only 'departments' with full task info (no separate 'tasks')
    
    Args:
        event_input: Event details dict
        use_llm: Whether to use LLM (set False to fallback to pure templates)
        llm_mode: "enhance" (lightweight) or "generate" (full generation)
        
    Returns:
        Complete WBS with extracted_info, epics_task, departments (with full tasks), risks
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
        llm_gen = LLMGenerator()
        if not llm_gen.client:
            # LLM not available, falling back to templates
            use_llm = False
    
    # Parse event date
    try:
        event_dt = datetime.strptime(event_date, "%Y-%m-%d")
    except:
        event_dt = datetime.now() + timedelta(days=30)
    
    # Initialize departments output with full task info
    departments_output: Dict[str, List[Dict[str, Any]]] = {
        "hậu cần": [],
        "marketing": [],
        "chuyên môn": [],
        "tài chính": [],
        "đối ngoại": [],
        "thiết kế": [],
    }
    
    # Map epic_id to normalized department
    epic_dept_map = {}
    for e in epics:
        normalized = get_department_bucket(e["department"])
        epic_dept_map[e["epic_id"]] = normalized
    
    # Generate tasks dynamically based on headcount and available workers
    task_counter = 1
    used_names: set = set()
    # Global task name to task_id mapping (for cross-epic dependencies)
    global_task_map = {}

    for epic in epics:
        epic_id = epic["epic_id"]
        epic_name = epic["name"]
        department = epic["department"]
        normalized_dept = get_department_bucket(department)

        # Base templates to take wording and priority/description from
        base_templates = ACTION_TEMPLATES.get(epic_name, []) or [
            {"name": f"Nhiệm vụ {epic_name}", "description": "", "priority": "medium", "duration_days": 1, "depends_on": []}
        ]

        # Use LLM to generate event-specific tasks if available
        # NOTE: LLM calls can be slow, so we only use LLM if explicitly requested
        # Default mode is "enhance" which doesn't call LLM for task generation
        selected_templates = base_templates
        if use_llm and llm_gen and llm_mode == "generate":
            try:
                # Generate tasks with LLM + RAG context
                # Limit to max 10 tasks per department to avoid timeout
                limited_base_tasks = base_templates[:10] if len(base_templates) > 10 else base_templates
                
                llm_tasks = llm_gen.generate_tasks_with_rag(
                    epic_name=epic_name,
                    department=department,
                    event_context=event_context,
                    rag_context=rag_context,
                    num_workers=min(available_workers, 20),  # Limit context to avoid large prompts
                    base_tasks=limited_base_tasks
                )
                
                if llm_tasks and len(llm_tasks) > 0:
                    # Use LLM-generated tasks (event-specific)
                    selected_templates = llm_tasks[:15]  # Limit to 15 tasks max
                    # LLM generated tasks for department
                else:
                    # Fallback to templates
                    selected_templates = base_templates
            except Exception as e:
                # LLM generation failed, using templates
                selected_templates = base_templates
        else:
            # No LLM, use all available templates and expand based on event size
            # REQUIREMENT: Minimum tasks = headcount_total / 3
            # Scale tasks based on event characteristics, not just workers
            base_task_count = len(base_templates)
            
            # Calculate minimum required tasks per department
            min_tasks_per_dept = max(1, int(headcount_total / 3 / len(epics)))
            
            # Scale with event characteristics (more aggressive scaling)
            if headcount_total >= 300:
                event_multiplier = 4.0  # Very large events need many tasks
            elif headcount_total >= 200:
                event_multiplier = 3.0
            elif headcount_total >= 100:
                event_multiplier = 2.0
            elif headcount_total >= 50:
                event_multiplier = 1.5
            else:
                event_multiplier = 1.2
            
            # Venue tier multiplier
            tier_multiplier = get_tier_multiplier(venue_tier)
            if tier_multiplier >= 1.3:  # XL
                venue_multiplier = 1.5
            elif tier_multiplier >= 1.1:  # L
                venue_multiplier = 1.3
            else:
                venue_multiplier = 1.1
            
            # Event type multiplier (career_fair needs more tasks)
            if event_type == "career_fair":
                type_multiplier = 2.0  # Career fair needs many setup tasks
            elif event_type in ["concert_opening", "conference"]:
                type_multiplier = 1.5
            else:
                type_multiplier = 1.3
            
            # Department multiplier (more departments = more coordination tasks)
            dept_multiplier = 1.0 + (len(departments) - 1) * 0.15  # +15% per additional dept
            
            # Calculate target based on multipliers
            calculated_target = int(base_task_count * event_multiplier * venue_multiplier * type_multiplier * dept_multiplier)
            
            # Ensure minimum: at least headcount_total / 3 tasks per department
            target_task_count = max(calculated_target, min_tasks_per_dept)
            
            # Use only base templates - NO variants, NO duplicates
            # Limit to actual available templates to ensure uniqueness
            selected_templates = base_templates.copy()
            
            # For career_fair, add specific tasks if they don't already exist
            if event_type == "career_fair":
                career_fair_specific = [
                    {
                        "name": "Chuẩn bị gian hàng cho nhà tuyển dụng",
                        "description": "Setup bàn ghế, backdrop, bảng hiệu cho từng gian hàng",
                        "priority": "high",
                        "duration_days": 2,
                        "depends_on": []
                    },
                    {
                        "name": "Phân bổ vị trí gian hàng",
                        "description": "Sắp xếp vị trí các nhà tuyển dụng theo khu vực",
                        "priority": "high",
                        "duration_days": 1,
                        "depends_on": []
                    },
                    {
                        "name": "Chuẩn bị hệ thống check-in",
                        "description": "Setup hệ thống đăng ký và check-in cho sinh viên",
                        "priority": "high",
                        "duration_days": 2,
                        "depends_on": []
                    },
                    {
                        "name": "Tổ chức hướng dẫn cho sinh viên",
                        "description": "Chuẩn bị tài liệu hướng dẫn, map sự kiện cho sinh viên",
                        "priority": "medium",
                        "duration_days": 2,
                        "depends_on": []
                    },
                    {
                        "name": "Chuẩn bị khu vực phỏng vấn",
                        "description": "Setup phòng phỏng vấn riêng cho các nhà tuyển dụng",
                        "priority": "medium",
                        "duration_days": 1,
                        "depends_on": []
                    },
                    {
                        "name": "Liên hệ và mời nhà tuyển dụng",
                        "description": "Gửi thư mời, follow-up, xác nhận tham gia",
                        "priority": "high",
                        "duration_days": 3,
                        "depends_on": []
                    },
                    {
                        "name": "Thu thập thông tin nhà tuyển dụng",
                        "description": "Collect logo, mô tả công ty, yêu cầu setup",
                        "priority": "medium",
                        "duration_days": 2,
                        "depends_on": []
                    },
                    {
                        "name": "Chuẩn bị bảng hiệu và backdrop cho gian hàng",
                        "description": "In ấn và chuẩn bị vật liệu quảng cáo cho từng gian hàng",
                        "priority": "high",
                        "duration_days": 2,
                        "depends_on": []
                    },
                    {
                        "name": "Setup hệ thống wifi cho nhà tuyển dụng",
                        "description": "Cấu hình mạng, cung cấp password cho các gian hàng",
                        "priority": "medium",
                        "duration_days": 1,
                        "depends_on": []
                    },
                    {
                        "name": "Chuẩn bị tài liệu quảng cáo cho sinh viên",
                        "description": "In ấn brochure, flyer, thông tin công ty",
                        "priority": "medium",
                        "duration_days": 3,
                        "depends_on": []
                    },
                    {
                        "name": "Tổ chức briefing cho nhà tuyển dụng",
                        "description": "Họp với các công ty về quy trình, timeline, quy định",
                        "priority": "high",
                        "duration_days": 1,
                        "depends_on": []
                    },
                    {
                        "name": "Chuẩn bị khu vực nghỉ giải lao",
                        "description": "Setup khu vực nghỉ, nước uống, đồ ăn nhẹ",
                        "priority": "low",
                        "duration_days": 1,
                        "depends_on": []
                    },
                    {
                        "name": "Setup hệ thống đăng ký trực tuyến",
                        "description": "Cấu hình form đăng ký, QR code check-in",
                        "priority": "high",
                        "duration_days": 2,
                        "depends_on": []
                    },
                    {
                        "name": "Chuẩn bị phần thưởng và quà tặng",
                        "description": "Mua sắm, đóng gói quà tặng cho sinh viên",
                        "priority": "medium",
                        "duration_days": 2,
                        "depends_on": []
                    },
                    {
                        "name": "Tổ chức sự kiện networking",
                        "description": "Chuẩn bị khu vực networking, ice-breaker activities",
                        "priority": "low",
                        "duration_days": 1,
                        "depends_on": []
                    },
                ]
                
                # Add career_fair specific tasks only if they don't already exist
                existing_names = {t.get("name", "").lower() for t in selected_templates}
                for cf_task in career_fair_specific:
                    # Check exact match and similar names to avoid duplicates
                    cf_name_lower = cf_task["name"].lower()
                    is_duplicate = False
                    for existing_name in existing_names:
                        # Check if names are too similar (one contains the other)
                        if cf_name_lower in existing_name or existing_name in cf_name_lower:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        selected_templates.append(cf_task)
                        existing_names.add(cf_name_lower)
            
            # NO variant creation - only use unique templates
            # If we need more tasks, we rely on the base templates and event-specific tasks only

        # Create task name to task_id mapping for this epic (to resolve depends_on)
        epic_task_map = {}

        # Generate tasks from selected templates
        # Process in order to resolve dependencies correctly
        for template in selected_templates:
            base_name = template.get("name", f"Nhiệm vụ {epic_name}")
            
            # Skip if already used (avoid duplicates - case-insensitive check)
            base_name_lower = base_name.lower()
            if base_name_lower in used_names:
                continue
            
            used_names.add(base_name_lower)

            task_id = f"T-{task_counter:03d}"
            task_counter += 1
            epic_task_map[base_name] = task_id
            global_task_map[base_name] = task_id

            # Calculate dates based on duration and priority
            duration_days = template.get("duration_days", 1)
            base_priority = template.get("priority", "medium")
            
            # Resolve depends_on from template (check both epic_task_map and global_task_map)
            depends_on_names = template.get("depends_on", [])
            depends_on_ids = []
            for dep_name in depends_on_names:
                # First check in current epic, then global
                dep_id = epic_task_map.get(dep_name) or global_task_map.get(dep_name)
                if dep_id:
                    depends_on_ids.append(dep_id)

            # Create task dict first (before priority classification)
            task = {
                "task_id": task_id,
                "epic_id": epic_id,
                "name": base_name,
                "category": epic_name,
                "description": template.get("description", ""),
                "priority": base_priority,  # Will be updated by priority classifier
                "duration_days": duration_days,
                "depends_on": depends_on_ids,
                "assign": "",
            }
            
            # Priority Classification (Rule-based + Context-based)
            # Note: critical_path_tasks will be set after CPM, so we'll re-classify later
            try:
                priority = classify_priority_hybrid(
                    task=task,
                    event_context=event_context,
                    all_tasks=[],  # Will be updated after all tasks are created
                    dependency_context={
                        "is_on_critical_path": False,  # Will be updated after CPM
                        "has_critical_deps": False,
                        "is_blocking_many": len(depends_on_ids) > 2
                    },
                    critical_path_tasks=set()
                )
                task["priority"] = priority
            except Exception as e:
                # Priority classification failed, using base priority
                task["priority"] = base_priority
            
            # Calculate complexity based on task characteristics
            complexity = calculate_task_complexity(
                task=task,
                venue_tier=venue_tier,
                event_type=event_type,
                dependencies=depends_on_ids
            )
            task["complexity"] = complexity
            
            # Calculate initial suggested_team_size (will be adjusted later with constraints)
            suggested_size = calculate_suggested_team_size(
                complexity=complexity,
                duration_days=duration_days,
                venue_tier=venue_tier,
                has_critical_dependencies=False,  # Will be updated after CPM
                department=department,  # Pass department name for special handling (e.g., tài chính)
                headcount_total=headcount_total
            )
            task["suggested_team_size"] = suggested_size
            
            # Calculate days before event based on priority (with buffers and deps)
            days_before_event = _calculate_days_before_event(priority, duration_days, has_dependencies=bool(depends_on_ids))
            
            try:
                event_dt = datetime.strptime(event_date, "%Y-%m-%d")
            except:
                event_dt = datetime.now() + timedelta(days=30)
            
            deadline_dt = event_dt - timedelta(days=days_before_event)
            start_dt = deadline_dt - timedelta(days=duration_days - 1)
            
            task["start-date"] = start_dt.strftime("%Y-%m-%d")
            task["deadline"] = deadline_dt.strftime("%Y-%m-%d")

            # Ensure department exists in output dict
            if normalized_dept not in departments_output:
                departments_output[normalized_dept] = []
            departments_output[normalized_dept].append(task)
    
    # Collect all tasks for CPM and dependency analysis
    all_tasks = []
    for dept_tasks in departments_output.values():
        all_tasks.extend(dept_tasks)
    
    # Verify minimum requirement: total tasks >= headcount_total / 3
    min_total_tasks = max(1, int(headcount_total / 3))
    if len(all_tasks) < min_total_tasks:
        # Warning: Task count may be insufficient
        pass
    
    # Initialize variables
    dependency_analysis = None
    cpm_result = None
    critical_path_tasks = set()
    sizing_stats = {}
    
    if all_tasks:
        # Dependency Analysis (with error handling)
        try:
            dependency_analysis = analyze_dependencies(all_tasks, event_context)
        except Exception as e:
            # Dependency analysis failed
            dependency_analysis = None
        
        # CPM Scheduling (calculate ES/EF/LS/LF/Slack/Critical Path)
        try:
            cpm_result = calculate_cpm(all_tasks, event_date)
            critical_path_tasks = set(cpm_result.get("critical_path", []))
        except Exception as e:
            # CPM calculation failed
            cpm_result = None
            critical_path_tasks = set()
        
        if cpm_result:
            # Update tasks with CPM data
            tasks_with_cpm = {t["task_id"]: t for t in cpm_result.get("tasks_with_cpm", [])}
            for task in all_tasks:
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
        
        # Re-classify priority with critical path information
        for task in all_tasks:
            has_critical_deps = any(
                dep_id in critical_path_tasks 
                for dep_id in task.get("depends_on", [])
            )
            
            try:
                priority = classify_priority_hybrid(
                    task=task,
                    event_context=event_context,
                    all_tasks=all_tasks,
                    dependency_context={
                        "is_on_critical_path": task["task_id"] in critical_path_tasks,
                        "has_critical_deps": has_critical_deps,
                        "is_blocking_many": len([
                            t for t in all_tasks 
                            if task["task_id"] in t.get("depends_on", [])
                        ]) > 2
                    },
                    critical_path_tasks=critical_path_tasks
                )
                task["priority"] = priority
            except Exception as e:
                # Priority re-classification failed
                # Keep existing priority
                pass
            
            # Re-calculate complexity and suggested_team_size with critical path info
            complexity = calculate_task_complexity(
                task=task,
                venue_tier=venue_tier,
                event_type=event_type,
                dependencies=task.get("depends_on", [])
            )
            task["complexity"] = complexity
            
            # Get department from epic_dept_map
            task_epic_id = task.get("epic_id")
            task_department = epic_dept_map.get(task_epic_id) if task_epic_id else None
            
            suggested_size = calculate_suggested_team_size(
                complexity=complexity,
                duration_days=task.get("duration_days", 1),
                venue_tier=venue_tier,
                has_critical_dependencies=has_critical_deps,
                department=task_department,  # Pass department for special handling
                headcount_total=headcount_total
            )
            task["suggested_team_size"] = suggested_size
    
    # Assign team sizes with constraints: sum(suggested_team_size) = available_workers
    # Constraint: 1 <= suggested_team_size <= 5 per task
    if all_tasks:
        try:
            tasks_with_sizing, sizing_stats = assign_team_sizes_to_tasks(
                tasks=all_tasks,
                available_workers=available_workers,
                venue_tier=venue_tier,
                event_context=event_context,
                dependency_analysis=dependency_analysis
            )
            
            # Update tasks with adjusted team sizes
            task_id_to_sizing = {t["task_id"]: t for t in tasks_with_sizing}
            for task in all_tasks:
                if task["task_id"] in task_id_to_sizing:
                    sizing_task = task_id_to_sizing[task["task_id"]]
                    task["suggested_team_size"] = sizing_task.get("suggested_team_size", task.get("suggested_team_size", 1))
                # Ensure suggested_team_size exists (fallback to 1 if missing)
                if "suggested_team_size" not in task:
                    task["suggested_team_size"] = 1
        except Exception as e:
            # Team sizing failed, using initial suggested_team_size
            # Keep initial suggested_team_size if sizing fails
            sizing_stats = {
                "total_team_size": sum(t.get("suggested_team_size", 1) for t in all_tasks),
                "available_workers": available_workers,
                "adjustments": [f"Team sizing failed: {str(e)}"],
                "is_balanced": False
            }
    
    # Update epic dates based on tasks
    for epic in epics:
        epic_dept = get_department_bucket(epic["department"])
        epic_tasks = departments_output.get(epic_dept, [])
        
        # Filter tasks belonging to this epic
        epic_tasks = [t for t in epic_tasks if t["epic_id"] == epic["epic_id"]]
        
        if epic_tasks:
            start_dates = [datetime.strptime(t["start-date"], "%Y-%m-%d") for t in epic_tasks]
            end_dates = [datetime.strptime(t["deadline"], "%Y-%m-%d") for t in epic_tasks]
            
            epic["start-date"] = min(start_dates).strftime("%Y-%m-%d")
            epic["end-date"] = max(end_dates).strftime("%Y-%m-%d")
    
    # Generate risks (now with headcount and event_type awareness)
    risks_by_dept = generate_risks_by_department(
        departments=unique_depts,
        venue_tier=venue_tier,
        event_type=event_type,
        headcount_total=headcount_total
    )
    
    risks_overall = generate_overall_risks(
        venue_tier=venue_tier,
        event_type=event_type,
        headcount_total=headcount_total
    )
    
    risks = {
        "by_department": risks_by_dept,
        "overall": risks_overall
    }
    
    # Parallel opportunities detection
    parallel_opportunities = []
    if cpm_result:
        parallel_opportunities = detect_parallel_opportunities(all_tasks, cpm_result)
    
    # Prepare result - NO 'tasks' field, only 'departments' with full info
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
        "departments": departments_output,  # Full task info here with suggested_team_size, ES/EF/LS/LF, complexity
        "risks": risks,
        "rag_insights": {
            "similar_events": [e["event"]["event_name"] for e in similar_events],
            "key_learnings": best_practices.get("lessons_learned", [])[:5],
            "special_requirements": all_special_reqs,
        },
        "cpm": cpm_result,
        "dependency_analysis": dependency_analysis,
        "parallel_opportunities": parallel_opportunities,
        "sizing_stats": sizing_stats if all_tasks else {}
    }
    
    # Add cost info if LLM was used
    if use_llm and llm_gen:
        result["llm_cost"] = llm_gen.get_total_cost()
    
    return result


def _calculate_days_before_event(priority: str, duration: int, has_dependencies: bool = False) -> int:
    """Calculate how many days before event this task should be completed with safer buffers"""
    base_days = {
        "critical": 3,
        "high": 7,
        "medium": 14,
        "low": 21,
    }
    extra = 2 if has_dependencies else 0
    return base_days.get(priority, 7) + duration + extra


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
    print("PIPELINE V3 - HYBRID RAG + LLM (UPDATED)")
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
    
    # Count total tasks from departments
    total_tasks = sum(len(tasks) for tasks in result['departments'].values())
    print(f"  Total tasks in departments: {total_tasks}")
    
    print(f"  Available workers: {result['extracted_info']['available_workers']}")
    
    print(f"\n📊 Tasks by Department:")
    for dept, tasks in result['departments'].items():
        if tasks:
            print(f"  {dept}: {len(tasks)} tasks")
            print(f"    Sample: {tasks[0]['name']}")
    
    print(f"\n📚 RAG Insights:")
    print(f"  Similar events: {', '.join(result['rag_insights']['similar_events'])}")
    print(f"  Key learnings: {len(result['rag_insights']['key_learnings'])}")
    
    print("\n✅ PIPELINE UPDATED - Only 'departments' with full task info!")