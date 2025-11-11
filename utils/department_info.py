"""
Department Information - Nhiệm vụ và ghi chú của từng ban
Lưu trữ thông tin chi tiết về nhiệm vụ và các sự kiện đặc biệt mà ban xuất hiện
"""

from typing import Dict, List, Optional


# Thông tin chi tiết về từng ban
DEPARTMENT_INFO = {
    "Team Core": {
        "display_name": "Team Core",
        "normalized_name": "core",
        "responsibilities": [
            "Là đầu não của Ban Tổ chức",
            "Gồm các Trưởng ban nắm quyền điều hành",
            "Điều phối sự kiện và các ban"
        ],
        "special_events": [],  # Xuất hiện ở mọi sự kiện
        "keywords": ["core", "team core", "đầu não", "điều hành", "trưởng ban"]
    },
    "Hậu cần - Thiết công": {
        "display_name": "Hậu cần - Thiết công",
        "normalized_name": "hậu cần",
        "responsibilities": [
            "Lên bản vẽ, kế hoạch thực hiện các khu vực trang trí trong sự kiện",
            "Xây dựng các khu vực đó và các vật dụng liên quan đến khu vực trang trí",
            "Mua đồ, bảo quản lưu trữ đồ của sự kiện"
        ],
        "special_events": [],  # Xuất hiện ở mọi sự kiện
        "keywords": ["hậu cần", "hau can", "logistics", "thiết công", "thiet cong", "vận hành", "van hanh"]
    },
    "Takecare": {
        "display_name": "Ban Takecare",
        "normalized_name": "takecare",
        "responsibilities": [
            "Phụ trách những đầu việc liên quan đến khách mời",
            "Quản lý những vị trí backstage",
            "Quản lý gian hàng"
        ],
        "special_events": [],  # Xuất hiện ở mọi sự kiện
        "keywords": ["takecare", "take care", "khách mời", "khach moi", "backstage", "gian hàng", "gian hang"]
    },
    "Nội dung": {
        "display_name": "Ban Nội dung",
        "normalized_name": "nội dung",
        "responsibilities": [
            "Lên kế hoạch, concept, timeline",
            "Xây dựng key activities cho toàn bộ chương trình",
            "Phát triển nội dung chương trình"
        ],
        "special_events": [],  # Xuất hiện ở mọi sự kiện
        "keywords": ["nội dung", "noi dung", "content", "concept", "timeline", "key activities"]
    },
    "Truyền thông": {
        "display_name": "Ban Truyền thông",
        "normalized_name": "marketing",
        "responsibilities": [
            "Xây dựng và triển khai kế hoạch truyền thông cho sự kiện",
            "Đảm bảo timeline và hiệu quả truyền thông",
            "Viết content theo tuyến bài truyền thông (Facebook, TikTok, Reels…)",
            "Sáng tạo nội dung truyền thông đa dạng: bài viết, hình ảnh, video ngắn, reel",
            "Phối hợp cùng Ban Nội dung, Media và Design để sản xuất các ấn phẩm truyền thông đồng bộ"
        ],
        "special_events": [],  # Xuất hiện ở mọi sự kiện
        "keywords": ["truyền thông", "truyen thong", "marketing", "media", "content", "facebook", "tiktok"]
    },
    "Design": {
        "display_name": "Ban Design",
        "normalized_name": "thiết kế",
        "responsibilities": [
            "Thiết kế các ấn phẩm truyền thông cho chương trình (poster, banner, backdrop, standee, vé mời, lookbook…)",
            "Hỗ trợ thiết kế ấn phẩm mạng xã hội (bài đăng, story, cover event, infographic…)",
            "Phối hợp cùng Ban Truyền thông để xây dựng hình ảnh thống nhất cho sự kiện",
            "Hỗ trợ thiết kế ấn phẩm sân khấu (visual LED, backdrop chính, signage)",
            "Chỉnh sửa và hoàn thiện file thiết kế phục vụ in ấn và trình chiếu"
        ],
        "special_events": [],  # Xuất hiện ở mọi sự kiện
        "keywords": ["design", "thiết kế", "thiet ke", "graphic", "poster", "banner", "backdrop"]
    },
    "Media": {
        "display_name": "Ban Media",
        "normalized_name": "media",
        "responsibilities": [
            "Chụp ảnh của sự kiện",
            "Phụ trách những bức hình và video xuyên suốt toàn bộ sự kiện",
            "Làm VJ (Video Jockey)"
        ],
        "special_events": [],  # Xuất hiện ở mọi sự kiện
        "keywords": ["media", "chụp ảnh", "chup anh", "video", "vj", "photography", "videography"]
    },
    "Nhà Ma": {
        "display_name": "Ban Nhà Ma",
        "normalized_name": "nhà ma",
        "responsibilities": [
            "Thiết kế nhà ma",
            "Xây dựng nhà ma",
            "Phát triển nội dung cốt chuyện, hình ảnh, con người của nhà ma"
        ],
        "special_events": ["halloween", "Halloween"],  # Chỉ xuất hiện ở Halloween
        "keywords": ["nhà ma", "nha ma", "haunted house", "halloween"]
    },
    "Lập trình": {
        "display_name": "Ban Lập trình",
        "normalized_name": "lập trình",
        "responsibilities": [
            "Thiết kế web để đưa thông tin của sự kiện đến với mọi người",
            "Phát triển website sự kiện",
            "Quản lý hệ thống đăng ký trực tuyến"
        ],
        "special_events": ["debate", "Debate"],  # Thấy ở Debate
        "keywords": ["lập trình", "lap trinh", "programming", "web", "website", "developer", "coding"]
    },
    "Đối ngoại": {
        "display_name": "Ban Đối ngoại",
        "normalized_name": "đối ngoại",
        "responsibilities": [
            "Liên hệ, làm việc, hợp tác với các nhà tài trợ",
            "Xin kinh phí tổ chức sự kiện",
            "Làm các giấy tờ hợp đồng"
        ],
        "special_events": [],  # Xuất hiện ở mọi sự kiện
        "keywords": ["đối ngoại", "doi ngoai", "external", "relations", "sponsor", "tài trợ", "tai tro"]
    },
    "Tài chính": {
        "display_name": "Ban Tài chính",
        "normalized_name": "tài chính",
        "responsibilities": [
            "Tổng hợp tiền của sự kiện",
            "Duyệt các khoản chi tiêu sao cho hợp lý",
            "Quản lý ngân sách và quyết toán"
        ],
        "special_events": [],  # Xuất hiện ở mọi sự kiện
        "keywords": ["tài chính", "tai chinh", "finance", "accounting", "kế toán", "ke toan", "ngân sách"]
    },
    "Nhân sự": {
        "display_name": "Ban Nhân sự (HR)",
        "normalized_name": "nhân sự",
        "responsibilities": [
            "Quản lý nhân sự của Ban tổ chức",
            "Theo dõi trạng thái nhân sự của từng ban",
            "Theo dõi trạng thái của từng cá nhân"
        ],
        "special_events": [],  # Xuất hiện ở mọi sự kiện
        "keywords": ["nhân sự", "nhan su", "hr", "human resources", "quản lý nhân sự"]
    },
    "Game": {
        "display_name": "Team Game",
        "normalized_name": "game",
        "responsibilities": [
            "Phát triển nội dung trò chơi theo chặng, theo vòng",
            "Test game, fix game để phù hợp với chương trình",
            "Quản lý và điều hành các trò chơi trong sự kiện"
        ],
        "special_events": [],  # Xuất hiện ở nhiều sự kiện
        "keywords": ["game", "trò chơi", "tro choi", "gaming", "game development"]
    },
    "Trình diễn": {
        "display_name": "Ban Trình diễn",
        "normalized_name": "trình diễn",
        "responsibilities": [
            "Trình diễn, biểu diễn các tiết mục văn hóa, nghệ thuật của sự kiện"
        ],
        "special_events": ["icon", "ICON", "fashion", "music", "thời trang", "âm nhạc"],  # Thấy ở ICON, thời trang, âm nhạc
        "keywords": ["trình diễn", "trinh dien", "performance", "biểu diễn", "bieu dien", "show"]
    },
    "Cố vấn": {
        "display_name": "Ban Cố vấn",
        "normalized_name": "cố vấn",
        "responsibilities": [
            "Gồm những thành viên kì cựu của những sự kiện trước",
            "Cố vấn, hỗ trợ chuyên môn",
            "Đồng hành cùng Ban tổ chức sự kiện"
        ],
        "special_events": [],  # Xuất hiện ở mọi sự kiện
        "keywords": ["cố vấn", "co van", "advisor", "mentor", "consultant"]
    },
    "Chuyên môn": {
        "display_name": "Ban Chuyên môn",
        "normalized_name": "chuyên môn",
        "responsibilities": [
            "Tùy sự kiện: FTIC thì là tập luyện và biểu diễn nhạc cụ truyền thống",
            "FChess thì là hỗ trợ chuyên môn",
            "Phụ trách các vấn đề chuyên môn đặc thù của sự kiện"
        ],
        "special_events": ["ftic", "FTIC", "fchess", "FChess"],  # Thấy ở FTIC, FChess
        "keywords": ["chuyên môn", "chuyen mon", "technical", "specialized", "expertise"]
    },
    "Kỹ thuật": {
        "display_name": "Ban Kỹ thuật",
        "normalized_name": "chuyên môn",
        "responsibilities": [
            "Phụ trách vấn đề về kĩ thuật",
            "Quản lý âm thanh, ánh sáng",
            "Quản lý thiết bị của sự kiện"
        ],
        "special_events": [],  # Xuất hiện ở mọi sự kiện
        "keywords": ["kỹ thuật", "ky thuat", "technical", "sound", "lighting", "equipment", "âm thanh", "ánh sáng"]
    },
    "Quản lý model": {
        "display_name": "Ban Quản lý model",
        "normalized_name": "quản lý model",
        "responsibilities": [
            "Quản lý, theo sát và hỗ trợ model từ khâu casting, fitting, rehearsal cho đến D-day",
            "Là cầu nối giữa model và các ban khác (Trang phục, Make-up, Chăm sóc, Hậu cần,...)",
            "Phối hợp lịch trình hiệu quả",
            "Giám sát, xử lý tình huống phát sinh liên quan đến model trong suốt sự kiện"
        ],
        "special_events": ["inflame", "Inflame", "fashion", "thời trang"],  # Thấy ở Inflame
        "keywords": ["quản lý model", "quan ly model", "model management", "casting", "fitting"]
    },
    "Văn thể mĩ": {
        "display_name": "Ban Văn thể mĩ",
        "normalized_name": "văn thể mĩ",
        "responsibilities": [
            "Hoạt náo",
            "Lên các tiết mục văn nghệ cho sự kiện"
        ],
        "special_events": [],  # Xuất hiện ở nhiều sự kiện
        "keywords": ["văn thể mĩ", "van the mi", "hoạt náo", "hoat nao", "văn nghệ", "van nghe", "entertainment"]
    },
}


