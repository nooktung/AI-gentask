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
                model="gpt-3.5-turbo",  # Cheaper model for cost efficiency
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
            
            # Track cost (GPT-3.5-turbo: $0.0005/1K input, $0.0015/1K output)
            usage = response.usage
            input_cost = (usage.prompt_tokens / 1000) * 0.0005
            output_cost = (usage.completion_tokens / 1000) * 0.0015
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
        
        prompt = f"""Generate {target_count} specific, actionable tasks for the "{epic_name}" epic in the {department} department.

### Event Context:
- Event Type: {event_context.get('event_type', 'N/A')}
- Venue: {event_context.get('venue', 'N/A')} (Tier: {event_context.get('venue_tier', 'N/A')})
- Team Size: {event_context.get('headcount_total', 0)} total ({num_workers} workers in this department)
- Event Date: {event_context.get('event_date', 'N/A')}
- Special Requirements: {', '.join(event_context.get('special_requirements', []))}
{dept_responsibilities_str}

### Insights from Similar Past Events:
Key successful tasks from similar events:
{chr(10).join('• ' + task for task in key_tasks[:5])}

Lessons learned:
{chr(10).join('• ' + lesson for lesson in lessons_learned[:5])}

Venue-specific requirements ({event_context.get('venue_tier', 'N/A')} tier):
{chr(10).join('• ' + req for req in venue_reqs[:5])}

Special requirements for this event type:
{chr(10).join('• ' + req for req in special_reqs[:3])}
{base_tasks_str}

### Task Generation Rules:
1. Each task MUST start with an ACTION VERB in Vietnamese (e.g., Khảo sát, Thiết kế, Lập, Chuẩn bị, Liên hệ, Setup, Test, Triển khai)
2. Tasks must be SPECIFIC to the venue type and event type (not generic)
3. NO duplicate task names
4. Include realistic durations (1-7 days based on complexity)
5. Set appropriate priority levels (critical/high/medium/low)
6. Include dependencies where logical (use task names)
7. Adapt tasks based on lessons learned and special requirements
8. Make sure tasks are ACTIONABLE and MEASURABLE

### Output Format (JSON):
{{
  "tasks": [
    {{
      "name": "Action verb + specific task name",
      "description": "Detailed description (1-2 sentences)",
      "priority": "critical|high|medium|low",
      "duration_days": 1-7,
      "depends_on": ["Other task name"] or []
    }}
  ]
}}

Generate exactly {target_count} tasks optimized for this specific event, venue, and team size."""
        
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
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You enhance task names to be more specific. Respond in JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=300,
                response_format={"type": "json_object"}
            )
            
            # Track cost
            usage = response.usage
            cost = (usage.prompt_tokens / 1000) * 0.0005 + (usage.completion_tokens / 1000) * 0.0015
            self.total_cost += cost
            
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
    
    def get_total_cost(self) -> float:
        """Get total API cost so far"""
        return self.total_cost


# Example usage
if __name__ == "__main__":
    print("="*70)
    print("LLM TASK GENERATOR - TESTING")
    print("="*70)
    
    # Initialize (will work even without API key - falls back to templates)
    llm_gen = LLMTaskGenerator()
    
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