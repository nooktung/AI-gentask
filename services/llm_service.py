"""
LLM Task Generator - Generate context-aware tasks using LLM + RAG
Hybrid approach: Base templates + LLM enhancement for specificity
"""

from typing import List, Dict, Any, Optional
import os
from openai import OpenAI
import json
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.department_info import get_department_info, get_department_responsibilities


class LLMGenerator:
    """
    Generate tasks using LLM with RAG context
    Combines template-based reliability with LLM flexibility
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM task generator
        
        Args:
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None
        
        # Cost tracking
        self.total_cost = 0.0
    
    def generate_tasks_with_rag(
        self,
        epic_name: str,
        department: str,
        event_context: Dict[str, Any],
        rag_context: Dict[str, Any],
        num_workers: int,
        base_tasks: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate tasks using hybrid approach: templates + LLM enhancement
        
        Args:
            epic_name: Epic name (e.g., "Điều phối vận hành & hậu cần")
            department: Department name
            event_context: Current event details (type, venue, headcount, etc.)
            rag_context: Retrieved context from similar events
            num_workers: Number of workers available
            base_tasks: Optional base templates to enhance
            
        Returns:
            List of enhanced task dictionaries
        """
        
        if not self.client:
            # Fallback to templates if no LLM available
            return base_tasks or []
        
        # Calculate target task count (2-3 tasks per worker)
        target_count = max(3, min(num_workers * 2, 12))
        
        # Build prompt
        prompt = self._build_task_generation_prompt(
            epic_name=epic_name,
            department=department,
            event_context=event_context,
            rag_context=rag_context,
            num_workers=num_workers,
            target_count=target_count,
            base_tasks=base_tasks
        )
        
        # Call LLM
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using gpt-4o-mini for better quality
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert event organizer who creates detailed, actionable task lists. Always respond in valid JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            # Track cost (GPT-4o-mini: $0.150/1M input, $0.600/1M output)
            usage = response.usage
            input_cost = (usage.prompt_tokens / 1000000) * 0.150
            output_cost = (usage.completion_tokens / 1000000) * 0.600
            self.total_cost += (input_cost + output_cost)
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            tasks = result.get("tasks", [])
            
            # Validate and clean tasks
            tasks = self._validate_tasks(tasks)
            
            return tasks
            
        except Exception as e:
            # LLM generation failed
            # Fallback to base templates
            return base_tasks or []
    
    def _build_task_generation_prompt(
        self,
        epic_name: str,
        department: str,
        event_context: Dict[str, Any],
        rag_context: Dict[str, Any],
        num_workers: int,
        target_count: int,
        base_tasks: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Build LLM prompt for task generation"""
        
        # Extract RAG insights
        key_tasks = rag_context.get("key_tasks", [])
        lessons_learned = rag_context.get("lessons_learned", [])
        special_reqs = rag_context.get("special_requirements", [])
        venue_reqs = rag_context.get("venue_specific_requirements", [])
        
        # Get department responsibilities
        dept_responsibilities = get_department_responsibilities(department)
        dept_info = get_department_info(department)
        dept_responsibilities_str = ""
        if dept_responsibilities:
            dept_responsibilities_str = "\n### Department Responsibilities:\n"
            for i, resp in enumerate(dept_responsibilities, 1):
                dept_responsibilities_str += f"{i}. {resp}\n"
        
        # Base tasks context
        base_tasks_str = ""
        if base_tasks:
            base_tasks_str = "\n### Base Task Templates (enhance these):\n"
            for i, task in enumerate(base_tasks[:target_count], 1):
                base_tasks_str += f"{i}. {task['name']}: {task['description']}\n"
        
        # Calculate days until event for urgency context
        days_until_event = ""
        try:
            event_date_str = event_context.get('event_date', '')
            if event_date_str:
                from datetime import datetime
                event_dt = datetime.strptime(event_date_str, "%Y-%m-%d")
                days_until = (event_dt - datetime.now()).days
                days_until_event = f"\n- Days until event: {days_until} days ({'URGENT' if days_until < 14 else 'Normal' if days_until < 30 else 'Plenty of time'})"
        except:
            pass
        
        # Venue tier details
        venue_tier = event_context.get('venue_tier', 'M')
        venue_tier_context = ""
        if venue_tier == "XL":
            venue_tier_context = " (Very large venue - requires extensive setup, crowd control, multiple entry points, backup systems)"
        elif venue_tier == "L":
            venue_tier_context = " (Large venue - needs careful planning, good infrastructure)"
        elif venue_tier == "S":
            venue_tier_context = " (Small venue - simpler setup, but space constraints)"
        elif venue_tier == "XS":
            venue_tier_context = " (Very small venue - minimal setup, intimate setting)"
        
        # Headcount scaling context
        headcount = event_context.get('headcount_total', 50)
        headcount_context = ""
        if headcount >= 500:
            headcount_context = " (MASSIVE event - requires extensive coordination, multiple teams, backup plans, crowd management)"
        elif headcount >= 300:
            headcount_context = " (Large event - needs careful resource planning, multiple shifts)"
        elif headcount >= 100:
            headcount_context = " (Medium-large event - standard coordination needed)"
        elif headcount >= 50:
            headcount_context = " (Medium event - manageable scope)"
        else:
            headcount_context = " (Small event - simpler coordination)"
        
        prompt = f"""Bạn là chuyên gia quản lý sự kiện với nhiều năm kinh nghiệm. Tạo {target_count} nhiệm vụ CỤ THỂ và HÀNH ĐỘNG được cho epic "{epic_name}" trong ban {department}.

### THÔNG TIN SỰ KIỆN CHI TIẾT:
- Loại sự kiện: {event_context.get('event_type', 'N/A')}
- Địa điểm: {event_context.get('venue', 'N/A')} - Tier {venue_tier}{venue_tier_context}
- Quy mô: {headcount} người tham gia{headcount_context}
- Số nhân sự ban {department}: {num_workers} người
- Ngày tổ chức: {event_context.get('event_date', 'N/A')}{days_until_event}
- Yêu cầu đặc biệt: {', '.join(event_context.get('special_requirements', [])) if event_context.get('special_requirements') else 'Không có'}
{dept_responsibilities_str}

### KINH NGHIỆM TỪ CÁC SỰ KIỆN TƯƠNG TỰ:
Các nhiệm vụ quan trọng đã thành công:
{chr(10).join('• ' + task for task in key_tasks[:8]) if key_tasks else '• Chưa có dữ liệu'}

Bài học kinh nghiệm:
{chr(10).join('• ' + lesson for lesson in lessons_learned[:8]) if lessons_learned else '• Chưa có dữ liệu'}

Yêu cầu đặc thù cho venue tier {venue_tier}:
{chr(10).join('• ' + req for req in venue_reqs[:8]) if venue_reqs else '• Chưa có yêu cầu đặc biệt'}

Yêu cầu đặc biệt cho loại sự kiện này:
{chr(10).join('• ' + req for req in special_reqs[:5]) if special_reqs else '• Không có'}
{base_tasks_str}

### QUY TẮC TẠO NHIỆM VỤ:
1. **BẮT ĐẦU BẰNG ĐỘNG TỪ HÀNH ĐỘNG** (tiếng Việt): Khảo sát, Thiết kế, Lập, Chuẩn bị, Liên hệ, Setup, Test, Triển khai, Thu thập, Tổ chức, Đặt, Booking, Sắp xếp, Phát triển, Tạo, Quay, Đăng, Theo dõi, Nghiên cứu, Phân tích, Xây dựng, Install, Configure, Kiểm tra, Review, Approve, Ký kết, Thanh toán, Phân bổ, Trình, Điều chỉnh, Coordinate, Manage, Monitor, Track

2. **CỤ THỂ THEO SỰ KIỆN**: 
   - Nếu {headcount} người → cần tasks scale phù hợp (ví dụ: {headcount} người cần nhiều check-in points hơn 50 người)
   - Nếu venue tier {venue_tier} → cần tasks phù hợp với quy mô venue
   - Nếu event type {event_context.get('event_type', 'conference')} → cần tasks đặc thù cho loại sự kiện này

3. **PRIORITY LOGIC**:
   - critical: Nhiệm vụ BẮT BUỘC phải hoàn thành, nếu không sự kiện không thể diễn ra (ví dụ: Setup sân khấu, Test hệ thống AV)
   - high: Nhiệm vụ quan trọng, ảnh hưởng lớn đến chất lượng sự kiện (ví dụ: Khảo sát venue, Thiết kế layout)
   - medium: Nhiệm vụ cần thiết nhưng có thể điều chỉnh (ví dụ: Chuẩn bị vật tư, Liên hệ vendor)
   - low: Nhiệm vụ hỗ trợ, có thể làm sau (ví dụ: Chuẩn bị tài liệu, Tổng kết)

4. **DURATION REALISTIC**:
   - 1 ngày: Tasks đơn giản, có thể làm nhanh (ví dụ: Liên hệ vendor, Kiểm tra thiết bị)
   - 2-3 ngày: Tasks phức tạp vừa (ví dụ: Thiết kế layout, Setup hệ thống)
   - 4-7 ngày: Tasks phức tạp, cần nhiều bước (ví dụ: Phát triển campaign, Setup toàn bộ venue)

5. **DEPENDENCIES LOGIC**:
   - Task A phụ thuộc vào Task B nếu B phải hoàn thành trước A
   - Ví dụ: "Thiết kế layout" depends_on ["Khảo sát địa điểm"]
   - Ví dụ: "Test hệ thống AV" depends_on ["Setup hệ thống AV", "Kéo dây điện"]

6. **ADAPT TO CONTEXT**:
   - Nếu có lessons learned → tạo tasks để tránh lỗi đã gặp
   - Nếu có special requirements → tạo tasks để đáp ứng yêu cầu
   - Nếu venue tier {venue_tier} → tạo tasks phù hợp với quy mô
   - Nếu {headcount} người → scale tasks phù hợp

7. **ACTIONABLE & MEASURABLE**:
   - Mỗi task phải có thể thực hiện được (không quá mơ hồ)
   - Có thể đo lường được khi hoàn thành (ví dụ: "Khảo sát địa điểm" → có báo cáo khảo sát)

### OUTPUT FORMAT (JSON):
{{
  "tasks": [
    {{
      "name": "Động từ hành động + tên nhiệm vụ cụ thể",
      "description": "Mô tả chi tiết (1-2 câu) về nhiệm vụ này, tại sao cần thiết, và làm như thế nào",
      "priority": "critical|high|medium|low",
      "duration_days": 1-7,
      "depends_on": ["Tên task khác"] hoặc []
    }}
  ]
}}

### LƯU Ý QUAN TRỌNG:
- Tạo ĐÚNG {target_count} tasks (không ít hơn, không nhiều hơn)
- Mỗi task phải UNIQUE (không trùng tên)
- Tasks phải SPECIFIC cho sự kiện này (không generic)
- Ưu tiên tasks dựa trên lessons learned và special requirements
- Scale tasks phù hợp với {headcount} người và venue tier {venue_tier}

Hãy tạo {target_count} tasks tối ưu cho sự kiện cụ thể này."""
        
        return prompt
    
    def _validate_tasks(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and clean LLM-generated tasks"""
        
        validated = []
        seen_names = set()
        
        # Vietnamese action verbs to check
        action_verbs = {
            "khảo sát", "thiết kế", "lập", "chuẩn bị", "liên hệ", "setup",
            "test", "triển khai", "thu thập", "tổ chức", "đặt", "booking",
            "sắp xếp", "phát triển", "tạo", "quay", "đăng", "theo dõi",
            "nghiên cứu", "phân tích", "xây dựng", "install", "configure",
            "kiểm tra", "review", "approve", "ký kết", "thanh toán", "phân bổ",
            "trình", "điều chỉnh", "coordinate", "manage", "monitor", "track"
        }
        
        for task in tasks:
            name = task.get("name", "").strip()
            
            # Skip if no name or duplicate
            if not name or name in seen_names:
                continue
            
            # Check if starts with action verb
            first_word = name.split()[0].lower() if name else ""
            if not any(verb in first_word for verb in action_verbs):
                # Skip non-action tasks
                continue
            
            # Ensure required fields
            validated_task = {
                "name": name,
                "description": task.get("description", "")[:200],  # Limit description
                "priority": task.get("priority", "medium"),
                "duration_days": min(max(task.get("duration_days", 2), 1), 7),  # 1-7 days
                "depends_on": task.get("depends_on", [])[:3]  # Max 3 dependencies
            }
            
            # Validate priority
            if validated_task["priority"] not in ["critical", "high", "medium", "low"]:
                validated_task["priority"] = "medium"
            
            validated.append(validated_task)
            seen_names.add(name)
        
        return validated
    
    def enhance_template_tasks(
        self,
        base_tasks: List[Dict[str, Any]],
        event_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Lightweight enhancement: Just make task names more specific
        Uses much cheaper prompt (no full generation)
        
        Args:
            base_tasks: Template tasks to enhance
            event_context: Event details for context
            
        Returns:
            Enhanced tasks with specific names
        """
        
        if not self.client or not base_tasks:
            return base_tasks
        
        # Build lightweight prompt
        prompt = f"""Make these task names MORE SPECIFIC for:
Event: {event_context.get('event_type')} at {event_context.get('venue')} (tier {event_context.get('venue_tier')})
Headcount: {event_context.get('headcount_total')}

Tasks to enhance:
{chr(10).join(f'{i+1}. {t["name"]}' for i, t in enumerate(base_tasks))}

Rules:
- Keep action verb at start
- Add venue/event specific details
- Keep names concise (< 50 chars)
- Maintain same order

Output JSON:
{{"enhanced_names": ["Enhanced name 1", "Enhanced name 2", ...]}}"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You enhance task names to be more specific. Respond in JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            # Track cost (GPT-4o-mini: $0.150/1M input, $0.600/1M output)
            usage = response.usage
            input_cost = (usage.prompt_tokens / 1000000) * 0.150
            output_cost = (usage.completion_tokens / 1000000) * 0.600
            self.total_cost += (input_cost + output_cost)
            
            result = json.loads(response.choices[0].message.content)
            enhanced_names = result.get("enhanced_names", [])
            
            # Apply enhanced names
            for i, task in enumerate(base_tasks):
                if i < len(enhanced_names):
                    task["name"] = enhanced_names[i]
            
            return base_tasks
            
        except Exception as e:
            # Enhancement failed
            return base_tasks
    
    def generate_risks_with_llm(
        self,
        event_context: Dict[str, Any],
        department: str,
        existing_risks: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate event-specific risks using LLM
        
        Args:
            event_context: Event details (event_type, venue, headcount, etc.)
            department: Department name
            existing_risks: Optional existing risks to avoid duplicates
            
        Returns:
            List of risk dictionaries with id, title, category, likelihood, impact, etc.
        """
        
        if not self.client:
            return []
        
        event_type = event_context.get("event_type", "conference")
        venue = event_context.get("venue", "")
        headcount = event_context.get("headcount_total", 50)
        event_date = event_context.get("event_date", "")
        
        existing_titles = set()
        if existing_risks:
            for risk in existing_risks:
                existing_titles.add(risk.get("title", "").lower())
        
        # Calculate urgency based on event date
        urgency_context = ""
        try:
            if event_date:
                from datetime import datetime
                event_dt = datetime.strptime(event_date, "%Y-%m-%d")
                days_until = (event_dt - datetime.now()).days
                if days_until < 7:
                    urgency_context = " (RẤT GẤP - < 7 ngày, rủi ro cao về chất lượng và thiếu thời gian)"
                elif days_until < 14:
                    urgency_context = " (GẤP - < 14 ngày, cần chú ý timeline)"
                elif days_until < 30:
                    urgency_context = " (Bình thường - đủ thời gian chuẩn bị)"
                else:
                    urgency_context = " (Còn nhiều thời gian - có thể lên kế hoạch kỹ)"
        except:
            pass
        
        # Venue tier risk context
        venue_tier = event_context.get("venue_tier", "M")
        venue_risk_context = ""
        if venue_tier == "XL":
            venue_risk_context = "\n- Venue XL: Rủi ro về crowd control, hệ thống quá tải, an ninh, logistics phức tạp"
        elif venue_tier == "L":
            venue_risk_context = "\n- Venue L: Rủi ro về quản lý không gian, thiết bị, nhân sự"
        elif venue_tier == "S":
            venue_risk_context = "\n- Venue S: Rủi ro về không gian chật hẹp, thiếu thiết bị, khó di chuyển"
        
        # Headcount risk context
        headcount_risk_context = ""
        if headcount >= 500:
            headcount_risk_context = "\n- Quy mô lớn ({headcount} người): Rủi ro về quản lý đám đông, an toàn, logistics, nhân sự không đủ, hệ thống quá tải"
        elif headcount >= 300:
            headcount_risk_context = "\n- Quy mô lớn ({headcount} người): Rủi ro về coordination, resource planning, backup systems"
        elif headcount >= 100:
            headcount_risk_context = "\n- Quy mô trung bình ({headcount} người): Rủi ro về coordination và resource management"
        
        # Event type specific risks
        event_type_risks = {
            "career_fair": "Rủi ro đặc thù: Nhà tuyển dụng rút lui, không đủ gian hàng, check-in quá tải, thiếu thông tin công ty",
            "concert_opening": "Rủi ro đặc thù: Hệ thống AV hỏng, nghệ sĩ đến trễ, giấy phép công an, copyright issues, crowd control",
            "conference": "Rủi ro đặc thù: Diễn giả không đến, thiết bị presentation lỗi, wifi không đủ, thiếu tài liệu",
            "food_festival": "Rủi ro đặc thù: ATVSTP, thực phẩm hết, thiếu vendor, vệ sinh không đảm bảo",
            "sport_competition": "Rủi ro đặc thù: Thương tích, thiết bị thể thao hỏng, thời tiết, đối thủ không đến"
        }
        event_specific_context = event_type_risks.get(event_type, "Rủi ro chung cho sự kiện")
        
        # Department-specific risk focus
        dept_risk_focus = {
            "hậu cần": "Tập trung vào: Logistics, thiết bị, vận chuyển, an ninh, nhân sự onsite, backup systems",
            "marketing": "Tập trung vào: KPI không đạt, content delay, budget vượt, reach thấp, engagement kém",
            "chuyên môn": "Tập trung vào: Technical failures, AV issues, network problems, compatibility, backup systems",
            "tài chính": "Tập trung vào: Budget overrun, payment delays, contract issues, unexpected costs",
            "đối ngoại": "Tập trung vào: Partner withdrawal, communication delays, VIP issues, contract problems",
            "thiết kế": "Tập trung vào: Design approval delays, printing issues, brand consistency, deadline pressure"
        }
        dept_focus = dept_risk_focus.get(department.lower(), "Rủi ro chung cho ban")
        
        prompt = f"""Bạn là chuyên gia quản lý rủi ro sự kiện với nhiều năm kinh nghiệm. Tạo danh sách rủi ro CỤ THỂ và THỰC TẾ cho ban {department} trong sự kiện {event_type}.

### THÔNG TIN SỰ KIỆN CHI TIẾT:
- Loại sự kiện: {event_type} ({event_specific_context})
- Địa điểm: {venue} - Tier {venue_tier}{venue_risk_context}
- Quy mô: {headcount} người tham gia{headcount_risk_context}
- Ngày tổ chức: {event_date}{urgency_context}
- Ban phụ trách: {department} ({dept_focus})

### RỦI RO ĐÃ CÓ (TRÁNH TRÙNG LẶP):
{chr(10).join('• ' + title for title in list(existing_titles)[:10]) if existing_titles else '• Chưa có rủi ro nào'}

### YÊU CẦU TẠO RỦI RO:
1. **Tạo 3-5 rủi ro CỤ THỂ** cho ban {department}, không generic:
   - Phải liên quan đến {event_type} và {headcount} người
   - Phải phù hợp với venue tier {venue_tier}
   - Phải realistic và có thể xảy ra trong thực tế

2. **Mỗi rủi ro phải có đầy đủ:**
   - title: Tiêu đề ngắn gọn, cụ thể (< 60 ký tự)
   - category: logistics/technical/financial/safety/operational/performance/coordination
   - likelihood: 1-5 
     * 1 = Rất hiếm (dưới 5% khả năng)
     * 2 = Hiếm (5-20% khả năng)
     * 3 = Có thể xảy ra (20-50% khả năng)
     * 4 = Thường xuyên (50-80% khả năng)
     * 5 = Rất thường xuyên (trên 80% khả năng)
   - impact: 1-5
     * 1 = Nhỏ (ảnh hưởng không đáng kể, dễ xử lý)
     * 2 = Trung bình (ảnh hưởng một phần, cần điều chỉnh)
     * 3 = Lớn (ảnh hưởng đáng kể, cần nỗ lực xử lý)
     * 4 = Rất lớn (ảnh hưởng nghiêm trọng, có thể hủy một phần sự kiện)
     * 5 = Catastrophic (ảnh hưởng thảm khốc, có thể hủy toàn bộ sự kiện)
   - description: Mô tả chi tiết rủi ro, tại sao nó có thể xảy ra, và hậu quả nếu xảy ra
   - mitigation: Array 2-4 biện pháp giảm thiểu CỤ THỂ và HÀNH ĐỘNG được (ví dụ: "Thuê backup equipment", "Có 2 nhân sự dự phòng")
   - contingency: Array 2-4 kế hoạch dự phòng CỤ THỂ (ví dụ: "Sử dụng venue backup", "Chuyển sang plan B")

3. **Ưu tiên rủi ro:**
   - Rủi ro có likelihood × impact cao (≥ 12) → ưu tiên
   - Rủi ro đặc thù cho {event_type} → ưu tiên
   - Rủi ro liên quan đến {headcount} người và venue tier {venue_tier} → ưu tiên
   - Rủi ro cho ban {department} → tập trung vào {dept_focus}

4. **Tránh trùng lặp:**
   - Không tạo rủi ro giống hoặc tương tự với các rủi ro đã có
   - Mỗi rủi ro phải UNIQUE và SPECIFIC

### OUTPUT FORMAT (JSON):
{{
  "risks": [
    {{
      "title": "Tiêu đề rủi ro cụ thể và ngắn gọn",
      "category": "logistics|technical|financial|safety|operational|performance|coordination",
      "likelihood": 1-5,
      "impact": 1-5,
      "description": "Mô tả chi tiết: Rủi ro này là gì, tại sao có thể xảy ra trong sự kiện {event_type} với {headcount} người tại {venue}, và hậu quả nếu xảy ra",
      "mitigation": ["Biện pháp cụ thể 1", "Biện pháp cụ thể 2", "Biện pháp cụ thể 3"],
      "contingency": ["Kế hoạch dự phòng cụ thể 1", "Kế hoạch dự phòng cụ thể 2"]
    }}
  ]
}}

### VÍ DỤ RỦI RO TỐT:
- ❌ KHÔNG TỐT: "Thiết bị hỏng" (quá generic)
- ✅ TỐT: "Hệ thống âm thanh chính bị hỏng trong buổi soundcheck cuối cùng" (cụ thể, có context)

- ❌ KHÔNG TỐT: "Thiếu nhân sự" (quá generic)
- ✅ TỐT: "Nhân sự ban hậu cần không đủ trong khung giờ cao điểm (check-in, setup) do {headcount} người tập trung cùng lúc" (cụ thể, có số liệu)

Hãy tạo 3-5 rủi ro CỤ THỂ, THỰC TẾ và HÀNH ĐỘNG được cho ban {department} trong sự kiện này."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a risk management expert. Generate specific, actionable risks for events. Always respond in valid JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.8,  # Higher temperature for more diverse risks
                max_tokens=1000,
                response_format={"type": "json_object"}
            )
            
            # Track cost
            usage = response.usage
            input_cost = (usage.prompt_tokens / 1000000) * 0.150
            output_cost = (usage.completion_tokens / 1000000) * 0.600
            self.total_cost += (input_cost + output_cost)
            
            # Parse response
            result = json.loads(response.choices[0].message.content)
            risks = result.get("risks", [])
            
            # Add risk_score and risk_level
            for i, risk in enumerate(risks, 1):
                risk["risk_score"] = risk.get("likelihood", 3) * risk.get("impact", 3)
                risk["risk_level"] = self._calculate_risk_level(risk["risk_score"])
                # Generate ID
                dept_code = department[:2].upper().replace(" ", "") if len(department) >= 2 else "XX"
                risk["id"] = f"LLM-{dept_code}-{i:03d}"
            
            return risks
            
        except Exception as e:
            print(f"LLM risk generation failed: {e}")
            return []
    
    def _calculate_risk_level(self, risk_score: float) -> str:
        """Calculate risk level from score"""
        if risk_score >= 20:
            return "critical"
        elif risk_score >= 15:
            return "high"
        elif risk_score >= 8:
            return "medium"
        else:
            return "low"
    
    def get_total_cost(self) -> float:
        """Get total API cost so far"""
        return self.total_cost


# Example usage
if __name__ == "__main__":
    print("="*70)
    print("LLM TASK GENERATOR - TESTING")
    print("="*70)
    
    # Initialize (will work even without API key - falls back to templates)
    llm_gen = LLMGenerator()
    
    if not llm_gen.client:
        print("\n⚠️ No OpenAI API key found. Running in fallback mode.")
        print("Set OPENAI_API_KEY environment variable to enable LLM features.")
    else:
        print("\n✅ OpenAI API connected. LLM generation enabled.")
    
    # Example event context
    event_context = {
        "event_type": "concert_opening",
        "venue": "Đường 30m FPT",
        "venue_tier": "XL",
        "headcount_total": 100,
        "event_date": "2025-12-29",
        "special_requirements": ["Giấy phép công an", "Bảo hiểm sự kiện"]
    }
    
    # Example RAG context (from similar events)
    rag_context = {
        "key_tasks": [
            "Khảo sát sức chứa sân vận động",
            "Lắp đặt hệ thống âm thanh công suất lớn",
            "Thiết kế phân luồng cho 5000+ khán giả",
            "Test livestream với bandwidth 100Mbps"
        ],
        "lessons_learned": [
            "Venue lớn cần thêm 2 ngày setup",
            "An ninh cần tăng gấp đôi cho venue XL",
            "Backup power system bắt buộc"
        ],
        "special_requirements": [
            "Giấy phép công an cho sự kiện đông người",
            "Bảo hiểm sự kiện"
        ],
        "venue_specific_requirements": [
            "Booking venue trước 2-3 tháng",
            "Hệ thống âm thanh quy mô lớn",
            "Backup power system"
        ]
    }
    
    # Base templates
    base_tasks = [
        {
            "name": "Khảo sát địa điểm",
            "description": "Survey venue",
            "priority": "high",
            "duration_days": 2,
            "depends_on": []
        },
        {
            "name": "Thiết kế layout",
            "description": "Design layout",
            "priority": "high",
            "duration_days": 3,
            "depends_on": ["Khảo sát địa điểm"]
        }
    ]
    
    print("\n" + "="*70)
    print("TEST: Template Enhancement (Lightweight)")
    print("="*70)
    
    print("\nBase tasks:")
    for task in base_tasks:
        print(f"  • {task['name']}")
    
    enhanced = llm_gen.enhance_template_tasks(base_tasks, event_context)
    
    print("\nEnhanced tasks:")
    for task in enhanced:
        print(f"  • {task['name']}")
    
    print(f"\n💰 Cost: ${llm_gen.get_total_cost():.4f}")
    
    # Only test full generation if API key exists
    if llm_gen.client:
        print("\n" + "="*70)
        print("TEST: Full LLM Generation with RAG")
        print("="*70)
        
        tasks = llm_gen.generate_tasks_with_rag(
            epic_name="Điều phối vận hành & hậu cần",
            department="Hậu cần",
            event_context=event_context,
            rag_context=rag_context,
            num_workers=23,
            base_tasks=base_tasks
        )
        
        print(f"\nGenerated {len(tasks)} tasks:")
        for i, task in enumerate(tasks, 1):
            print(f"\n{i}. {task['name']}")
            print(f"   Priority: {task['priority']}, Duration: {task['duration_days']} days")
            print(f"   {task['description'][:80]}...")
        
        print(f"\n💰 Total cost: ${llm_gen.get_total_cost():.4f}")