def get_department_info(dept_name: str) -> Optional[Dict]:
    """
    Lấy thông tin chi tiết về một ban
    
    Args:
        dept_name: Tên ban (có thể là bất kỳ variation nào)
        
    Returns:
        Dict với thông tin ban hoặc None nếu không tìm thấy
    """
    dept_lower = dept_name.lower().strip()
    
    # Tìm theo keywords
    for dept_key, info in DEPARTMENT_INFO.items():
        keywords = info.get("keywords", [])
        if any(kw in dept_lower for kw in keywords):
            return info
    
    # Tìm theo normalized_name
    for dept_key, info in DEPARTMENT_INFO.items():
        if info["normalized_name"].lower() == dept_lower:
            return info
    
    # Tìm theo display_name
    for dept_key, info in DEPARTMENT_INFO.items():
        if info["display_name"].lower() == dept_lower:
            return info
    
    return None


def get_department_responsibilities(dept_name: str) -> List[str]:
    """
    Lấy danh sách nhiệm vụ của một ban
    
    Args:
        dept_name: Tên ban
        
    Returns:
        List các nhiệm vụ hoặc empty list nếu không tìm thấy
    """
    info = get_department_info(dept_name)
    if info:
        return info.get("responsibilities", [])
    return []


def get_department_special_events(dept_name: str) -> List[str]:
    """
    Lấy danh sách các sự kiện đặc biệt mà ban xuất hiện
    
    Args:
        dept_name: Tên ban
        
    Returns:
        List các sự kiện đặc biệt (empty list = xuất hiện ở mọi sự kiện)
    """
    info = get_department_info(dept_name)
    if info:
        return info.get("special_events", [])
    return []


