"""
Pipeline V3 - Hybrid RAG + LLM Task Generation
Combines template reliability with LLM flexibility and RAG context awareness

UPDATED: Only returns 'departments' with full task info (no separate 'tasks' field)
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import V3 components
from services.rag_service import SimpleRAGEngine
from services.llm_service import LLMGenerator
from services.task_template_service import (
    calculate_available_workers,
    distribute_workers_to_departments,
    ACTION_TEMPLATES,
)
from services.risk_service import get_risk_assessment_framework
from services.venue_service import classify_venue, VenueTier, get_tier_multiplier
from utils.department_normalizer import normalize_department, normalize_departments, get_department_bucket
from services.task_complexity_service import (
    calculate_task_complexity,
    calculate_suggested_team_size
)
from services.dependency_service import analyze_dependencies
from modules.wbs.cpm_scheduler import calculate_cpm, detect_parallel_opportunities
from services.priority_service import classify_priority_hybrid
from services.team_sizing_service import get_team_size_optimizer
from services.task_scope_service import get_task_scope_calculator


def _normalize_task_name(name: str) -> str:
    """Normalize task name for duplicate detection"""
    import re
    # Remove "(Phần X)", "(Part X)" patterns
    name = re.sub(r'\s*\(Phần\s+\d+\)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\s*\(Part\s+\d+\)', '', name, flags=re.IGNORECASE)
    # Normalize: lowercase, strip, remove extra spaces
    name = name.lower().strip()
    name = re.sub(r'\s+', ' ', name)
    return name


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
    task_dependency_depth: Dict[str, int] = {}

    # Scope-based task targets per department
    scope_calculator = get_task_scope_calculator()
    scope_targets = scope_calculator.calculate_task_distribution({
        "event_type": event_type,
        "venue_tier": venue_tier,
        "special_requirements": all_special_reqs,
        "event_date": event_date,
        "departments": [get_department_bucket(e['department']) for e in epics],
        "headcount_total": headcount_total
    })

    for epic in epics:
        epic_id = epic["epic_id"]
        epic_name = epic["name"]
        department = epic["department"]
        normalized_dept = get_department_bucket(department)

        # Base templates to take wording and priority/description from
        base_templates = ACTION_TEMPLATES.get(epic_name, []) or [
            {"name": f"Nhiệm vụ {epic_name}", "description": "", "priority": "medium", "duration_days": 1, "depends_on": []}
        ]

        # Calculate target_task_count based on headcount (for all modes)
        base_task_count = len(base_templates)
        
        # Scale tasks based on organizing team size (not participants)
        # Team size typically: 10-20 (small), 20-50 (medium), 50-100 (large), 100+ (very large)
        # Minimum tasks per department: based on available workers per department
        available_workers_per_dept = max(1, available_workers // len(epics))
        min_tasks_per_dept = max(1, int(available_workers_per_dept * 0.5))  # ~0.5 tasks per worker
        
        # Scale with organizing team size (headcount = team size, not participants)
        if headcount_total >= 100:
            event_multiplier = 2.5  # Very large organizing team
        elif headcount_total >= 50:
            event_multiplier = 2.0  # Large organizing team
        elif headcount_total >= 30:
            event_multiplier = 1.8  # Medium-large team
        elif headcount_total >= 20:
            event_multiplier = 1.5  # Medium team
        else:
            event_multiplier = 1.2  # Small team (10-19 people)
        
        tier_multiplier = get_tier_multiplier(venue_tier)
        if tier_multiplier >= 1.3:
            venue_multiplier = 1.5
        elif tier_multiplier >= 1.1:
            venue_multiplier = 1.3
        else:
            venue_multiplier = 1.1
        
        if event_type == "career_fair":
            type_multiplier = 2.0
        elif event_type in ["concert_opening", "conference"]:
            type_multiplier = 1.5
        else:
            type_multiplier = 1.3
        
        dept_multiplier = 1.0 + (len(departments) - 1) * 0.15
        
        # Duration multiplier: Multi-day events need more tasks
        # Parse event_date to calculate duration if available
        duration_multiplier = 1.0
        try:
            if event_date:
                event_dt = datetime.strptime(event_date, "%Y-%m-%d")
                days_until = (event_dt - datetime.now()).days
                # Events with longer preparation time need more tasks
                if days_until >= 60:
                    duration_multiplier = 1.3  # Long preparation
                elif days_until >= 30:
                    duration_multiplier = 1.2
                elif days_until >= 14:
                    duration_multiplier = 1.1
                # Short timeline (< 14 days) = 1.0 (no multiplier)
        except:
            pass
        
        calculated_target = int(base_task_count * event_multiplier * venue_multiplier * type_multiplier * dept_multiplier * duration_multiplier)
        
        # Max cap: XL venue = 35 tasks/dept, L = 30, M = 25, S = 20
        max_tasks_per_dept = {
            VenueTier.XL: 35,
            VenueTier.L: 30,
            VenueTier.M: 25,
            VenueTier.S: 20,
            VenueTier.XS: 15,
        }.get(venue_tier, 25)
        
        calculated_target = min(calculated_target, max_tasks_per_dept)
        
        # ALWAYS ensure target_task_count >= min_tasks_per_dept (based on available workers)
        # This ensures each worker has sufficient tasks to work on
        target_task_count = max(calculated_target, min_tasks_per_dept)
        
        # Dynamic LLM/Template ratio based on organizing team size
        # Small team (< 20): 100% Templates (simple, fast)
        # Medium team (20-49): 70% Templates + 30% LLM (some customization)
        # Large team (>= 50): 20% Templates + 80% LLM (heavy customization)
        selected_templates = base_templates.copy()
        
        if use_llm and llm_gen and llm_mode == "generate":
            try:
                # Calculate LLM ratio based on organizing team size
                if headcount_total < 20:
                    llm_ratio = 0.0  # 100% templates (small team)
                elif headcount_total < 50:
                    llm_ratio = 0.3  # 30% LLM, 70% templates (medium team)
                else:
                    llm_ratio = 0.8  # 80% LLM, 20% templates (large team)
                
                # Calculate task counts
                llm_target_count = max(1, int(target_task_count * llm_ratio)) if llm_ratio > 0 else 0
                template_count = target_task_count - llm_target_count
                
                # Select base tasks for LLM (prioritize critical/high priority ones)
                # Sort by priority: critical > high > medium > low
                priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
                sorted_base = sorted(
                    base_templates,
                    key=lambda t: priority_order.get(t.get("priority", "medium"), 2)
                )
                llm_base_tasks = sorted_base[:min(llm_target_count * 2, len(sorted_base))]
                
                # Generate LLM tasks (only if llm_ratio > 0)
                llm_tasks = []
                if llm_target_count > 0:
                    llm_tasks = llm_gen.generate_tasks_with_rag(
                        epic_name=epic_name,
                        department=department,
                        event_context=event_context,
                        rag_context=rag_context,
                        num_workers=min(available_workers, 20),
                        base_tasks=llm_base_tasks[:10],  # Limit to 10 for LLM call
                        target_count=llm_target_count  # Pass calculated target count
                    )
                
                if llm_tasks and len(llm_tasks) > 0:
                    # Take LLM-generated tasks (up to llm_target_count)
                    llm_selected = llm_tasks[:llm_target_count]
                    
                    # Get remaining tasks from templates (avoid duplicates using normalized names)
                    llm_names_normalized = {_normalize_task_name(t.get("name", "")) for t in llm_selected}
                    template_selected = []
                    for t in base_templates:
                        if _normalize_task_name(t.get("name", "")) not in llm_names_normalized:
                            template_selected.append(t)
                            if len(template_selected) >= template_count:
                                break
                    
                    # Combine: LLM tasks + template tasks
                    selected_templates = llm_selected + template_selected
                else:
                    # LLM failed, use all templates
                    selected_templates = base_templates[:target_task_count]
            except Exception as e:
                # LLM generation failed, using templates
                selected_templates = base_templates[:target_task_count]
        else:
            # No LLM, use all available templates
            selected_templates = base_templates[:target_task_count] if target_task_count else base_templates.copy()
            
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
        # Scope-driven expansion if below target (applies to both LLM and non-LLM modes)
        # Use target_task_count (calculated from headcount) as primary target
        # Merge with scope_targets for event-type specific adjustments
        scope_target = scope_targets.get(normalized_dept, 0)
        # Use the MAXIMUM of headcount-based target and scope-based target
        # BUT: Always expand if below target_task_count (headcount-based requirement)
        target_count = max(target_task_count, scope_target)
        
        if len(selected_templates) < target_count:
            add_templates = scope_calculator.get_task_expansion_strategy(
                current_task_count=len(selected_templates),
                target_task_count=target_count,
                department=normalized_dept,
                event_type=event_type
            )
            # Append additional templates while keeping names unique
            # Check both current epic templates AND global used_names to avoid duplicates
            existing_names = {_normalize_task_name(t.get("name", "")) for t in selected_templates}
            # Also check global used_names to avoid cross-epic duplicates
            existing_names.update({_normalize_task_name(n) for n in used_names})
            for t in add_templates:
                name_normalized = _normalize_task_name(t.get("name", ""))
                if name_normalized and name_normalized not in existing_names:
                    selected_templates.append(t)
                    existing_names.add(name_normalized)
                    # CRITICAL: Update global used_names immediately to prevent duplicates in other epics
                    used_names.add(name_normalized)

        # Create task name to task_id mapping for this epic (to resolve depends_on)
        epic_task_map = {}

        # Generate tasks from selected templates
        # Process in order to resolve dependencies correctly
        # Filter out duplicates BEFORE generating to avoid gaps in task_id (using normalized names)
        unique_templates = []
        for template in selected_templates:
            base_name = template.get("name", f"Nhiệm vụ {epic_name}")
            base_name_normalized = _normalize_task_name(base_name)
            if base_name_normalized not in used_names:
                unique_templates.append(template)
                used_names.add(base_name_normalized)
        
        # Now generate tasks only from unique templates (no skipping = no gaps)
        for template in unique_templates:
            base_name = template.get("name", f"Nhiệm vụ {epic_name}")
            
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
            # NOTE: task_id will be assigned AFTER task is successfully created
            task = {
                "task_id": "",  # Will be assigned after successful creation
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
                headcount_total=headcount_total,
                event_context=event_context,
                priority=base_priority
            )
            task["suggested_team_size"] = suggested_size
            
            # Calculate dependency depth for buffer calculation
            if depends_on_ids:
                max_dep_depth = max(task_dependency_depth.get(dep_id, 0) for dep_id in depends_on_ids)
                dependency_depth = max_dep_depth + 1
            else:
                dependency_depth = 0

            # Calculate days before event based on priority (with buffers and deps)
            days_before_event = _calculate_days_before_event(
                priority,
                duration_days,
                has_dependencies=bool(depends_on_ids),
                dependency_depth=dependency_depth
            )
            
            try:
                event_dt = datetime.strptime(event_date, "%Y-%m-%d")
            except:
                event_dt = datetime.now() + timedelta(days=30)
            
            deadline_dt = event_dt - timedelta(days=days_before_event)
            start_dt = deadline_dt - timedelta(days=duration_days - 1)
            
            task["start-date"] = start_dt.strftime("%Y-%m-%d")
            task["deadline"] = deadline_dt.strftime("%Y-%m-%d")

            # CRITICAL: Generate task_id and update maps ONLY AFTER task is fully created
            # This ensures no gaps in task_id sequence
            task_id = f"T-{task_counter:03d}"
            task["task_id"] = task_id
            epic_task_map[base_name] = task_id
            global_task_map[base_name] = task_id
            # Update dependency depth map with task_id
            task_dependency_depth[task_id] = dependency_depth
            
            # Ensure department exists in output dict
            if normalized_dept not in departments_output:
                departments_output[normalized_dept] = []
            departments_output[normalized_dept].append(task)
            
            # CRITICAL: Only increment task_counter AFTER task is successfully created and appended
            # This ensures no gaps in task_id sequence
            task_counter += 1
    
    # Collect all tasks for CPM and dependency analysis
    all_tasks = []
    for dept_tasks in departments_output.values():
        all_tasks.extend(dept_tasks)
    
    # Verify minimum requirement: total tasks based on available workers
    # Each worker should have at least 1-2 tasks
    min_total_tasks = max(1, int(available_workers * 1.5))
    if len(all_tasks) < min_total_tasks:
        # Warning: Task count may be insufficient
        pass
    
    # Initialize variables
    dependency_analysis = None
    cpm_result = None
    critical_path_tasks = set()
    sizing_stats = {}
    
    dependency_warnings: List[str] = []

    if all_tasks:
        all_tasks, dependency_warnings = _validate_dependencies(all_tasks)

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
            
            # Calculate blocking count (how many tasks depend on this task)
            blocking_count = len([
                t for t in all_tasks 
                if task["task_id"] in t.get("depends_on", [])
            ])
            
            try:
                priority = classify_priority_hybrid(
                    task=task,
                    event_context=event_context,
                    all_tasks=all_tasks,
                    dependency_context={
                        "is_on_critical_path": task["task_id"] in critical_path_tasks,
                        "has_critical_deps": has_critical_deps,
                        "is_blocking_many": blocking_count > 2,
                        "blocking_count": blocking_count,  # ✅ Added for failure impact
                        "days_until_deadline": (datetime.strptime(task.get("deadline", event_date), "%Y-%m-%d") - datetime.now()).days if task.get("deadline") else 999
                    },
                    critical_path_tasks=critical_path_tasks
                )
                task["priority"] = priority
            except Exception as e:
                # Priority re-classification failed
                # Keep existing priority
                pass
        
        # Limit priority distribution: Only 10-15% critical, 25-30% high
        # This prevents priority inflation
        total_tasks = len(all_tasks)
        if total_tasks > 0:
            critical_limit = max(1, int(total_tasks * 0.15))  # Max 15% critical
            high_limit = max(1, int(total_tasks * 0.30))  # Max 30% high
            
            # Count current priorities
            critical_tasks = [t for t in all_tasks if t.get("priority") == "critical"]
            high_tasks = [t for t in all_tasks if t.get("priority") == "high"]
            
            # If too many critical, downgrade excess to high
            if len(critical_tasks) > critical_limit:
                # Sort by importance (keep highest as critical)
                critical_tasks_sorted = sorted(
                    critical_tasks,
                    key=lambda t: (
                        t.get("task_id") in critical_path_tasks,
                        len([d for d in t.get("depends_on", [])]),
                        t.get("complexity") == "critical"
                    ),
                    reverse=True
                )
                # Downgrade excess to high
                for task in critical_tasks_sorted[critical_limit:]:
                    task["priority"] = "high"
            
            # If too many high (including downgraded critical), downgrade excess to medium
            high_tasks_updated = [t for t in all_tasks if t.get("priority") == "high"]
            if len(high_tasks_updated) > high_limit:
                high_tasks_sorted = sorted(
                    high_tasks_updated,
                    key=lambda t: (
                        t.get("task_id") in critical_path_tasks,
                        len([d for d in t.get("depends_on", [])]),
                        t.get("complexity") == "high"
                    ),
                    reverse=True
                )
                # Downgrade excess to medium
                for task in high_tasks_sorted[high_limit:]:
                    task["priority"] = "medium"
        
        # Re-calculate complexity and suggested_team_size with critical path info
        for task in all_tasks:
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
                event_context=event_context,
                priority=task.get("priority", "medium"),
                has_critical_dependencies=has_critical_deps,
                department=task_department,  # Pass department for special handling
                headcount_total=headcount_total
            )
            task["suggested_team_size"] = suggested_size
    
    # Assign team sizes with constraints using optimizer
    if all_tasks:
        try:
            optimizer = get_team_size_optimizer()
            optimized_tasks, sizing_stats = optimizer.calculate_optimal_team_sizes(
                tasks=all_tasks,
                available_workers=available_workers,
                event_context=event_context
            )
            # Update team sizes in all_tasks
            opt_map = {t["task_id"]: t for t in optimized_tasks}
            for task in all_tasks:
                opt = opt_map.get(task["task_id"])
                if opt and "suggested_team_size" in opt:
                    task["suggested_team_size"] = opt["suggested_team_size"]
                if "suggested_team_size" not in task:
                    task["suggested_team_size"] = 1
            
            # CRITICAL: Update departments_output with normalized team sizes
            # Rebuild departments_output from updated all_tasks
            task_id_to_dept = {}
            for dept, tasks in departments_output.items():
                for task in tasks:
                    task_id_to_dept[task["task_id"]] = dept
            
            # Rebuild departments_output
            departments_output = {}
            for task in all_tasks:
                dept = task_id_to_dept.get(task["task_id"])
                if dept:
                    if dept not in departments_output:
                        departments_output[dept] = []
                    departments_output[dept].append(task)
        except Exception as e:
            # Team sizing failed, using initial suggested_team_size
            # BUT: Still need to normalize to fit within available_workers
            total_team_size = sum(t.get("suggested_team_size", 1) for t in all_tasks)
            
            # Emergency normalization if over-allocated
            if total_team_size > available_workers:
                scale_factor = available_workers / total_team_size if total_team_size > 0 else 0
                for task in all_tasks:
                    current = task.get("suggested_team_size", 1)
                    # Scale down but keep at least 1 person per task
                    task["suggested_team_size"] = max(1, int(current * scale_factor))
                
                # Recalculate after normalization
                total_team_size = sum(t.get("suggested_team_size", 1) for t in all_tasks)
            
            # CRITICAL: Update departments_output with normalized team sizes
            # Rebuild departments_output from updated all_tasks
            task_id_to_dept = {}
            for dept, tasks in departments_output.items():
                for task in tasks:
                    task_id_to_dept[task["task_id"]] = dept
            
            # Rebuild departments_output
            departments_output = {}
            for task in all_tasks:
                dept = task_id_to_dept.get(task["task_id"])
                if dept:
                    if dept not in departments_output:
                        departments_output[dept] = []
                    departments_output[dept].append(task)
            
            sizing_stats = {
                "total_team_size": total_team_size,
                "available_workers": available_workers,
                "adjustments": [f"Team sizing failed: {str(e)}", "Applied emergency normalization"],
                "is_balanced": total_team_size <= available_workers
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
    
    # Generate risks using Risk Assessment Framework + LLM
    risk_framework = get_risk_assessment_framework()
    event_context_for_risk = {
        **event_context,
        "departments": unique_depts
    }
    # Pass LLM generator to enable LLM risk generation for diversity
    risks = risk_framework.assess_event_risks(
        event_context_for_risk,
        llm_generator=llm_gen if use_llm else None
    )
    
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

    if dependency_warnings:
        result["dependency_warnings"] = dependency_warnings
    
    # Final validation: Ensure total team size = available_workers (exact match)
    # This is a safety check in case any tasks were added/modified after normalization
    total_team_size_final = sum(
        t.get("suggested_team_size", 1) 
        for dept_tasks in departments_output.values() 
        for t in dept_tasks
    )
    
    if total_team_size_final != available_workers:
        if total_team_size_final > available_workers:
            # Scale down proportionally
            scale_factor = available_workers / total_team_size_final if total_team_size_final > 0 else 0
            for dept_tasks in departments_output.values():
                for task in dept_tasks:
                    current = task.get("suggested_team_size", 1)
                    task["suggested_team_size"] = max(1, int(current * scale_factor))
        else:
            # Scale up proportionally (rare case)
            scale_factor = available_workers / total_team_size_final if total_team_size_final > 0 else 1
            for dept_tasks in departments_output.values():
                for task in dept_tasks:
                    current = task.get("suggested_team_size", 1)
                    task["suggested_team_size"] = max(1, int(current * scale_factor))
        
        # Final pass: Adjust to ensure exact match
        total_after_scale = sum(
            t.get("suggested_team_size", 1) 
            for dept_tasks in departments_output.values() 
            for t in dept_tasks
        )
        diff = available_workers - total_after_scale
        if diff != 0:
            # Distribute difference to tasks (prioritize critical/high priority)
            priority_order = {"critical": 3, "high": 2, "medium": 1, "low": 0}
            sorted_tasks = sorted(
                [t for dept_tasks in departments_output.values() for t in dept_tasks],
                key=lambda t: priority_order.get(t.get("priority", "medium"), 1),
                reverse=True
            )
            for i, task in enumerate(sorted_tasks):
                if diff == 0:
                    break
                if diff > 0:
                    task["suggested_team_size"] += 1
                    diff -= 1
                elif diff < 0 and task["suggested_team_size"] > 1:
                    task["suggested_team_size"] -= 1
                    diff += 1
        
        # Update sizing_stats
        if "sizing_stats" in result:
            final_total = sum(
                t.get("suggested_team_size", 1) 
                for dept_tasks in departments_output.values() 
                for t in dept_tasks
            )
            result["sizing_stats"]["final_allocation"] = final_total
            result["sizing_stats"]["is_within_budget"] = True
            result["sizing_stats"]["warnings"] = result["sizing_stats"].get("warnings", []) + [
                f"Applied final emergency normalization: {total_team_size_final} -> {final_total} (available: {available_workers})"
            ]
        
        # CRITICAL: Update result["departments"] with normalized team sizes
        result["departments"] = departments_output
    
    # CRITICAL: Always update result["departments"] with latest departments_output
    # This ensures any normalization is reflected in the result
    result["departments"] = departments_output
    
    # Add cost info if LLM was used
    if use_llm and llm_gen:
        result["llm_cost"] = llm_gen.get_total_cost()
    
    return result


def _calculate_days_before_event(
    priority: str,
    duration: int,
    has_dependencies: bool = False,
    dependency_depth: int = 0
) -> int:
    """Calculate how many days before event this task should be completed with safer buffers"""
    # Increased base days for critical tasks (was 5, now 7-10)
    base_days = {
        "critical": 8,  # Increased from 5 to 8 (safer)
        "high": 10,
        "medium": 18,
        "low": 25,
    }
    # Reduced buffers (was 3, now 2; was depth*2, now depth*1)
    dep_buffer = 2 if has_dependencies else 0  # Reduced from 3
    chain_buffer = max(0, dependency_depth) * 1  # Reduced from *2
    duration_buffer = max(0, int(round(duration * 0.2)))
    
    result = base_days.get(priority, 10) + duration + dep_buffer + chain_buffer + duration_buffer
    
    # Hard cap: No task deadline > 60 days before event
    return min(result, 60)


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
    return run_pipeline_with_rag(event_input, use_llm=True, llm_mode="generate")


def _validate_dependencies(tasks: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
    """
    Validate dependencies list to ensure no broken or circular references.
    Returns mutated tasks and list of warnings.
    """
    task_map = {task["task_id"]: task for task in tasks}
    warnings: List[str] = []

    for task in tasks:
        valid_deps: List[str] = []
        for dep_id in task.get("depends_on", []):
            if dep_id not in task_map:
                warnings.append(
                    f"Task '{task.get('name')}' depends on missing task '{dep_id}'"
                )
                continue

            dep_task = task_map[dep_id]
            if task["task_id"] in dep_task.get("depends_on", []):
                warnings.append(
                    f"Circular dependency detected between '{task.get('name')}' and '{dep_task.get('name')}'"
                )
                continue

            if dep_id not in valid_deps:
                valid_deps.append(dep_id)

        task["depends_on"] = valid_deps

    return tasks, warnings


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