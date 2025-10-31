from pydantic import BaseModel, field_validator, Field
from pydantic import ConfigDict
from typing import List, Optional, Literal
from datetime import datetime, timedelta
import pytz


class DateValidationError(ValueError):
    """Custom exception for date validation failures"""
    pass


class EventInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    event_name: str
    event_type: Literal[
        "concert_opening",
        "food_festival",
        "conference",
        "sport_competition",
        "career_fair",
    ]
    event_date: str  # YYYY-MM-DD
    start_date: str | None = Field(default=None, alias="start-date")
    venue: str
    headcount_total: int
    departments: List[str]

    @field_validator("event_name", "event_type", "event_date", "start_date", "venue")
    @classmethod
    def _strip_strings(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("event_date")
    @classmethod
    def _normalize_event_date(cls, v: str):
        """
        Normalize event_date to YYYY-MM-DD format with robust parsing
        Raises DateValidationError if date is invalid
        """
        if not isinstance(v, str):
            raise DateValidationError(f"event_date must be string, got {type(v)}")
        
        val = v.strip()
        
        if not val:
            raise DateValidationError("event_date cannot be empty")
        
        # Try YYYY-MM-DD format (standard)
        if len(val) == 10 and val[4] == "-" and val[7] == "-":
            parts = val.split("-")
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                y, m, d = parts
                try:
                    dt = datetime(int(y), int(m), int(d))
                    # Validate date is not too far in the past (> 1 year ago)
                    one_year_ago = datetime.now() - timedelta(days=365)
                    if dt.date() < one_year_ago.date():
                        raise DateValidationError(
                            f"event_date {val} is more than 1 year in the past"
                        )
                    return dt.strftime("%Y-%m-%d")
                except ValueError as e:
                    raise DateValidationError(f"Invalid date: {val} - {str(e)}")
        
        # Try parsing digits-only patterns
        digits = "".join(ch for ch in val if ch.isdigit())
        
        if len(digits) == 8:
            # Case: YYYYMMDD
            y, m, d = digits[:4], digits[4:6], digits[6:8]
            try:
                dt = datetime(int(y), int(m), int(d))
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass
            
            # Case: DDMMYYYY
            d2, m2, y2 = digits[:2], digits[2:4], digits[4:8]
            try:
                dt = datetime(int(y2), int(m2), int(d2))
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                pass
        
        # Try common separated formats
        for sep in ["/", "-", ".", " "]:
            if sep in val:
                parts = val.split(sep)
                if len(parts) == 3 and all(p.strip().isdigit() for p in parts):
                    # Determine format based on first part length
                    if len(parts[0].strip()) == 4:  # YYYY-MM-DD or YYYY/MM/DD
                        y, m, d = [p.strip() for p in parts]
                    else:  # DD-MM-YYYY or DD/MM/YYYY
                        d, m, y = [p.strip() for p in parts]
                    
                    try:
                        dt = datetime(int(y), int(m), int(d))
                        return dt.strftime("%Y-%m-%d")
                    except ValueError:
                        continue
        
        # If all parsing fails, raise error instead of defaulting
        raise DateValidationError(
            f"Cannot parse date '{val}'. Expected format: YYYY-MM-DD, DD/MM/YYYY, or YYYYMMDD"
        )

    @field_validator("start_date")
    @classmethod
    def _normalize_start_date(cls, v: str | None):
        """Normalize start_date using same logic as event_date"""
        if v is None or not v.strip():
            return None
        
        # Reuse event_date validation logic
        try:
            return cls._normalize_event_date(v)
        except DateValidationError:
            # For start_date, we can be more lenient and return None
            return None

    @field_validator("headcount_total")
    @classmethod
    def _validate_headcount(cls, v: int):
        """Validate headcount is reasonable"""
        if v < 1:
            raise ValueError("headcount_total must be at least 1")
        if v > 10000:
            raise ValueError("headcount_total seems unreasonably high (>10,000)")
        return v

    @field_validator("departments")
    @classmethod
    def _validate_departments(cls, v: List[str]):
        """Validate departments list is not empty"""
        if not v:
            raise ValueError("departments cannot be empty")
        if len(v) > 10:
            raise ValueError("Too many departments (>10)")
        return v


class Epic(BaseModel):
    epic_id: str
    name: str
    department: str
    description: str


class Task(BaseModel):
    task_id: str
    epic_id: str
    name: str
    duration_days: int
    depends_on: List[str]
    can_parallel: bool
    planned_start: str  # YYYY-MM-DD
    planned_end: str    # YYYY-MM-DD
    milestone: bool = False


class Milestone(BaseModel):
    name: str
    task_id: str
    date: str  # YYYY-MM-DD


class Meta(BaseModel):
    event_name: str
    event_type: str
    event_date: str
    venue: Optional[str] = None
    headcount_total: int
    generated_at: str


class WBSResponse(BaseModel):
    event_id: str
    meta: Meta
    epics: List[Epic]
    tasks: List[Task]
    milestones: List[Milestone]
    summary: dict


# Action Required schemas
class Option(BaseModel):
    id: str
    label: str
    expects_payload: Optional[dict] = None
    preview: Optional[dict] = None


class ActionRequiredResponse(BaseModel):
    status: Literal["action_required"]
    code: str
    message: str
    options: List[Option]


class ValidationResponse(BaseModel):
    status: Literal["ok"]


class WBSGenerateResponse(BaseModel):
    status: Literal["ok"]
    event_id: str
    meta: Meta
    epics: List[Epic]
    tasks: List[Task]
    milestones: List[Milestone]
    summary: dict


# New output schemas for department-based tasks and risks
class TaskRow(BaseModel):
    task_id: str
    name: str
    start_date: str  # YYYY-MM-DD
    deadline: str    # YYYY-MM-DD
    depends_on: List[str]
    complexity: Literal["low", "medium", "high", "critical"]


class DepartmentTasks(BaseModel):
    department: str
    tasks: List[TaskRow]


class RiskItem(BaseModel):
    id: str
    title: str
    level: Literal["low", "medium", "high", "critical"]
    description: str
    owner: str | None = None


class RisksBlock(BaseModel):
    by_department: dict  # {department: List[RiskItem]}
    overall: List[RiskItem]


class EventPlan(BaseModel):
    event_id: str
    departments: List[DepartmentTasks]
    risks: RisksBlock

