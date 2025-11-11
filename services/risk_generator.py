from typing import Dict, List, Any
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.venue_classifier import VenueTier, scale_risk_level
from utils.department_normalizer import get_department_bucket as _normalize_department
from kb.risks_knowledge_base import get_risks_by_owner, search_risks


def generate_risks_by_department(
    departments: List[str],
    venue_tier: VenueTier,
    event_type: str = "",
    headcount_total: int = 50
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate risks grouped by department and scaled by venue tier, event type, and headcount
    
    Args:
        departments: List of department names
        venue_tier: Venue tier for scaling
        event_type: Event type (concert_opening, conference, etc.)
        headcount_total: Total headcount for risk scaling
    
    Returns:
        Dict with department names as keys and list of risks as values
    """
    
    # Base risk catalog by department
    base_risk_catalog = {
        "hậu cần": [
            {
                "id": "HC-001",
                "title": "Thiết bị hư hỏng đột xuất",
                "base_level": "medium",
                "description": "Thiết bị âm thanh, ánh sáng, sân khấu gặp sự cố kỹ thuật trong quá trình setup hoặc diễn ra sự kiện"
            },
            {
                "id": "HC-002",
                "title": "Thời tiết xấu (mưa, gió)",
                "base_level": "high",
                "description": "Điều kiện thời tiết bất lợi ảnh hưởng đến sự kiện ngoài trời, cần phương án dự phòng"
            },
            {
                "id": "HC-003",
                "title": "Vật tư thiếu hụt phút chót",
                "base_level": "medium",
                "description": "Nhà cung cấp không giao đủ hoặc đúng hạn, ảnh hưởng tiến độ setup"
            },
            {
                "id": "HC-004",
                "title": "Sự cố an toàn điện",
                "base_level": "critical",
                "description": "Quá tải điện, chập điện, thiếu hụt công suất cho thiết bị"
            },
            {
                "id": "HC-005",
                "title": "Khu vực setup không đủ không gian",
                "base_level": "medium",
                "description": "Diện tích thực tế nhỏ hơn dự kiến, cần điều chỉnh layout"
            },
        ],
        "marketing": [
            {
                "id": "MKT-001",
                "title": "Nội dung vi phạm bản quyền",
                "base_level": "high",
                "description": "Sử dụng hình ảnh, nhạc, hoặc nội dung không có quyền, dẫn đến vi phạm pháp luật"
            },
            {
                "id": "MKT-002",
                "title": "Key Visual không được duyệt",
                "base_level": "medium",
                "description": "Ban lãnh đạo yêu cầu chỉnh sửa lại thiết kế, làm trễ timeline"
            },
            {
                "id": "MKT-003",
                "title": "Ngân sách quảng cáo vượt dự trù",
                "base_level": "medium",
                "description": "Chi phí chạy ads cao hơn dự kiến, cần điều chỉnh chiến dịch"
            },
            {
                "id": "MKT-004",
                "title": "Reach thấp hơn mục tiêu",
                "base_level": "low",
                "description": "Số lượng người tiếp cận không đạt KPI, cần tối ưu nội dung"
            },
            {
                "id": "MKT-005",
                "title": "Phản hồi tiêu cực trên mạng xã hội",
                "base_level": "medium",
                "description": "Comments/reviews tiêu cực ảnh hưởng đến hình ảnh sự kiện"
            },
        ],
        "chuyên môn": [
            {
                "id": "CM-001",
                "title": "Hệ thống livestream bị gián đoạn",
                "base_level": "high",
                "description": "Kết nối internet không ổn định, thiết bị streaming gặp sự cố"
            },
            {
                "id": "CM-002",
                "title": "Âm thanh phản hồi (feedback)",
                "base_level": "medium",
                "description": "Hệ thống âm thanh bị rít, phản hồi, ảnh hưởng chất lượng"
            },
            {
                "id": "CM-003",
                "title": "Thiếu nhân sự kỹ thuật",
                "base_level": "high",
                "description": "Technician bị ốm hoặc bận việc đột xuất, không có người thay thế"
            },
            {
                "id": "CM-004",
                "title": "Dữ liệu bị mất (backup fail)",
                "base_level": "critical",
                "description": "Mất dữ liệu quan trọng: rundown, danh sách khách, cue sheet"
            },
            {
                "id": "CM-005",
                "title": "Hệ thống check-in quá tải",
                "base_level": "medium",
                "description": "Quá nhiều người check-in cùng lúc, hệ thống chậm hoặc crash"
            },
        ],
        "tài chính": [
            {
                "id": "TC-001",
                "title": "Chi phí vượt ngân sách",
                "base_level": "high",
                "description": "Tổng chi phí thực tế cao hơn dự trù, cần cắt giảm hoặc tìm thêm nguồn"
            },
            {
                "id": "TC-002",
                "title": "Nhà cung cấp yêu cầu thanh toán sớm",
                "base_level": "medium",
                "description": "Vendor đòi thanh toán trước thời hạn, ảnh hưởng dòng tiền"
            },
            {
                "id": "TC-003",
                "title": "Hợp đồng không rõ ràng",
                "base_level": "medium",
                "description": "Điều khoản hợp đồng mơ hồ dẫn đến tranh chấp với vendor"
            },
            {
                "id": "TC-004",
                "title": "Mất hóa đơn chứng từ",
                "base_level": "low",
                "description": "Không có đủ chứng từ để quyết toán, khó khăn trong báo cáo tài chính"
            },
            {
                "id": "TC-005",
                "title": "Sponsor rút lui phút chót",
                "base_level": "critical",
                "description": "Nhà tài trợ hủy hợp đồng, mất một phần nguồn thu quan trọng"
            },
        ],
        "thiết kế": [
            {
                "id": "TK-001",
                "title": "Key Visual không được duyệt",
                "base_level": "high",
                "description": "Ban lãnh đạo yêu cầu chỉnh sửa lại thiết kế, làm trễ timeline"
            },
            {
                "id": "TK-002",
                "title": "File thiết kế bị lỗi hoặc mất",
                "base_level": "critical",
                "description": "File thiết kế bị corrupt, mất dữ liệu, hoặc không tương thích với máy in"
            },
            {
                "id": "TK-003",
                "title": "Chất lượng in ấn không đạt yêu cầu",
                "base_level": "high",
                "description": "Màu sắc, độ phân giải, hoặc chất lượng in không đúng như thiết kế"
            },
            {
                "id": "TK-004",
                "title": "Thiết kế không phù hợp với yêu cầu",
                "base_level": "medium",
                "description": "Thiết kế không đáp ứng yêu cầu của ban lãnh đạo hoặc không phù hợp với concept"
            },
            {
                "id": "TK-005",
                "title": "Thiếu thời gian để chỉnh sửa",
                "base_level": "medium",
                "description": "Feedback quá nhiều hoặc quá muộn, không đủ thời gian để chỉnh sửa"
            },
            {
                "id": "TK-006",
                "title": "Vi phạm bản quyền hình ảnh/font",
                "base_level": "high",
                "description": "Sử dụng hình ảnh, font chữ không có license, dẫn đến vi phạm pháp luật"
            },
        ],
        "đối ngoại": [
            {
                "id": "DN-001",
                "title": "Nghệ sĩ/Diễn giả hủy show phút chót",
                "base_level": "critical",
                "description": "Performer chính hủy tham gia vì lý do sức khỏe, lịch trình, hoặc bất khả kháng"
            },
            {
                "id": "DN-002",
                "title": "Không liên hệ được với đối tác",
                "base_level": "high",
                "description": "Không thể liên hệ được với nghệ sĩ, diễn giả, hoặc đối tác để xác nhận"
            },
            {
                "id": "DN-003",
                "title": "Yêu cầu vượt quá khả năng",
                "base_level": "medium",
                "description": "Đối tác yêu cầu quá nhiều hoặc vượt quá ngân sách/khả năng của sự kiện"
            },
            {
                "id": "DN-004",
                "title": "Hợp đồng không được ký kết đúng hạn",
                "base_level": "high",
                "description": "Hợp đồng bị delay, ảnh hưởng đến việc chuẩn bị và thanh toán"
            },
            {
                "id": "DN-005",
                "title": "Thiếu thông tin từ đối tác",
                "base_level": "medium",
                "description": "Không nhận được đủ thông tin (rider, yêu cầu kỹ thuật) từ đối tác"
            },
        ],
    }
    
    # Event-type specific risks (additional risks based on event type)
    event_specific_risks = {
        "concert_opening": {
            "hậu cần": [
                {
                    "id": "HC-CON-001",
                    "title": "Nghệ sĩ đến muộn hoặc hủy show",
                    "base_level": "critical",
                    "description": "Nghệ sĩ chính không thể tham gia, cần có backup plan"
                },
                {
                    "id": "HC-CON-002",
                    "title": "Thiết bị âm thanh không đủ công suất",
                    "base_level": "high",
                    "description": "Hệ thống âm thanh không đáp ứng yêu cầu của nghệ sĩ"
                },
            ],
            "chuyên môn": [
                {
                    "id": "CM-CON-001",
                    "title": "Soundcheck không đủ thời gian",
                    "base_level": "medium",
                    "description": "Nghệ sĩ cần thời gian soundcheck nhưng bị giới hạn"
                },
            ],
        },
        "career_fair": {
            "hậu cần": [
                {
                    "id": "HC-CF-001",
                    "title": "Thiếu không gian cho các gian hàng",
                    "base_level": "high",
                    "description": "Số lượng nhà tuyển dụng vượt quá khả năng địa điểm"
                },
                {
                    "id": "HC-CF-002",
                    "title": "Quá tải tại khu vực check-in",
                    "base_level": "medium",
                    "description": "Sinh viên tập trung quá đông tại cổng vào"
                },
            ],
            "marketing": [
                {
                    "id": "MKT-CF-001",
                    "title": "Thông tin sự kiện không đến được đối tượng mục tiêu",
                    "base_level": "medium",
                    "description": "Sinh viên không biết về sự kiện, số lượng tham dự thấp"
                },
            ],
        },
        "conference": {
            "chuyên môn": [
                {
                    "id": "CM-CONF-001",
                    "title": "Hệ thống livestream bị gián đoạn",
                    "base_level": "high",
                    "description": "Kết nối internet không ổn định cho phần trình bày trực tuyến"
                },
                {
                    "id": "CM-CONF-002",
                    "title": "Thiết bị trình chiếu không tương thích",
                    "base_level": "medium",
                    "description": "Laptop của diễn giả không kết nối được với hệ thống"
                },
            ],
        },
    }
    
    # Headcount-specific risks (additional risks for large events)
    headcount_specific_risks = {
        "hậu cần": [
            {
                "id": "HC-HC-001",
                "title": "Quản lý đám đông quá tải",
                "base_level": "critical",
                "description": f"Với {headcount_total} người, khó kiểm soát đám đông, cần thêm nhân sự an ninh"
            },
            {
                "id": "HC-HC-002",
                "title": "Thiếu hụt nhà vệ sinh và tiện ích",
                "base_level": "high",
                "description": f"Số lượng người tham dự lớn ({headcount_total}) vượt quá khả năng địa điểm"
            },
        ],
        "tài chính": [
            {
                "id": "TC-HC-001",
                "title": "Chi phí vượt ngân sách do quy mô lớn",
                "base_level": "high",
                "description": f"Với {headcount_total} người, chi phí thực tế có thể cao hơn dự kiến"
            },
        ],
    } if headcount_total >= 100 else {}
    
    # Generate risks by department with venue scaling
    result = {}
    
    # Generic risks for departments not in catalog
    generic_risks = [
        {
            "id": "GEN-001",
            "title": "Thiếu nhân sự",
            "base_level": "high",
            "description": "Không đủ người để thực hiện công việc, cần điều động thêm"
        },
        {
            "id": "GEN-002",
            "title": "Tiến độ chậm trễ",
            "base_level": "medium",
            "description": "Công việc không hoàn thành đúng deadline, ảnh hưởng các ban khác"
        },
        {
            "id": "GEN-003",
            "title": "Thiếu phối hợp với các ban khác",
            "base_level": "medium",
            "description": "Thiếu communication và phối hợp, dẫn đến sai sót hoặc chồng chéo"
        },
        {
            "id": "GEN-004",
            "title": "Thay đổi yêu cầu đột xuất",
            "base_level": "high",
            "description": "Ban lãnh đạo yêu cầu thay đổi, làm lại công việc đã hoàn thành"
        },
    ]
    
    for dept in departments:
        # Normalize department name to standard bucket
        dept_bucket = _normalize_department(dept)
        
        # Get base risks for this department (use generic if not in catalog)
        if dept_bucket in base_risk_catalog:
            base_risks = base_risk_catalog[dept_bucket].copy()
        else:
            # Use generic risks for departments not in catalog
            base_risks = generic_risks.copy()
            # Department not in risk catalog, using generic risks
        
        # Add event-type specific risks
        if event_type and event_type in event_specific_risks:
            event_risks = event_specific_risks[event_type].get(dept_bucket, [])
            base_risks.extend(event_risks)
        
        # Add headcount-specific risks for large events
        if headcount_total >= 100 and dept_bucket in headcount_specific_risks:
            base_risks.extend(headcount_specific_risks[dept_bucket])
        
        # Try to get risks from knowledge base first (with mitigation and solution)
        # Try multiple variations of department name
        knowledge_base_risks = []
        dept_variations = [
            dept_bucket,
            dept,  # Original name
            dept.lower(),
            dept_bucket.lower(),
            dept.replace(" ", "").lower(),
            dept_bucket.replace(" ", "").lower()
        ]
        
        for dept_var in dept_variations:
            risks = get_risks_by_owner(dept_var)
            if risks:
                knowledge_base_risks = risks
                break
        
        # Merge knowledge base risks with template risks
        # Knowledge base risks have priority (they have mitigation and solution)
        # Ensure NO duplicates by checking both title and id
        scaled_risks = []
        seen_risk_ids = set()
        seen_risk_titles = set()
        
        if knowledge_base_risks:
            # Use knowledge base risks first
            for risk in knowledge_base_risks:
                risk_id = risk.get("id", f"{dept_bucket}-{len(scaled_risks)+1}")
                risk_title = risk["title"]
                
                # Skip if duplicate (check both id and title)
                if risk_id in seen_risk_ids or risk_title.lower() in seen_risk_titles:
                    continue
                
                scaled_risk = {
                    "id": risk_id,
                    "title": risk_title,
                    "level": scale_risk_level(risk.get("level", "medium"), venue_tier),
                    "description": risk.get("description", ""),
                    "owner": dept_bucket,
                    "mitigation": risk.get("mitigation", []),  # Phương án giảm thiểu
                    "solution": risk.get("solution", [])      # Phương án giải quyết
                }
                scaled_risks.append(scaled_risk)
                seen_risk_ids.add(risk_id)
                seen_risk_titles.add(risk_title.lower())
        
        # Add template risks that are not in knowledge base (no duplicates)
        for risk in base_risks:
            risk_id = risk["id"]
            risk_title = risk["title"]
            
            # Skip if duplicate (check both id and title)
            if risk_id in seen_risk_ids or risk_title.lower() in seen_risk_titles:
                continue
            
            scaled_risk = {
                "id": risk_id,
                "title": risk_title,
                "level": scale_risk_level(risk["base_level"], venue_tier),
                "description": risk["description"],
                "owner": dept_bucket,
                "mitigation": [],  # Empty if not in knowledge base
                "solution": []    # Empty if not in knowledge base
            }
            scaled_risks.append(scaled_risk)
            seen_risk_ids.add(risk_id)
            seen_risk_titles.add(risk_title.lower())
        
        result[dept_bucket] = scaled_risks
    
    return result


def generate_overall_risks(
    venue_tier: VenueTier,
    event_type: str = "",
    headcount_total: int = 50
) -> List[Dict[str, Any]]:
    """
    Generate overall/cross-functional risks scaled by venue tier, event type, and headcount
    
    Args:
        venue_tier: Venue tier for scaling
        event_type: Event type (concert_opening, conference, etc.)
        headcount_total: Total headcount for risk scaling
    
    Returns:
        List of overall risk dictionaries
    """
    
    # Base overall risks
    base_overall_risks = [
        {
            "id": "OVR-001",
            "title": "Nghệ sĩ/Diễn giả hủy show phút chót",
            "base_level": "critical",
            "description": "Performer chính hủy tham gia vì lý do sức khỏe, lịch trình, hoặc bất khả kháng",
        },
        {
            "id": "OVR-002",
            "title": "Đám đông quá tải, mất kiểm soát",
            "base_level": "critical",
            "description": "Số lượng khách vượt quá dự kiến, gây nguy hiểm về an toàn",
        },
        {
            "id": "OVR-003",
            "title": "Phối hợp giữa các ban kém",
            "base_level": "medium",
            "description": "Thiếu communication giữa các ban, dẫn đến sai sót hoặc chồng chéo công việc",
        },
        {
            "id": "OVR-004",
            "title": "Giấy phép/IC-PDP chậm trễ",
            "base_level": "high",
            "description": "Hồ sơ xin phép không được duyệt đúng hạn, phải hoãn sự kiện",
        },
        {
            "id": "OVR-005",
            "title": "Sự cố y tế khẩn cấp",
            "base_level": "high",
            "description": "Khách tham dự hoặc staff bị thương, cần xử lý y tế khẩn cấp",
        },
        {
            "id": "OVR-006",
            "title": "Conflict lịch trình giữa các nhiệm vụ",
            "base_level": "medium",
            "description": "Các task dependencies không được resolve đúng, gây trễ timeline",
        },
        {
            "id": "OVR-007",
            "title": "Nhân sự chủ chốt nghỉ đột xuất",
            "base_level": "high",
            "description": "Leader hoặc key person không thể tham gia, ảnh hưởng toàn bộ kế hoạch",
        },
    ]
    
    # Event-type specific overall risks
    event_specific_overall = {
        "concert_opening": [
            {
                "id": "OVR-CON-001",
                "title": "Nghệ sĩ hủy show phút chót",
                "base_level": "critical",
                "description": "Performer chính không thể tham gia, cần có backup performer hoặc hoãn sự kiện"
            },
        ],
        "career_fair": [
            {
                "id": "OVR-CF-001",
                "title": "Nhà tuyển dụng rút lui phút chót",
                "base_level": "high",
                "description": "Các công ty lớn hủy tham gia, ảnh hưởng đến chất lượng sự kiện"
            },
        ],
        "conference": [
            {
                "id": "OVR-CONF-001",
                "title": "Diễn giả chính không thể tham gia",
                "base_level": "critical",
                "description": "Keynote speaker hủy tham gia, cần tìm người thay thế"
            },
        ],
    }
    
    # Headcount-specific overall risks
    headcount_overall_risks = [
        {
            "id": "OVR-HC-001",
            "title": "Quá tải hạ tầng địa điểm",
            "base_level": "critical",
            "description": f"Với {headcount_total} người, địa điểm có thể không đủ sức chứa, cần backup venue"
        },
        {
            "id": "OVR-HC-002",
            "title": "Thiếu nhân sự quản lý",
            "base_level": "high",
            "description": f"Số lượng người tham dự lớn ({headcount_total}) cần nhiều nhân sự quản lý hơn dự kiến"
        },
    ] if headcount_total >= 100 else []
    
    # Combine all overall risks
    all_overall_risks = base_overall_risks.copy()
    
    # Add event-type specific risks
    if event_type and event_type in event_specific_overall:
        all_overall_risks.extend(event_specific_overall[event_type])
    
    # Add headcount-specific risks
    all_overall_risks.extend(headcount_overall_risks)
    
    # Scale based on venue tier
    scaled_overall = []
    for risk in all_overall_risks:
        scaled_risk = {
            "id": risk["id"],
            "title": risk["title"],
            "level": scale_risk_level(risk["base_level"], venue_tier),
            "description": risk["description"],
            "owner": None,  # Overall risks don't belong to specific department
            "mitigation": [],  # Phương án giảm thiểu (có thể bổ sung sau)
            "solution": []     # Phương án giải quyết (có thể bổ sung sau)
        }
        scaled_overall.append(scaled_risk)
    
    return scaled_overall





# Example usage
if __name__ == "__main__":
    departments = ["Hậu cần", "Marketing", "Chuyên môn", "Tài chính"]
    
    print("=== RISKS BY DEPARTMENT (XL Venue) ===")
    dept_risks = generate_risks_by_department(departments, "XL")
    for dept, risks in dept_risks.items():
        print(f"\n{dept.upper()}:")
        for risk in risks:
            print(f"  [{risk['level']:8}] {risk['title']}")
    
    print("\n\n=== OVERALL RISKS (XL Venue) ===")
    overall = generate_overall_risks("XL")
    for risk in overall:
        print(f"  [{risk['level']:8}] {risk['title']}")