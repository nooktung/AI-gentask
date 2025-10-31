"""
Department Normalizer - Centralized department name standardization
Handles typos and variations to ensure consistent department naming across the system
"""

from typing import Dict, List


# Standard department names (canonical forms)
STANDARD_DEPARTMENTS = {
    "hậu cần": "Hậu cần",
    "marketing": "Marketing", 
    "chuyên môn": "Chuyên môn",
    "tài chính": "Tài chính",
    "đối ngoại": "Đối ngoại",
}


# Keyword mappings for fuzzy matching (includes common typos)
DEPARTMENT_KEYWORDS = {
    "hậu cần": [
        "hậu cần", "hau can", "logistics", "vận hành", 
        "van hanh", "operations", "haucan"
    ],
    "marketing": [
        "marketing", "maketing", "marketting", "media", 
        "truyền thông", "truyen thong", "truyenthong"
    ],
    "chuyên môn": [
        "chuyên môn", "chuyen mon", "chuyenmon", "technical", 
        "it", "kỹ thuật", "ky thuat", "kythuat"
    ],
    "tài chính": [
        "tài chính", "tai chinh", "taichinh", "finance", 
        "accounting", "kế toán", "ke toan"
    ],
    "đối ngoại": [
        "đối ngoại", "doi ngoai", "doingoai", "external", 
        "relations", "external relations", "pr"
    ],
}


def normalize_department(dept: str) -> str:
    """
    Normalize department name to standard form
    Handles typos, case insensitivity, and Vietnamese accents
    
    Args:
        dept: Department name (can be typo, no accents, etc.)
        
    Returns:
        Standardized department name (e.g., "Hậu cần")
        
    Examples:
        >>> normalize_department("maketing")
        "Marketing"
        >>> normalize_department("HAU CAN")
        "Hậu cần"
        >>> normalize_department("tai chinh")
        "Tài chính"
    """
    if not dept:
        return dept
    
    dept_lower = dept.lower().strip()
    
    # Exact match first (fast path)
    if dept_lower in STANDARD_DEPARTMENTS:
        return STANDARD_DEPARTMENTS[dept_lower]
    
    # Fuzzy match using keywords
    for standard_key, keywords in DEPARTMENT_KEYWORDS.items():
        if any(keyword in dept_lower for keyword in keywords):
            return STANDARD_DEPARTMENTS[standard_key]
    
    # No match - return capitalized original
    return dept.strip().title()


def normalize_departments(departments: List[str]) -> List[str]:
    """
    Normalize a list of department names
    Removes duplicates after normalization
    
    Args:
        departments: List of department names (may contain typos/duplicates)
        
    Returns:
        List of standardized unique department names
        
    Examples:
        >>> normalize_departments(["maketing", "Marketing", "hau can"])
        ["Marketing", "Hậu cần"]
    """
    normalized = [normalize_department(d) for d in departments]
    
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for dept in normalized:
        if dept not in seen:
            seen.add(dept)
            unique.append(dept)
    
    return unique


def get_department_bucket(dept: str) -> str:
    """
    Get lowercase bucket name for internal processing
    
    Args:
        dept: Department name
        
    Returns:
        Lowercase bucket name (e.g., "hậu cần", "marketing")
        
    Examples:
        >>> get_department_bucket("Maketing")
        "marketing"
    """
    normalized = normalize_department(dept)
    
    # Reverse lookup in STANDARD_DEPARTMENTS
    for bucket, standard_name in STANDARD_DEPARTMENTS.items():
        if normalized == standard_name:
            return bucket
    
    return normalized.lower()


def validate_department(dept: str) -> bool:
    """
    Check if department is valid (can be normalized)
    
    Args:
        dept: Department name to validate
        
    Returns:
        True if valid department, False otherwise
        
    Examples:
        >>> validate_department("marketing")
        True
        >>> validate_department("random department")
        False
    """
    bucket = get_department_bucket(dept)
    return bucket in STANDARD_DEPARTMENTS


# Export common patterns for other modules
DEPARTMENT_BUCKETS = list(STANDARD_DEPARTMENTS.keys())
DISPLAY_NAMES = list(STANDARD_DEPARTMENTS.values())


if __name__ == "__main__":
    # Test cases
    print("="*70)
    print("DEPARTMENT NORMALIZER - TESTING")
    print("="*70)
    
    test_cases = [
        # Typos
        ("maketing", "Marketing"),
        ("hau can", "Hậu cần"),
        ("tai chinh", "Tài chính"),
        
        # Case variations
        ("MARKETING", "Marketing"),
        ("Hậu Cần", "Hậu cần"),
        
        # With spaces
        ("  marketing  ", "Marketing"),
        
        # Multiple keywords
        ("truyen thong", "Marketing"),
        ("van hanh", "Hậu cần"),
        
        # Unknown
        ("unknown dept", "Unknown Dept"),
    ]
    
    print("\n🧪 Individual Tests:")
    for input_dept, expected in test_cases:
        result = normalize_department(input_dept)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_dept}' → '{result}' (expected: '{expected}')")
    
    print("\n🧪 List Normalization Test:")
    input_list = ["maketing", "Marketing", "hau can", "Hậu cần", "tai chinh"]
    result_list = normalize_departments(input_list)
    print(f"Input: {input_list}")
    print(f"Output: {result_list}")
    print(f"Expected: ['Marketing', 'Hậu cần', 'Tài chính']")
    
    print("\n🧪 Validation Tests:")
    valid_tests = ["marketing", "hau can", "tai chinh", "random dept"]
    for dept in valid_tests:
        is_valid = validate_department(dept)
        print(f"  validate_department('{dept}') = {is_valid}")


