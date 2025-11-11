"""
RAG Engine - Retrieve similar past events for context-aware task generation
Uses embedding similarity to find relevant historical events
"""

from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.department_info import (
    get_department_info,
    get_department_responsibilities,
    is_department_for_event,
    get_all_departments_for_event
)


class SimpleRAGEngine:
    """
    Lightweight RAG engine for event task generation
    Stores past events and retrieves similar ones based on:
    - Event type similarity
    - Venue tier similarity
    - Headcount similarity
    """
    
    def __init__(self, knowledge_base_path: Optional[str] = None):
        """
        Initialize RAG engine
        
        Args:
            knowledge_base_path: Path to JSON file with past events
        """
        self.knowledge_base: List[Dict[str, Any]] = []
        
        if knowledge_base_path:
            try:
                with open(knowledge_base_path, 'r', encoding='utf-8') as f:
                    self.knowledge_base = json.load(f)
            except:
                self.knowledge_base = []
        
        # Initialize with default knowledge if empty
        if not self.knowledge_base:
            self.knowledge_base = self._get_default_knowledge_base()
    
    def _get_default_knowledge_base(self) -> List[Dict[str, Any]]:
        """Default knowledge base with sample past events"""
        return [
            {
                "event_id": "EVT-2024-001",
                "event_name": "FPT University Opening Concert 2024",
                "event_type": "concert_opening",
                "venue": "Đường 30m",
                "venue_tier": "XL",
                "headcount_total": 150,
                "departments": ["hậu cần", "marketing", "chuyên môn", "tài chính"],
                "success_metrics": {
                    "on_time_completion": 0.95,
                    "budget_adherence": 0.92,
                    "attendee_satisfaction": 4.8
                },
                "key_tasks": [
                    "Khảo sát sức chứa sân vận động",
                    "Lắp đặt hệ thống âm thanh công suất lớn",
                    "Thiết kế phân luồng cho 5000+ khán giả",
                    "Test livestream với bandwidth 100Mbps",
                    "Chuẩn bị 20+ điểm vệ sinh di động"
                ],
                "lessons_learned": [
                    "Venue lớn cần thêm 2 ngày setup",
                    "An ninh cần tăng gấp đôi cho venue XL",
                    "Backup power system bắt buộc"
                ],
                "special_requirements": [
                    "Giấy phép công an cho sự kiện đông người",
                    "Bảo hiểm sự kiện",
                    "Kế hoạch ứng phó khẩn cấp"
                ]
            },
            {
                "event_id": "EVT-2024-002",
                "event_name": "Tech Career Fair FPT 2024",
                "event_type": "career_fair",
                "venue": "Hội trường tòa Gamma",
                "venue_tier": "M",
                "headcount_total": 50,
                "departments": ["hậu cần", "marketing", "tài chính", "đối ngoại"],
                "success_metrics": {
                    "on_time_completion": 0.98,
                    "budget_adherence": 0.95,
                    "attendee_satisfaction": 4.6
                },
                "key_tasks": [
                    "Thiết kế layout booth cho 30+ doanh nghiệp",
                    "Setup hệ thống check-in QR code",
                    "Chuẩn bị backdrop và standee",
                    "Liên hệ doanh nghiệp tuyển dụng",
                    "In tài liệu hướng dẫn 500 bản"
                ],
                "lessons_learned": [
                    "Hội trường cần booking trước 2 tuần",
                    "QR check-in giảm 50% thời gian xếp hàng",
                    "Tài liệu digital tốt hơn in ấn"
                ]
            },
            {
                "event_id": "EVT-2023-005",
                "event_name": "FPT Food Festival 2023",
                "event_type": "food_festival",
                "venue": "Sảnh tòa học",
                "venue_tier": "L",
                "headcount_total": 80,
                "departments": ["hậu cần", "marketing", "chuyên môn", "tài chính"],
                "success_metrics": {
                    "on_time_completion": 0.90,
                    "budget_adherence": 0.88,
                    "attendee_satisfaction": 4.7
                },
                "key_tasks": [
                    "Xin phép ATVSTP (An toàn vệ sinh thực phẩm)",
                    "Thuê 15+ food truck/stall",
                    "Setup hệ thống thanh toán không tiền mặt",
                    "Chuẩn bị khu rửa tay và vệ sinh",
                    "Tổ chức gameshow tương tác"
                ],
                "lessons_learned": [
                    "ATVSTP cần 1 tháng approve",
                    "Thanh toán cashless giảm queue time",
                    "Cần thêm điểm vệ sinh cho food event"
                ],
                "special_requirements": [
                    "Giấy phép ATVSTP",
                    "Bảo hiểm thực phẩm",
                    "Y tế dự phòng"
                ]
            },
            {
                "event_id": "EVT-2024-007",
                "event_name": "Seminar AI & Future Tech",
                "event_type": "conference",
                "venue": "Phòng 301 Alpha",
                "venue_tier": "S",
                "headcount_total": 25,
                "departments": ["marketing", "chuyên môn", "tài chính"],
                "success_metrics": {
                    "on_time_completion": 0.96,
                    "budget_adherence": 0.94,
                    "attendee_satisfaction": 4.5
                },
                "key_tasks": [
                    "Booking phòng học",
                    "Setup projector và micro",
                    "Chuẩn bị slides và tài liệu",
                    "Đặt nước uống và snack",
                    "Quay video và chụp ảnh"
                ],
                "lessons_learned": [
                    "Phòng nhỏ chỉ cần 1 ngày setup",
                    "Micro không dây tốt hơn có dây",
                    "Tài liệu digital tiết kiệm chi phí"
                ]
            },
            {
                "event_id": "EVT-2023-012",
                "event_name": "FPT Marathon 2023",
                "event_type": "sport_competition",
                "venue": "Đường 30m",
                "venue_tier": "XL",
                "headcount_total": 120,
                "departments": ["hậu cần", "marketing", "chuyên môn", "tài chính", "y tế"],
                "success_metrics": {
                    "on_time_completion": 0.93,
                    "budget_adherence": 0.90,
                    "attendee_satisfaction": 4.9
                },
                "key_tasks": [
                    "Đăng ký giấy phép chạy đường",
                    "Đo đạc và đánh dấu tuyến đường 10km",
                    "Setup 10+ trạm tiếp nước",
                    "Chuẩn bị 2 xe cứu thương standby",
                    "In 500+ bib number và timing chip"
                ],
                "lessons_learned": [
                    "Giấy phép đường chạy cần 6 tuần",
                    "Y tế dự phòng bắt buộc cho sport event",
                    "Timing chip chính xác hơn manual"
                ],
                "special_requirements": [
                    "Giấy phép sử dụng đường công cộng",
                    "Bảo hiểm thể thao",
                    "Đội y tế onsite",
                    "Phối hợp công an giao thông"
                ]
            }
        ]
    
    def retrieve_similar_events(
        self,
        event_type: str,
        venue_tier: str,
        headcount_total: int,
        departments: List[str],
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve top K similar past events
        
        Args:
            event_type: Type of event
            venue_tier: S/M/L/XL
            headcount_total: Total team size
            departments: List of departments
            top_k: Number of results to return
            
        Returns:
            List of similar past events with similarity scores
        """
        
        if not self.knowledge_base:
            return []
        
        # Calculate similarity for each event
        scored_events = []
        
        for past_event in self.knowledge_base:
            similarity_score = self._calculate_similarity(
                event_type=event_type,
                venue_tier=venue_tier,
                headcount_total=headcount_total,
                departments=departments,
                past_event=past_event
            )
            
            scored_events.append({
                "event": past_event,
                "similarity_score": similarity_score
            })
        
        # Sort by similarity
        scored_events.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        # Return top K
        return scored_events[:top_k]
    
    def _calculate_similarity(
        self,
        event_type: str,
        venue_tier: str,
        headcount_total: int,
        departments: List[str],
        past_event: Dict[str, Any]
    ) -> float:
        """
        Calculate similarity score between current and past event
        
        Returns:
            Float between 0 and 1 (higher = more similar)
        """
        
        score = 0.0
        
        # Event type match (40% weight)
        if event_type == past_event.get("event_type"):
            score += 0.4
        elif self._is_similar_event_type(event_type, past_event.get("event_type")):
            score += 0.2
        
        # Venue tier match (25% weight)
        if venue_tier == past_event.get("venue_tier"):
            score += 0.25
        elif self._is_adjacent_tier(venue_tier, past_event.get("venue_tier")):
            score += 0.15
        
        # Headcount similarity (20% weight)
        past_headcount = past_event.get("headcount_total", 0)
        if past_headcount > 0:
            headcount_ratio = min(headcount_total, past_headcount) / max(headcount_total, past_headcount)
            score += 0.2 * headcount_ratio
        
        # Department overlap (15% weight)
        past_depts = set(past_event.get("departments", []))
        current_depts = set(departments)
        
        if past_depts and current_depts:
            overlap = len(past_depts & current_depts) / len(past_depts | current_depts)
            score += 0.15 * overlap
        
        return score
    
    def _is_similar_event_type(self, type1: str, type2: str) -> bool:
        """Check if two event types are similar"""
        similar_groups = [
            {"concert_opening", "concert", "music_event"},
            {"conference", "seminar", "workshop"},
            {"career_fair", "expo", "exhibition"},
            {"sport_competition", "tournament", "championship"},
        ]
        
        for group in similar_groups:
            if type1 in group and type2 in group:
                return True
        
        return False
    
    def _is_adjacent_tier(self, tier1: str, tier2: str) -> bool:
        """Check if two tiers are adjacent (e.g., M and L)"""
        tier_order = ["S", "M", "L", "XL"]
        
        try:
            idx1 = tier_order.index(tier1)
            idx2 = tier_order.index(tier2)
            return abs(idx1 - idx2) == 1
        except:
            return False
    
    def add_event_to_knowledge_base(self, event_data: Dict[str, Any]):
        """
        Add a completed event to knowledge base for future reference
        
        Args:
            event_data: Event details including tasks, metrics, lessons learned
        """
        self.knowledge_base.append(event_data)
    
    def save_knowledge_base(self, path: str):
        """Save knowledge base to file"""
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_base, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            # Error saving knowledge base
            return False
    
    def get_venue_specific_requirements(self, venue_tier: str) -> List[str]:
        """Get venue-specific requirements based on tier"""
        requirements = {
            "S": [
                "Booking phòng trước 1 tuần",
                "Kiểm tra projector và sound system",
                "Chuẩn bị tài liệu cho 50-100 người"
            ],
            "M": [
                "Booking venue trước 2 tuần",
                "Test âm thanh và lighting",
                "Chuẩn bị signage và wayfinding",
                "Sắp xếp parking cho 50+ xe"
            ],
            "L": [
                "Booking venue trước 1 tháng",
                "Setup hệ thống âm thanh chuyên nghiệp",
                "Chuẩn bị kế hoạch phân luồng",
                "Xin phép các cơ quan liên quan",
                "Bảo hiểm sự kiện"
            ],
            "XL": [
                "Booking venue trước 2-3 tháng",
                "Giấy phép công an cho sự kiện đông người",
                "Hệ thống âm thanh và ánh sáng quy mô lớn",
                "Kế hoạch an ninh chi tiết",
                "Bảo hiểm sự kiện và trách nhiệm công cộng",
                "Đội y tế và xe cứu thương standby",
                "Backup power system",
                "Kế hoạch ứng phó khẩn cấp"
            ]
        }
        
        return requirements.get(venue_tier, [])
    
    def extract_best_practices(self, similar_events: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """
        Extract best practices from similar events
        
        Returns:
            Dict with key_tasks, lessons_learned, special_requirements
        """
        
        best_practices = {
            "key_tasks": [],
            "lessons_learned": [],
            "special_requirements": []
        }
        
        for event_dict in similar_events:
            event = event_dict["event"]
            
            # Collect key tasks
            best_practices["key_tasks"].extend(event.get("key_tasks", []))
            
            # Collect lessons learned
            best_practices["lessons_learned"].extend(event.get("lessons_learned", []))
            
            # Collect special requirements
            best_practices["special_requirements"].extend(event.get("special_requirements", []))
        
        # Remove duplicates while preserving order
        for key in best_practices:
            best_practices[key] = list(dict.fromkeys(best_practices[key]))
        
        return best_practices
    
    def get_department_context(
        self,
        departments: List[str],
        event_type: str = ""
    ) -> Dict[str, Any]:
        """
        Lấy thông tin context về các departments cho event
        
        Args:
            departments: List tên departments
            event_type: Loại sự kiện
            
        Returns:
            Dict với thông tin departments và responsibilities
        """
        context = {
            "departments": [],
            "total_departments": len(departments),
            "event_type": event_type
        }
        
        for dept in departments:
            dept_info = get_department_info(dept)
            if dept_info:
                # Check if department is relevant for this event
                is_relevant = is_department_for_event(dept, event_type)
                
                context["departments"].append({
                    "name": dept_info["display_name"],
                    "normalized_name": dept_info["normalized_name"],
                    "responsibilities": dept_info["responsibilities"],
                    "special_events": dept_info["special_events"],
                    "is_relevant_for_event": is_relevant,
                    "keywords": dept_info["keywords"]
                })
            else:
                # Unknown department - add with minimal info
                context["departments"].append({
                    "name": dept,
                    "normalized_name": dept.lower(),
                    "responsibilities": [],
                    "special_events": [],
                    "is_relevant_for_event": True,
                    "keywords": []
                })
        
        return context


# Example usage
if __name__ == "__main__":
    print("="*70)
    print("RAG ENGINE - TESTING")
    print("="*70)
    
    # Initialize RAG engine
    rag = SimpleRAGEngine()
    
    print(f"\n📚 Knowledge Base: {len(rag.knowledge_base)} past events")
    
    # Test retrieval for concert opening at large venue
    print("\n" + "="*70)
    print("TEST: Concert Opening at XL Venue")
    print("="*70)
    
    similar = rag.retrieve_similar_events(
        event_type="concert_opening",
        venue_tier="XL",
        headcount_total=100,
        departments=["hậu cần", "marketing", "chuyên môn", "tài chính"],
        top_k=3
    )
    
    print(f"\n🔍 Found {len(similar)} similar events:\n")
    
    for i, item in enumerate(similar, 1):
        event = item["event"]
        score = item["similarity_score"]
        
        print(f"{i}. {event['event_name']} (Similarity: {score:.2%})")
        print(f"   Type: {event['event_type']}, Tier: {event['venue_tier']}, Headcount: {event['headcount_total']}")
        print(f"   Key tasks preview:")
        for task in event['key_tasks'][:3]:
            print(f"     • {task}")
        print()
    
    # Extract best practices
    best_practices = rag.extract_best_practices(similar)
    
    print("\n💡 Best Practices from Similar Events:")
    print("\n📋 Key Tasks:")
    for task in best_practices["key_tasks"][:5]:
        print(f"  • {task}")
    
    print("\n📚 Lessons Learned:")
    for lesson in best_practices["lessons_learned"][:5]:
        print(f"  • {lesson}")
    
    print("\n⚠️ Special Requirements:")
    for req in best_practices["special_requirements"][:5]:
        print(f"  • {req}")
    
    # Test venue-specific requirements
    print("\n" + "="*70)
    print("VENUE-SPECIFIC REQUIREMENTS")
    print("="*70)
    
    for tier in ["S", "M", "L", "XL"]:
        reqs = rag.get_venue_specific_requirements(tier)
        print(f"\nTier {tier}:")
        for req in reqs:
            print(f"  • {req}")