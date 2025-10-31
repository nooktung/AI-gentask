from typing import Dict, List, Any
from venue_classifier import VenueTier, scale_risk_level


def generate_risks_by_department(
    departments: List[str],
    venue_tier: VenueTier,
    event_type: str = ""
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate risks grouped by department and scaled by venue tier
    
    Returns:
        Dict with department names as keys and list of risks as values
    """
    
    # Risk catalog by department
    risk_catalog = {
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
    }
    
    # Generate risks by department with venue scaling
    result = {}
    
    for dept in departments:
        # Normalize department name to standard bucket
        dept_bucket = _normalize_department(dept)
        
        if dept_bucket not in risk_catalog:
            continue
        
        # Get base risks for this department
        base_risks = risk_catalog[dept_bucket]
        
        # Scale risks based on venue tier
        scaled_risks = []
        for risk in base_risks:
            scaled_risk = {
                "id": risk["id"],
                "title": risk["title"],
                "level": scale_risk_level(risk["base_level"], venue_tier),
                "description": risk["description"],
                "owner": dept_bucket,
            }
            scaled_risks.append(scaled_risk)
        
        result[dept_bucket] = scaled_risks
    
    return result


def generate_overall_risks(
    venue_tier: VenueTier,
    event_type: str = ""
) -> List[Dict[str, Any]]:
    """
    Generate overall/cross-functional risks scaled by venue tier
    """
    
    overall_risks = [
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
    
    # Scale based on venue tier
    scaled_overall = []
    for risk in overall_risks:
        scaled_risk = {
            "id": risk["id"],
            "title": risk["title"],
            "level": scale_risk_level(risk["base_level"], venue_tier),
            "description": risk["description"],
            "owner": None,  # Overall risks don't belong to specific department
        }
        scaled_overall.append(scaled_risk)
    
    return scaled_overall


def _normalize_department(dept: str) -> str:
    """Normalize department name to standard bucket"""
    dept_lower = dept.lower().strip()
    
    if any(k in dept_lower for k in ["hậu cần", "hau can", "logistics", "vận hành"]):
        return "hậu cần"
    if any(k in dept_lower for k in ["media", "marketing", "maketing", "truyền thông", "truyen thong"]):
        return "marketing"
    if any(k in dept_lower for k in ["chuyên môn", "chuyen mon", "technical", "it", "kỹ thuật"]):
        return "chuyên môn"
    if any(k in dept_lower for k in ["tài chính", "tai chinh", "finance"]):
        return "tài chính"
    
    return dept  # Return original if can't normalize


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