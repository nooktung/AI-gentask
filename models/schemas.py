from pydantic import BaseModel, field_validator, Field
from pydantic import ConfigDict
from typing import List, Optional, Literal
from datetime import datetime
import pytz


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
        # Accept flexible inputs; normalize to YYYY-MM-DD. Fallback: today's date (Asia/Bangkok)
        if not isinstance(v, str):
            return v
        val = v.strip()
        # Already YYYY-MM-DD
        if len(val) == 10 and val[4] == "-" and val[7] == "-":
            y, m, d = val.split("-")
            if y.isdigit() and m.isdigit() and d.isdigit():
                try:
                    dt = datetime(int(y), int(m), int(d))
                    return dt.strftime("%Y-%m-%d")
                except Exception:
                    pass
        # Try digits-only patterns
        digits = "".join(ch for ch in val if ch.isdigit())
        if len(digits) >= 8:
            # Case: YYYYMMDD
            y, m, d = digits[:4], digits[4:6], digits[6:8]
            try:
                dt = datetime(int(y), int(m), int(d))
                return dt.strftime("%Y-%m-%d")
            except Exception:
                # Case: DDMMYYYY
                d2, m2, y2 = digits[:2], digits[2:4], digits[4:8]
                try:
                    dt = datetime(int(y2), int(m2), int(d2))
                    return dt.strftime("%Y-%m-%d")
                except Exception:
                    pass
        # Try common separated formats
        for sep in ["/", "-", ".", " "]:
            parts = val.split(sep)
            if len(parts) == 3:
                if len(parts[0]) == 4 and parts[0].isdigit():
                    y, m, d = parts
                else:
                    d, m, y = parts
                if all(p.isdigit() for p in [y, m, d]):
                    try:
                        dt = datetime(int(y), int(m), int(d))
                        return dt.strftime("%Y-%m-%d")
                    except Exception:
                        continue
        # Fallback: today's date in Bangkok tz
        return datetime.now(pytz.timezone('Asia/Bangkok')).strftime('%Y-%m-%d')

    @field_validator("start_date")
    @classmethod
    def _normalize_start_date(cls, v: str | None):
        if v is None:
            return v
        if not isinstance(v, str):
            return v
        val = v.strip()
        if not val:
            return None
        # Reuse normalization logic of event_date
        try:
            # Try YYYY-MM-DD
            if len(val) == 10 and val[4] == "-" and val[7] == "-":
                y, m, d = val.split("-")
                if y.isdigit() and m.isdigit() and d.isdigit():
                    dt = datetime(int(y), int(m), int(d))
                    return dt.strftime("%Y-%m-%d")
        except Exception:
            pass
        digits = "".join(ch for ch in val if ch.isdigit())
        if len(digits) >= 8:
            y, m, d = digits[:4], digits[4:6], digits[6:8]
            try:
                dt = datetime(int(y), int(m), int(d))
                return dt.strftime("%Y-%m-%d")
            except Exception:
                d2, m2, y2 = digits[:2], digits[2:4], digits[4:8]
                try:
                    dt = datetime(int(y2), int(m2), int(d2))
                    return dt.strftime("%Y-%m-%d")
                except Exception:
                    pass
        for sep in ["/", "-", ".", " "]:
            parts = val.split(sep)
            if len(parts) == 3:
                if len(parts[0]) == 4 and parts[0].isdigit():
                    y, m, d = parts
                else:
                    d, m, y = parts
                if all(p.isdigit() for p in [y, m, d]):
                    try:
                        dt = datetime(int(y), int(m), int(d))
                        return dt.strftime("%Y-%m-%d")
                    except Exception:
                        continue
        return None


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
    # markdown removed; only JSON structure is provided