def is_department_for_event(dept_name: str, event_type: str) -> bool:
    """
    Kiểm tra xem ban có xuất hiện trong sự kiện này không
    
    Args:
        dept_name: Tên ban
        event_type: Loại sự kiện (e.g., "halloween", "debate", "icon")
        
    Returns:
        True nếu ban xuất hiện trong sự kiện này
    """
    info = get_department_info(dept_name)
    if not info:
        return True  # Default: assume present if unknown
    
    special_events = info.get("special_events", [])
    
    # Nếu không có special_events → xuất hiện ở mọi sự kiện
    if not special_events:
        return True
    
    # Nếu có special_events → chỉ xuất hiện ở các sự kiện đó
    event_type_lower = event_type.lower()
    return any(se.lower() in event_type_lower or event_type_lower in se.lower() for se in special_events)


def get_all_departments_for_event(event_type: str) -> List[Dict]:
    """
    Lấy danh sách tất cả các ban phù hợp với sự kiện
    
    Args:
        event_type: Loại sự kiện
        
    Returns:
        List các dict thông tin ban
    """
    result = []
    for dept_key, info in DEPARTMENT_INFO.items():
        if is_department_for_event(dept_key, event_type):
            result.append({
                "name": info["display_name"],
                "normalized_name": info["normalized_name"],
                "responsibilities": info["responsibilities"],
                "special_events": info["special_events"]
            })
    return result


