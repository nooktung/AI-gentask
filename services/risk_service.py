"""
Risk Assessment Framework - Theo chuẩn PMBOK
Risk = Likelihood × Impact + Event-Specific Factors

Không dùng generic risks, mà:
1. Event-specific risks (ẩm thực → ATVSTP, âm nhạc → copyright)
2. Venue-specific risks (XL → crowd control)
3. Timeline risks (gần event → quality risks)
"""

from typing import Dict, List
from services.venue_service import VenueTier
from datetime import datetime, timedelta


class RiskAssessmentFramework:
    """
    Risk assessment theo PMBOK standard
    
    Risk Score = Likelihood (1-5) × Impact (1-5)
    Risk Level: Critical (>=20), High (15-19), Medium (8-14), Low (<8)
    """
    
    # Event-specific risk catalog
    EVENT_SPECIFIC_RISKS = {
        "concert_opening": {
            "hậu cần": [
                {
                    "id": "CONCERT-HC-001",
                    "title": "Hệ thống âm thanh không đủ công suất cho venue",
                    "category": "technical",
                    "likelihood": 3,  # Medium (30-60%)
                    "impact": 5,      # Critical
                    "description": "Loa không đủ mạnh, phủ sóng không đều, gây trải nghiệm kém",
                    "mitigation": [
                        "Soundcheck 2 ngày trước với full power",
                        "Đo decibel ở nhiều vị trí khán giả",
                        "Chuẩn bị loa backup công suất cao"
                    ],
                    "contingency": [
                        "Có nhà cung cấp loa backup trong vòng 4h",
                        "Giảm capacity venue nếu cần"
                    ]
                },
                {
                    "id": "CONCERT-HC-002",
                    "title": "Sập sân khấu do quá tải trọng",
                    "category": "safety",
                    "likelihood": 1,  # Low
                    "impact": 5,      # Critical
                    "description": "Sân khấu không chịu được trọng lượng thiết bị + người",
                    "mitigation": [
                        "Tính toán tải trọng chi tiết bởi kỹ sư",
                        "Giới hạn số người trên sân khấu",
                        "Kiểm tra cấu trúc thường xuyên"
                    ],
                    "contingency": [
                        "Insurance coverage",
                        "Emergency evacuation plan",
                        "Đội y tế standby"
                    ]
                },
            ],
            "đối ngoại": [
                {
                    "id": "CONCERT-DN-001",
                    "title": "Nghệ sĩ chính cancel phút chót (sức khỏe/lịch trình)",
                    "category": "external",
                    "likelihood": 2,  # Low-Medium (10-30%)
                    "impact": 5,      # Critical
                    "description": "Nghệ sĩ bị ốm, tai nạn, hoặc conflict lịch trình",
                    "mitigation": [
                        "Hợp đồng có penalty clause rõ ràng",
                        "Booking backup performer sớm",
                        "Event cancellation insurance",
                        "Yêu cầu health check trước event 3 ngày"
                    ],
                    "contingency": [
                        "Activate backup lineup ngay lập tức",
                        "Refund policy prepared",
                        "Crisis PR communication plan"
                    ]
                },
            ],
            "chuyên môn": [
                {
                    "id": "CONCERT-CM-001",
                    "title": "Livestream bị gián đoạn vì bandwidth không đủ",
                    "category": "technical",
                    "likelihood": 3,
                    "impact": 4,
                    "description": "Internet không đủ cho streaming 1080p/4K",
                    "mitigation": [
                        "Test bandwidth 1 tuần trước",
                        "Thuê dedicated line từ ISP",
                        "Có 4G/5G backup ready"
                    ],
                    "contingency": [
                        "Switch to 720p nếu cần",
                        "Record offline, post sau"
                    ]
                },
            ],
            "marketing": [
                {
                    "id": "CONCERT-MKT-001",
                    "title": "Vi phạm bản quyền âm nhạc trong promotional content",
                    "category": "legal",
                    "likelihood": 3,
                    "impact": 4,
                    "description": "Dùng nhạc không có license trong video promo",
                    "mitigation": [
                        "Chỉ dùng royalty-free music",
                        "Có giấy phép rõ ràng từ nghệ sĩ",
                        "Legal review trước khi post"
                    ],
                    "contingency": [
                        "Takedown nội dung vi phạm ngay",
                        "Apologize và thay bằng version hợp pháp"
                    ]
                },
            ],
        },
        
        "food_festival": {
            "hậu cần": [
                {
                    "id": "FOOD-HC-001",
                    "title": "Giấy phép ATVSTP không được duyệt đúng hạn",
                    "category": "regulatory",
                    "likelihood": 4,  # Medium-High (40-70%)
                    "impact": 5,      # Critical (dừng event)
                    "description": "Cơ quan y tế không approve do hồ sơ thiếu/sai",
                    "mitigation": [
                        "Nộp hồ sơ trước 60 ngày (not 30 days)",
                        "Thuê consultant về ATVSTP",
                        "Pre-inspection với cơ quan y tế",
                        "Chuẩn bị tất cả certificates từ vendors"
                    ],
                    "contingency": [
                        "Venue backup có sẵn giấy phép ATVSTP",
                        "Partner với nhà hàng licensed",
                        "Convert sang format không phục vụ đồ ăn"
                    ]
                },
                {
                    "id": "FOOD-HC-002",
                    "title": "Ngộ độc thực phẩm hàng loạt từ vendor",
                    "category": "health_safety",
                    "likelihood": 2,  # Low (10-30%)
                    "impact": 5,      # Critical
                    "description": "Food poisoning outbreak, hospitalization",
                    "mitigation": [
                        "Audit tất cả vendors 2 tuần trước",
                        "Yêu cầu food safety certificates",
                        "Sample testing thực phẩm ngẫu nhiên",
                        "Đội y tế + ambulance standby onsite"
                    ],
                    "contingency": [
                        "Emergency protocol với bệnh viện gần nhất",
                        "Event cancellation insurance activated",
                        "Crisis communication team ready",
                        "Recall all food từ vendor đó"
                    ]
                },
                {
                    "id": "FOOD-HC-003",
                    "title": "Thiếu khu vực rửa tay/vệ sinh theo quy định",
                    "category": "health_safety",
                    "likelihood": 3,
                    "impact": 4,
                    "description": "Không đủ handwashing stations, vi phạm quy định",
                    "mitigation": [
                        "1 handwashing station / 50 người",
                        "Portable sinks thuê từ chuyên vendor",
                        "Soap, sanitizer, paper towels đầy đủ",
                        "Biển báo rõ ràng"
                    ],
                    "contingency": [
                        "Thuê thêm stations khẩn cấp",
                        "Hand sanitizer stations bổ sung"
                    ]
                },
            ],
            "tài chính": [
                {
                    "id": "FOOD-TC-001",
                    "title": "Vendor food yêu cầu % revenue share cao hơn dự tính",
                    "category": "financial",
                    "likelihood": 3,
                    "impact": 3,
                    "description": "Food vendors demand 20-30% thay vì 15%",
                    "mitigation": [
                        "Negotiate hard trước, sign contract sớm",
                        "Có nhiều vendor options",
                        "Clear revenue share terms trong contract"
                    ],
                    "contingency": [
                        "Accept higher % nếu vendor chất lượng",
                        "Tăng booth rental fee để compensate"
                    ]
                },
            ],
        },
        
        "career_fair": {
            "đối ngoại": [
                {
                    "id": "CF-DN-001",
                    "title": "Công ty lớn rút lui phút chót (>3 companies)",
                    "category": "external",
                    "likelihood": 3,
                    "impact": 4,
                    "description": "Key companies cancel, ảnh hưởng chất lượng fair",
                    "mitigation": [
                        "Over-book 20% companies (expect dropouts)",
                        "Contract có cancellation penalties",
                        "Keep waitlist companies ready",
                        "Confirm attendance 1 tuần trước"
                    ],
                    "contingency": [
                        "Activate waitlist companies ngay",
                        "Reduce booth count, tối ưu layout",
                        "PR spin: 'intimate, curated fair'"
                    ]
                },
            ],
            "hậu cần": [
                {
                    "id": "CF-HC-001",
                    "title": "Không đủ không gian cho số lượng booth đã bán",
                    "category": "logistics",
                    "likelihood": 2,
                    "impact": 4,
                    "description": "Oversold booths, không fit layout",
                    "mitigation": [
                        "Measure venue chính xác, làm 3D layout",
                        "Cap booth sales dựa trên layout confirmed",
                        "Buffer space 10% cho circulation"
                    ],
                    "contingency": [
                        "Smaller booth size (3x3m thay vì 3x4m)",
                        "Expand sang area lân cận",
                        "Refund companies cuối cùng"
                    ]
                },
                {
                    "id": "CF-HC-002",
                    "title": "Quá tải check-in, sinh viên chờ quá lâu (>30 min)",
                    "category": "operations",
                    "likelihood": 4,
                    "impact": 3,
                    "description": "Bottleneck tại entrance, bad experience",
                    "mitigation": [
                        "QR code pre-registration required",
                        "Multiple check-in lanes (1 lane / 100 people)",
                        "Express lane cho pre-registered",
                        "Staff training cho fast check-in"
                    ],
                    "contingency": [
                        "Open all doors (no single entry point)",
                        "Wave through students if system down",
                        "Apologize + giveaways cho those waited long"
                    ]
                },
            ],
        },
        
        "conference": {
            "chuyên môn": [
                {
                    "id": "CONF-CM-001",
                    "title": "Laptop diễn giả không tương thích với projector/HDMI",
                    "category": "technical",
                    "likelihood": 4,  # High (very common!)
                    "impact": 3,
                    "description": "Mac không connect, hoặc resolution sai",
                    "mitigation": [
                        "Test tất cả laptops 1 ngày trước",
                        "Có đầy đủ adapters (HDMI, USB-C, VGA)",
                        "Backup laptop với all presentations loaded"
                    ],
                    "contingency": [
                        "Use backup laptop immediately",
                        "Screen share via Zoom nếu cần"
                    ]
                },
            ],
        },
    }
    
    def assess_event_risks(
        self,
        event_context: Dict
    ) -> Dict:
        """
        Comprehensive risk assessment
        
        Returns:
            {
                "by_department": {...},
                "overall": [...],
                "risk_matrix": {...},
                "top_risks": [...],
                "mitigation_priorities": [...]
            }
        """
        
        event_type = event_context.get("event_type", "conference")
        venue_tier = event_context.get("venue_tier", VenueTier.M)
        headcount = event_context.get("headcount_total", 50)
        departments = event_context.get("departments", [])
        
        from utils.department_normalizer import get_department_bucket
        
        risks = {
            "by_department": {},
            "overall": [],
            "risk_matrix": {},
            "top_risks": [],
            "mitigation_priorities": []
        }
        
        # 1. Get event-specific risks
        event_risks = self.EVENT_SPECIFIC_RISKS.get(event_type, {})
        
        for dept in departments:
            dept_bucket = get_department_bucket(dept)
            dept_risks = event_risks.get(dept_bucket, [])
            
            # Add risk score
            for risk in dept_risks:
                risk["risk_score"] = risk["likelihood"] * risk["impact"]
                risk["risk_level"] = self._calculate_risk_level(risk["risk_score"])
            
            risks["by_department"][dept_bucket] = dept_risks
        
        # 2. Add venue-specific risks
        venue_risks = self._get_venue_specific_risks(venue_tier, headcount)
        risks["overall"].extend(venue_risks)
        
        # 3. Add timeline risks
        timeline_risks = self._get_timeline_risks(event_context)
        risks["overall"].extend(timeline_risks)
        
        # 4. Calculate risk matrix
        risks["risk_matrix"] = self._build_risk_matrix(risks)
        
        # 5. Identify top risks
        all_risks = []
        for dept_risks in risks["by_department"].values():
            all_risks.extend(dept_risks)
        all_risks.extend(risks["overall"])
        
        # Sort by risk score
        all_risks.sort(key=lambda r: r["risk_score"], reverse=True)
        risks["top_risks"] = all_risks[:10]  # Top 10
        
        # 6. Prioritize mitigation
        risks["mitigation_priorities"] = self._prioritize_mitigation(all_risks)
        
        return risks
    
    def _calculate_risk_level(self, risk_score: float) -> str:
        """Convert risk score to level"""
        if risk_score >= 20:
            return "critical"
        elif risk_score >= 15:
            return "high"
        elif risk_score >= 8:
            return "medium"
        else:
            return "low"
    
    def _get_venue_specific_risks(
        self,
        venue_tier: VenueTier,
        headcount: int
    ) -> List[Dict]:
        """Venue-specific risks"""
        
        risks = []
        
        if venue_tier == VenueTier.XL:
            risks.append({
                "id": "VENUE-XL-001",
                "title": "Mất kiểm soát đám đông (>1000 người)",
                "category": "safety",
                "likelihood": 3,
                "impact": 5,
                "risk_score": 15,
                "risk_level": "high",
                "description": "Stampede, crushing, panic trong crowd lớn",
                "mitigation": [
                    "Thuê security chuyên nghiệp (1 guard / 100 người)",
                    "Crowd flow simulation trước event",
                    "Multiple entry/exit points rõ ràng",
                    "Barriers để control flow",
                    "PA system cho announcements"
                ],
                "contingency": [
                    "Emergency evacuation protocol",
                    "Coordination với police/fire dept",
                    "Medical team onsite"
                ]
            })
            
            risks.append({
                "id": "VENUE-XL-002",
                "title": "Hệ thống điện không đủ công suất cho thiết bị",
                "category": "technical",
                "likelihood": 3,
                "impact": 4,
                "risk_score": 12,
                "risk_level": "medium",
                "description": "Overload, breaker trip, blackout",
                "mitigation": [
                    "Professional electrician survey trước",
                    "Calculate total wattage needed",
                    "Backup generator mandatory",
                    "Distribute load across multiple circuits"
                ],
                "contingency": [
                    "Generator kick in < 30 seconds",
                    "Critical systems on UPS"
                ]
            })
        
        if headcount >= 100:
            risks.append({
                "id": "HC-001",
                "title": "Thiếu toilets, long queues (>10 min wait)",
                "category": "logistics",
                "likelihood": 4,
                "impact": 2,
                "risk_score": 8,
                "risk_level": "medium",
                "description": "Bad attendee experience, complaints",
                "mitigation": [
                    "1 toilet / 50 people minimum",
                    "Rent portable toilets nếu venue không đủ",
                    "Clear signage to all restrooms"
                ],
                "contingency": [
                    "Open staff restrooms to public",
                    "Rent additional portables mid-event"
                ]
            })
        
        return risks
    
    def _get_timeline_risks(
        self,
        event_context: Dict
    ) -> List[Dict]:
        """Timeline-based risks"""
        
        risks = []
        
        event_date = event_context.get("event_date")
        if not event_date:
            return risks
        
        try:
            days_until = (
                datetime.strptime(event_date, "%Y-%m-%d") - datetime.now()
            ).days
            
            if days_until < 14:
                risks.append({
                    "id": "TIME-001",
                    "title": "Timeline quá gấp, chất lượng kém",
                    "category": "project_management",
                    "likelihood": 5,
                    "impact": 4,
                    "risk_score": 20,
                    "risk_level": "critical",
                    "description": f"Chỉ còn {days_until} ngày, rushed work = poor quality",
                    "mitigation": [
                        "All-hands mode: everyone works overtime",
                        "Cut non-essential scope",
                        "Outsource critical tasks to vendors",
                        "Daily standup meetings"
                    ],
                    "contingency": [
                        "Delay event nếu quality không đạt",
                        "Accept lower quality, plan post-event improvements"
                    ]
                })
            
            if days_until < 7:
                risks.append({
                    "id": "TIME-002",
                    "title": "Vendors không thể deliver đúng deadline",
                    "category": "external",
                    "likelihood": 4,
                    "impact": 4,
                    "risk_score": 16,
                    "risk_level": "high",
                    "description": "Printing, catering, equipment không kịp giờ",
                    "mitigation": [
                        "Rush fees cho vendors",
                        "Backup vendors ready",
                        "Pickup instead of delivery"
                    ],
                    "contingency": [
                        "Use existing materials",
                        "Simplify requirements"
                    ]
                })
        except:
            pass
        
        return risks
    
    def _build_risk_matrix(self, risks: Dict) -> Dict:
        """Build risk matrix for visualization"""
        
        matrix = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        all_risks = []
        for dept_risks in risks["by_department"].values():
            all_risks.extend(dept_risks)
        all_risks.extend(risks["overall"])
        
        for risk in all_risks:
            level = risk.get("risk_level", "medium")
            matrix[level].append(risk)
        
        return matrix
    
    def _prioritize_mitigation(
        self,
        all_risks: List[Dict]
    ) -> List[Dict]:
        """Prioritize which risks to mitigate first"""
        
        # Sort by risk score
        sorted_risks = sorted(all_risks, key=lambda r: r["risk_score"], reverse=True)
        
        priorities = []
        
        for i, risk in enumerate(sorted_risks[:15], 1):  # Top 15
            priority = {
                "rank": i,
                "risk_id": risk["id"],
                "title": risk["title"],
                "risk_score": risk["risk_score"],
                "actions": risk.get("mitigation", [])[:3],  # Top 3 actions
                "owner": risk.get("responsible_dept", "TBD"),
                "deadline": self._suggest_mitigation_deadline(risk)
            }
            priorities.append(priority)
        
        return priorities
    
    def _suggest_mitigation_deadline(self, risk: Dict) -> str:
        """Suggest when mitigation should be done"""
        
        risk_score = risk["risk_score"]
        
        if risk_score >= 20:
            return "ASAP (within 3 days)"
        elif risk_score >= 15:
            return "1 week"
        elif risk_score >= 10:
            return "2 weeks"
        else:
            return "Before event"


# Singleton
_risk_framework = None

def get_risk_assessment_framework() -> RiskAssessmentFramework:
    """Get singleton"""
    global _risk_framework
    if _risk_framework is None:
        _risk_framework = RiskAssessmentFramework()
    return _risk_framework