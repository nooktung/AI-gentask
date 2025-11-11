"""
Task Scope Calculator - Tính số task dựa trên SCOPE thực tế
KHÔNG phải dựa vào headcount (sai lầm cơ bản)

Nghiệp vụ: Số task phụ thuộc vào:
1. Event type complexity
2. Venue infrastructure requirements  
3. Special requirements
4. Event duration
"""

from typing import Dict, List, Tuple
from services.venue_service import VenueTier
from datetime import datetime, timedelta


class TaskScopeCalculator:
    """
    Calculate task count based on event SCOPE, not headcount
    
    Principle: Headcount affects TEAM SIZE per task, not number of tasks
    """
    
    # Base task counts by event type (from real event experience)
    BASE_TASK_COUNTS = {
        "concert_opening": {
            "hậu cần": 18,      # Stage, sound, lighting, power, logistics
            "marketing": 12,     # Promo, social, ads, PR
            "chuyên môn": 15,    # Technical, IT, streaming, recording
            "tài chính": 10,     # Budget, contracts, payments
            "đối ngoại": 12,     # Artist management, rider, hospitality
            "thiết kế": 10,      # Visual, backdrop, signage
        },
        "career_fair": {
            "hậu cần": 25,      # NHIỀU HƠN: Setup nhiều booth, signage, logistics
            "marketing": 14,     # Student outreach, company promotion
            "đối ngoại": 18,     # NHIỀU HƠN: Liên hệ nhiều công ty
            "tài chính": 12,     # Sponsor management, booth fees
            "thiết kế": 12,      # Booth design, branding materials
            "chuyên môn": 10,    # Check-in system, IT support
        },
        "conference": {
            "hậu cần": 12,      # ÍT HƠN: Đơn giản hơn, indoor venue
            "marketing": 10,     # Registration promo, speaker marketing
            "chuyên môn": 14,    # AV setup, livestream, recording
            "tài chính": 8,      # Budget simpler
            "đối ngoại": 10,     # Speaker management
            "thiết kế": 8,       # Slides, branding
        },
        "food_festival": {
            "hậu cần": 30,      # NHIỀU NHẤT: Food safety, vendor setup, hygiene
            "marketing": 12,     
            "đối ngoại": 20,     # NHIỀU vendor relationships
            "tài chính": 14,     # Complex vendor payments
            "thiết kế": 10,
            "chuyên môn": 8,     # Simpler tech requirements
        },
        "sport_competition": {
            "hậu cần": 22,      # Field setup, equipment, medical
            "marketing": 12,
            "chuyên môn": 12,    # Timing, scoring systems
            "tài chính": 10,
            "đối ngoại": 8,      # Referee, judges
        },
    }
    
    def calculate_task_distribution(
        self, 
        event_context: Dict
    ) -> Dict[str, int]:
        """
        Calculate số task cho mỗi department dựa trên SCOPE
        
        Args:
            event_context: {
                event_type, venue_tier, special_requirements,
                event_date, headcount_total (chỉ để log, không dùng tính task)
            }
            
        Returns:
            Dict[department_name, task_count]
        """
        
        event_type = event_context.get("event_type", "conference")
        venue_tier = event_context.get("venue_tier", VenueTier.M)
        special_reqs = event_context.get("special_requirements", [])
        departments = event_context.get("departments", [])
        
        # Step 1: Get base counts
        base_counts = self.BASE_TASK_COUNTS.get(
            event_type,
            self.BASE_TASK_COUNTS["conference"]  # Default fallback
        )
        
        # Step 2: Filter to only requested departments
        from utils.department_normalizer import get_department_bucket
        
        task_distribution = {}
        for dept in departments:
            dept_bucket = get_department_bucket(dept)
            if dept_bucket in base_counts:
                task_distribution[dept_bucket] = base_counts[dept_bucket]
            else:
                # Unknown department, use average
                avg_count = int(sum(base_counts.values()) / len(base_counts))
                task_distribution[dept_bucket] = avg_count
        
        # Step 3: Adjust by venue tier (infrastructure complexity)
        venue_multiplier = self._get_venue_multiplier(venue_tier)
        
        for dept in task_distribution:
            task_distribution[dept] = int(task_distribution[dept] * venue_multiplier)
        
        # Step 4: Adjust by special requirements
        task_distribution = self._adjust_for_special_requirements(
            task_distribution,
            special_reqs
        )
        
        # Step 5: Adjust by event duration
        task_distribution = self._adjust_for_event_duration(
            task_distribution,
            event_context
        )
        
        return task_distribution
    
    def _get_venue_multiplier(self, venue_tier: VenueTier) -> float:
        """
        Venue tier affects infrastructure complexity
        
        XL venue: Nhiều tasks hơn (power, safety, logistics)
        S venue: Ít tasks hơn (simpler setup)
        """
        multipliers = {
            VenueTier.XL: 1.5,   # 50% more tasks
            VenueTier.L: 1.25,   # 25% more tasks
            VenueTier.M: 1.0,    # Baseline
            VenueTier.S: 0.8,    # 20% fewer tasks
            VenueTier.XS: 0.6,   # 40% fewer tasks
        }
        
        return multipliers.get(venue_tier, 1.0)
    
    def _adjust_for_special_requirements(
        self,
        task_distribution: Dict[str, int],
        special_reqs: List[str]
    ) -> Dict[str, int]:
        """
        Special requirements add specific tasks
        
        Examples:
        - Livestream → +5 chuyên môn tasks
        - VIP guests → +3 đối ngoại tasks
        - Food vendors → +8 hậu cần tasks
        """
        
        special_reqs_str = " ".join(special_reqs).lower()
        
        # Livestream/streaming requirements
        if any(kw in special_reqs_str for kw in ["livestream", "streaming", "broadcast"]):
            if "chuyên môn" in task_distribution:
                task_distribution["chuyên môn"] += 5
        
        # VIP/guest management
        if any(kw in special_reqs_str for kw in ["vip", "guest", "khách mời"]):
            if "đối ngoại" in task_distribution:
                task_distribution["đối ngoại"] += 3
        
        # Food/catering
        if any(kw in special_reqs_str for kw in ["food", "catering", "thức ăn"]):
            if "hậu cần" in task_distribution:
                task_distribution["hậu cần"] += 8
        
        # Outdoor/weather concerns
        if any(kw in special_reqs_str for kw in ["outdoor", "ngoài trời"]):
            if "hậu cần" in task_distribution:
                task_distribution["hậu cần"] += 4
        
        # Complex AV requirements
        if any(kw in special_reqs_str for kw in ["led wall", "projection", "lighting"]):
            if "chuyên môn" in task_distribution:
                task_distribution["chuyên môn"] += 4
        
        return task_distribution
    
    def _adjust_for_event_duration(
        self,
        task_distribution: Dict[str, int],
        event_context: Dict
    ) -> Dict[str, int]:
        """
        Multi-day events need more logistics/coordination tasks
        
        1-day event: Base count
        2-3 day event: +20% tasks
        4+ day event: +40% tasks
        """
        
        # Check if event has duration info
        event_date = event_context.get("event_date")
        start_date = event_context.get("start_date")
        
        if event_date and start_date:
            try:
                end_dt = datetime.strptime(event_date, "%Y-%m-%d")
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                duration_days = (end_dt - start_dt).days + 1
                
                if duration_days >= 4:
                    multiplier = 1.4
                elif duration_days >= 2:
                    multiplier = 1.2
                else:
                    multiplier = 1.0
                
                # Apply to logistics/operations departments
                for dept in ["hậu cần", "tài chính"]:
                    if dept in task_distribution:
                        task_distribution[dept] = int(task_distribution[dept] * multiplier)
                        
            except Exception:
                pass  # Invalid dates, skip adjustment
        
        return task_distribution
    
    def get_task_expansion_strategy(
        self,
        current_task_count: int,
        target_task_count: int,
        department: str,
        event_type: str
    ) -> List[Dict]:
        """
        Strategy để expand tasks khi cần thêm
        
        Returns: List of additional task templates to add
        """
        
        if current_task_count >= target_task_count:
            return []
        
        needed = target_task_count - current_task_count
        
        # Department-specific expansion patterns
        # Expanded to support larger events (more templates per department)
        expansion_templates = {
            "hậu cần": [
                {
                    "name": "Kiểm tra an toàn khu vực bổ sung",
                    "description": "Rà soát thêm các khu vực chưa check",
                    "priority": "high",
                    "duration_days": 1,
                },
                {
                    "name": "Chuẩn bị vật tư dự phòng",
                    "description": "Backup supplies cho trường hợp khẩn cấp",
                    "priority": "medium",
                    "duration_days": 1,
                },
                {
                    "name": "Setup khu vực lưu trữ thiết bị",
                    "description": "Tổ chức kho đồ có hệ thống",
                    "priority": "low",
                    "duration_days": 1,
                },
                {
                    "name": "Lập phương án di chuyển thiết bị sau sự kiện",
                    "description": "Logistics teardown và vận chuyển",
                    "priority": "low",
                    "duration_days": 1,
                },
                {
                    "name": "Chuẩn bị phương án xử lý sự cố khẩn cấp",
                    "description": "Emergency response protocol và contact list",
                    "priority": "high",
                    "duration_days": 1,
                },
                {
                    "name": "Kiểm tra và bảo trì thiết bị trước sự kiện",
                    "description": "Maintenance checklist và testing",
                    "priority": "medium",
                    "duration_days": 2,
                },
                {
                    "name": "Chuẩn bị nhân sự hỗ trợ tại chỗ",
                    "description": "Staffing plan và shift schedule",
                    "priority": "high",
                    "duration_days": 2,
                },
                {
                    "name": "Setup hệ thống quản lý hàng đợi",
                    "description": "Queue management cho check-in/registration",
                    "priority": "medium",
                    "duration_days": 1,
                },
                {
                    "name": "Chuẩn bị khu vực nghỉ giải lao cho nhân viên",
                    "description": "Staff break area và refreshments",
                    "priority": "low",
                    "duration_days": 1,
                },
                {
                    "name": "Lập kế hoạch dọn dẹp và thu hồi sau sự kiện",
                    "description": "Post-event cleanup và equipment return",
                    "priority": "medium",
                    "duration_days": 1,
                },
            ],
            "marketing": [
                {
                    "name": "Tạo content Instagram Stories",
                    "description": "Series stories countdown đến event",
                    "priority": "medium",
                    "duration_days": 3,
                },
                {
                    "name": "Liên hệ influencer/KOL",
                    "description": "Partnership với micro-influencers",
                    "priority": "medium",
                    "duration_days": 2,
                },
                {
                    "name": "Chuẩn bị press kit",
                    "description": "Media kit cho báo chí",
                    "priority": "low",
                    "duration_days": 2,
                },
                {
                    "name": "Tạo video teaser cho sự kiện",
                    "description": "Short video preview để tạo hype",
                    "priority": "medium",
                    "duration_days": 3,
                },
                {
                    "name": "Setup landing page cho đăng ký",
                    "description": "Event registration page và form",
                    "priority": "high",
                    "duration_days": 2,
                },
                {
                    "name": "Chạy chiến dịch quảng cáo Facebook/Google",
                    "description": "Paid ads để tăng reach",
                    "priority": "high",
                    "duration_days": 5,
                },
                {
                    "name": "Tạo hashtag campaign cho social media",
                    "description": "Branded hashtag và user-generated content",
                    "priority": "medium",
                    "duration_days": 2,
                },
                {
                    "name": "Chuẩn bị email marketing sequence",
                    "description": "Automated emails cho registrants",
                    "priority": "medium",
                    "duration_days": 3,
                },
                {
                    "name": "Tổ chức minigame/contest trước sự kiện",
                    "description": "Engagement activities để tăng awareness",
                    "priority": "low",
                    "duration_days": 3,
                },
                {
                    "name": "Chuẩn bị live streaming setup",
                    "description": "Streaming equipment và platform setup",
                    "priority": "medium",
                    "duration_days": 2,
                },
            ],
            "chuyên môn": [
                {
                    "name": "Setup hệ thống backup internet",
                    "description": "4G/5G backup cho primary internet",
                    "priority": "high",
                    "duration_days": 1,
                },
                {
                    "name": "Cài đặt monitoring system",
                    "description": "Real-time monitoring cho all tech systems",
                    "priority": "medium",
                    "duration_days": 1,
                },
                {
                    "name": "Chuẩn bị troubleshooting guide",
                    "description": "Quick fix guide cho common issues",
                    "priority": "low",
                    "duration_days": 1,
                },
                {
                    "name": "Test và calibrate hệ thống âm thanh",
                    "description": "Sound system testing và fine-tuning",
                    "priority": "high",
                    "duration_days": 1,
                },
                {
                    "name": "Setup hệ thống recording/streaming",
                    "description": "Recording equipment và streaming setup",
                    "priority": "medium",
                    "duration_days": 2,
                },
                {
                    "name": "Chuẩn bị backup equipment cho critical systems",
                    "description": "Spare equipment cho AV, IT, lighting",
                    "priority": "high",
                    "duration_days": 1,
                },
                {
                    "name": "Setup hệ thống network cho attendees",
                    "description": "WiFi access và bandwidth management",
                    "priority": "medium",
                    "duration_days": 2,
                },
                {
                    "name": "Chuẩn bị technical support team onsite",
                    "description": "Tech support staff và shift schedule",
                    "priority": "high",
                    "duration_days": 1,
                },
                {
                    "name": "Test compatibility với các thiết bị di động",
                    "description": "Mobile device testing cho apps/streaming",
                    "priority": "low",
                    "duration_days": 1,
                },
                {
                    "name": "Chuẩn bị documentation cho technical setup",
                    "description": "Technical specs và setup guides",
                    "priority": "low",
                    "duration_days": 1,
                },
            ],
            "tài chính": [
                {
                    "name": "Review lại tất cả hợp đồng",
                    "description": "Final contract audit",
                    "priority": "medium",
                    "duration_days": 1,
                },
                {
                    "name": "Chuẩn bị báo cáo tài chính trung gian",
                    "description": "Mid-point financial report",
                    "priority": "low",
                    "duration_days": 1,
                },
                {
                    "name": "Setup hệ thống tracking chi phí real-time",
                    "description": "Live expense tracking dashboard",
                    "priority": "medium",
                    "duration_days": 2,
                },
            ],
            "đối ngoại": [
                {
                    "name": "Chuẩn bị welcome kit cho đối tác",
                    "description": "Gift bags và materials",
                    "priority": "low",
                    "duration_days": 2,
                },
                {
                    "name": "Lên lịch courtesy calls",
                    "description": "Check-in calls với partners trước event",
                    "priority": "medium",
                    "duration_days": 1,
                },
                {
                    "name": "Chuẩn bị phương án đón tiếp VIP",
                    "description": "VIP reception protocol",
                    "priority": "high",
                    "duration_days": 2,
                },
            ],
            "thiết kế": [
                {
                    "name": "Thiết kế phiên bản mobile-optimized",
                    "description": "Mobile-first designs cho social",
                    "priority": "medium",
                    "duration_days": 2,
                },
                {
                    "name": "Tạo animation/motion graphics",
                    "description": "Animated content cho video",
                    "priority": "low",
                    "duration_days": 3,
                },
                {
                    "name": "Design merchandise/giveaways",
                    "description": "Branded items cho attendees",
                    "priority": "low",
                    "duration_days": 2,
                },
            ],
        }
        
        dept_templates = expansion_templates.get(department, [])
        
        if not dept_templates:
            # No expansion templates available, return empty
            return []
        
        # Return only unique templates (no variants, no cycling)
        # If needed > available templates, return only what we have
        # User doesn't want duplicate tasks with "(Phần X)" suffix
        return dept_templates[:needed]


# Singleton instance
_task_scope_calculator = None

def get_task_scope_calculator() -> TaskScopeCalculator:
    """Get singleton instance"""
    global _task_scope_calculator
    if _task_scope_calculator is None:
        _task_scope_calculator = TaskScopeCalculator()
    return _task_scope_calculator