def get_department_suggestions(user_input: str) -> List[str]:
    """
    Gợi ý các ban dựa trên input của user
    
    Args:
        user_input: Input từ user (có thể là mô tả công việc)
        
    Returns:
        List các tên ban phù hợp
    """
    user_input_lower = user_input.lower()
    suggestions = []
    
    for dept_key, info in DEPARTMENT_INFO.items():
        # Check keywords
        keywords = info.get("keywords", [])
        if any(kw in user_input_lower for kw in keywords):
            suggestions.append(info["display_name"])
            continue
        
        # Check responsibilities
        responsibilities = info.get("responsibilities", [])
        if any(resp.lower() in user_input_lower or user_input_lower in resp.lower() for resp in responsibilities):
            suggestions.append(info["display_name"])
    
    return list(set(suggestions))  # Remove duplicates


if __name__ == "__main__":
    # Test
    print("="*70)
    print("DEPARTMENT INFO - TESTING")
    print("="*70)
    
    # Test get_department_info
    print("\n🧪 Test get_department_info:")
    test_depts = ["marketing", "truyền thông", "design", "thiết kế", "nhà ma"]
    for dept in test_depts:
        info = get_department_info(dept)
        if info:
            print(f"  ✅ '{dept}' → {info['display_name']}")
            print(f"     Responsibilities: {len(info['responsibilities'])} items")
            print(f"     Special events: {info['special_events']}")
        else:
            print(f"  ❌ '{dept}' → Not found")
    
    # Test is_department_for_event
    print("\n🧪 Test is_department_for_event:")
    test_cases = [
        ("nhà ma", "halloween", True),
        ("nhà ma", "career_fair", False),
        ("truyền thông", "halloween", True),
        ("truyền thông", "career_fair", True),
        ("lập trình", "debate", True),
        ("lập trình", "halloween", False),
    ]
    for dept, event, expected in test_cases:
        result = is_department_for_event(dept, event)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{dept}' in '{event}' = {result} (expected: {expected})")
    
    # Test get_all_departments_for_event
    print("\n🧪 Test get_all_departments_for_event:")
    for event in ["halloween", "debate", "career_fair"]:
        depts = get_all_departments_for_event(event)
        print(f"  '{event}': {len(depts)} departments")
        print(f"    {', '.join([d['name'] for d in depts[:5]])}...")




