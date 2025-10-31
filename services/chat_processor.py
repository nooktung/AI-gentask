"""
Chat Processor - Conversational planner with basic RAG hooks
Features:
- Conversational AI (greetings/small talk)
- Context-aware per session
- Event planning and querying over WBS

UPDATED: Works with 'departments' containing full task info (no separate 'tasks')
"""

import re
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import pytz
try:
    from openai import OpenAI  # optional dependency
except Exception:
    OpenAI = None  # type: ignore
try:
    from dotenv import load_dotenv  # optional dependency
except Exception:
    def load_dotenv() -> None:  # type: ignore
        return None
from services.pipeline import run_pipeline

load_dotenv()


class ChatProcessor:
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.client = OpenAI() if os.getenv("OPENAI_API_KEY") else None
        
    def process_message(self, message: str, session_id: str) -> Dict[str, Any]:
        """
        Process user message with full conversational capability
        """
        # Initialize session
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "created_at": datetime.now(),
                "last_updated": datetime.now(),
                "messages": [],
                "current_event": None,  # Current active event
                "events": {},  # All events in this session {event_id: event_data}
                "context": "greeting",  # greeting, planning, querying
            }
        
        session = self.sessions[session_id]
        
        # Add user message
        session["messages"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Determine intent
        intent = self._classify_intent(message, session)
        
        # Route to appropriate handler
        if intent == "greeting":
            response = self._handle_greeting(message, session)
        elif intent == "event_planning":
            response = self._handle_event_planning(message, session)
        elif intent == "event_query":
            response = self._handle_event_query(message, session)
        elif intent == "context_switch":
            response = self._handle_context_switch(message, session)
        elif intent == "general_chat":
            response = self._handle_general_chat(message, session)
        else:
            response = self._handle_unknown(message, session)
        
        # Add AI response
        session["messages"].append({
            "role": "assistant",
            "content": response.get("message", ""),
            "timestamp": datetime.now().isoformat(),
            "intent": intent,
            "data": response.get("data"),
        })
        
        session["last_updated"] = datetime.now()
        
        return response
    
    def _classify_intent(self, message: str, session: Dict[str, Any]) -> str:
        """
        Classify user intent using LLM or rule-based
        """
        message_lower = message.lower().strip()
        
        # Greeting patterns (chỉ khi message ngắn và không có info khác)
        if len(message_lower) < 30:
            greeting_patterns = [
                r'^(xin chào|chào|hello|hi|hey|good morning|good afternoon)[\s!.]*$',
                r'^(bạn là ai|bạn có thể làm gì|giới thiệu)[\s!.?]*$',
            ]
            if any(re.search(p, message_lower) for p in greeting_patterns):
                return "greeting"
        
        # Event planning patterns (ưu tiên cao)
        planning_keywords = [
            'tổ chức', 'sự kiện', 'event', 'concert', 'hội nghị', 'festival',
            'khai giảng', 'khai mạc', 'bế mạc', 'opening', 'closing',
            'ngày', 'tháng', 'địa điểm', 'venue', 'người', 'headcount',
            'ban', 'department', 'team', 'hậu cần', 'marketing', 'chuyên môn', 'tài chính',
            'đường 30m', 'phòng học', 'sảnh', 'tầng',
        ]
        
        # Đếm số keywords match
        keyword_count = sum(1 for kw in planning_keywords if kw in message_lower)
        
        # Nếu có ít nhất 3 keywords hoặc có date pattern → event planning
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # DD/MM/YYYY
            r'\d{4}-\d{2}-\d{2}',       # YYYY-MM-DD
            r'ngày \d{1,2}',            # ngày 25
        ]
        has_date = any(re.search(p, message_lower) for p in date_patterns)
        
        if keyword_count >= 3 or (keyword_count >= 2 and has_date):
            return "event_planning"
        
        # Event query patterns
        query_patterns = [
            r'\b(task|công việc|deadline|tiến độ|rủi ro|risk)\b',
            r'\b(của|trong|sự kiện|event)\b',
            r'\b(show|xem|hiển thị|list)\b',
        ]
        if any(re.search(p, message_lower) for p in query_patterns) and session.get("current_event"):
            return "event_query"
        
        # Context switch patterns
        switch_patterns = [
            r'\b(chuyển sang|switch to|đổi sang|sang sự kiện)\b',
        ]
        if any(re.search(p, message_lower) for p in switch_patterns):
            return "context_switch"
        
        # Default to general chat
        return "general_chat"
    
    def _handle_greeting(self, message: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle greeting messages"""
        greeting_responses = [
            "Xin chào! 👋 Tôi là AI Assistant giúp bạn lập kế hoạch và quản lý sự kiện.",
            "Tôi có thể giúp bạn:",
            "• Tạo WBS (Work Breakdown Structure) cho sự kiện",
            "• Phân công công việc theo từng ban",
            "• Phân tích rủi ro và đề xuất giải pháp",
            "• Trả lời các câu hỏi về tiến độ sự kiện",
            "",
            "Bạn muốn bắt đầu bằng cách nào?"
        ]
        
        return {
            "message": "\n".join(greeting_responses),
            "data": None
        }
    
    def _handle_event_planning(self, message: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle event planning - extract info and generate WBS"""
        
        # Extract event information
        extracted = self._extract_event_info(message, session)
        
        # Update or create current event
        current_event = session.get("current_event")
        if not current_event:
            # Create new event
            event_id = f"EVT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            session["current_event"] = event_id
            session["events"][event_id] = extracted
        else:
            # Update existing event
            session["events"][current_event].update(extracted)
        
        event_data = session["events"][session["current_event"]]
        
        # Check if we have enough info to generate WBS
        if self._has_sufficient_info(event_data):
            # Generate WBS
            wbs_result = run_pipeline(event_data)
            
            # Store WBS in event data
            session["events"][session["current_event"]]["wbs"] = wbs_result
            
            # Generate response message
            response_msg = self._format_wbs_summary(event_data, wbs_result)
            
            # Return with departments containing full task info
            return {
                "message": response_msg,
                "data": wbs_result,
                "extracted_info": wbs_result["extracted_info"],
                "epics_task": wbs_result["epics_task"],
                "departments": wbs_result["departments"],  # Contains full task info (no separate 'tasks')
                "risks": wbs_result.get("risks", {}),
            }
        else:
            # Ask for missing info
            missing_msg = self._identify_missing_info(event_data)
            return {
                "message": missing_msg,
                "data": None,
                "extracted_info": event_data,
            }
    
    def _handle_event_query(self, message: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle queries about current event (RAG)"""
        
        current_event_id = session.get("current_event")
        if not current_event_id:
            return {
                "message": "Bạn chưa có sự kiện nào đang hoạt động. Hãy bắt đầu bằng cách mô tả sự kiện của bạn!",
                "data": None
            }
        
        event_data = session["events"][current_event_id]
        wbs = event_data.get("wbs")
        
        if not wbs:
            return {
                "message": "Sự kiện chưa có WBS. Hãy cung cấp đầy đủ thông tin để tôi tạo WBS cho bạn!",
                "data": None
            }
        
        # Use LLM to answer query based on WBS data
        if self.client:
            answer = self._llm_answer_query(message, wbs, event_data)
        else:
            answer = self._rule_based_answer_query(message, wbs, event_data)
        
        return {
            "message": answer,
            "data": wbs
        }
    
    def _handle_context_switch(self, message: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle switching to different event"""
        
        # Extract event identifier from message
        # For now, simple implementation
        events = session.get("events", {})
        
        if not events:
            return {
                "message": "Bạn chưa có sự kiện nào. Hãy tạo sự kiện mới!",
                "data": None
            }
        
        # List available events
        event_list = []
        for event_id, data in events.items():
            event_name = data.get("event_name", "Chưa đặt tên")
            event_list.append(f"• {event_id}: {event_name}")
        
        msg = "Các sự kiện hiện có:\n" + "\n".join(event_list)
        msg += "\n\nBạn muốn chuyển sang sự kiện nào? (nhắn event ID)"
        
        return {
            "message": msg,
            "data": {"events": list(events.keys())}
        }
    
    def _handle_general_chat(self, message: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general conversation"""
        
        # Use LLM for natural conversation
        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": """Bạn là AI assistant chuyên về quản lý sự kiện. 
Hãy trả lời ngắn gọn, thân thiện nhưng luôn hướng người dùng về việc lập kế hoạch sự kiện.
Không trả lời các câu hỏi ngoài phạm vi quản lý sự kiện."""
                        },
                        {"role": "user", "content": message}
                    ],
                    temperature=0.7,
                    max_tokens=200
                )
                answer = response.choices[0].message.content
            except:
                answer = "Tôi là AI giúp bạn lập kế hoạch sự kiện. Bạn cần hỗ trợ gì về sự kiện?"
        else:
            answer = "Tôi là AI giúp bạn lập kế hoạch sự kiện. Bạn cần hỗ trợ gì về sự kiện?"
        
        return {
            "message": answer,
            "data": None
        }
    
    def _handle_unknown(self, message: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle unknown intent"""
        return {
            "message": "Xin lỗi, tôi chưa hiểu ý bạn. Bạn có thể nói rõ hơn được không?",
            "data": None
        }
    
    def _extract_event_info(self, message: str, session: Dict[str, Any]) -> Dict[str, Any]:
        """Extract event information from message using LLM"""
        
        current_event_id = session.get("current_event")
        current_data = {}
        if current_event_id and current_event_id in session["events"]:
            current_data = session["events"][current_event_id]
        
        if self.client:
            try:
                system_prompt = f"""
Bạn là AI trích xuất thông tin sự kiện.

Thông tin hiện tại: {json.dumps(current_data, ensure_ascii=False)}

Nhiệm vụ: Phân tích tin nhắn và trích xuất/cập nhật thông tin sự kiện.

Quy tắc:
1. Chỉ trích xuất thông tin MỚI từ tin nhắn
2. Nếu không có thông tin mới, trả về {{}}
3. Tự động nhận diện loại sự kiện

Mapping loại sự kiện:
- concert_opening: concert, show, nhạc
- food_festival: festival, lễ hội
- conference: hội nghị, seminar, workshop
- sport_competition: thi đấu, thể thao
- career_fair: career fair, ngày hội việc làm

Trả về JSON với các trường (chỉ khi có):
- event_name: Tên sự kiện
- event_type: Loại sự kiện
- event_date: Ngày (YYYY-MM-DD)
- venue: Địa điểm
- headcount_total: Số người
- departments: Array tên ban
"""
                
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    temperature=0.1,
                    response_format={"type": "json_object"}
                )
                
                result = json.loads(response.choices[0].message.content)
                
                # Merge with current data
                merged = current_data.copy()
                merged.update(result)
                return merged
                
            except Exception as e:
                print(f"LLM extraction error: {e}")
                return current_data
        
        # Fallback to regex
        return self._extract_with_regex(message, current_data)
    
    def _extract_with_regex(self, message: str, current_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback regex extraction"""
        info = current_data.copy()
        message_lower = message.lower()
        
        # Extract event name (improved extraction)
        if not info.get("event_name"):
            # Pattern 1: "event_type + name" format
            name_patterns = [
                r'(concert|sự kiện|event|hội nghị|festival)\s+([^,\d]{5,40})',
                r'(khai giảng|khai mạc|bế mạc)(?:\s+([^,\d]{0,30}))?',
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, message_lower)
                if match:
                    if match.lastindex >= 2 and match.group(2):
                        # Has explicit name
                        info["event_name"] = f"{match.group(1).title()} {match.group(2).strip()}"
                    else:
                        # Just the type
                        info["event_name"] = match.group(1).title()
                    break
            
            # Fallback: use event_type as name
            if not info.get("event_name") and info.get("event_type"):
                type_names = {
                    "concert_opening": "Concert Khai Giảng",
                    "conference": "Hội nghị",
                    "food_festival": "Festival Ẩm thực",
                    "sport_competition": "Giải đấu",
                }
                info["event_name"] = type_names.get(info["event_type"], "Sự kiện")
        
        # Extract event type
        type_keywords = {
            "concert_opening": ["concert", "show", "nhạc", "âm nhạc", "khai giảng", "khai mạc", "opening"],
            "conference": ["hội nghị", "conference", "seminar", "workshop"],
            "food_festival": ["festival", "lễ hội", "food", "ẩm thực"],
            "sport_competition": ["thi đấu", "thể thao", "giải", "competition"],
            "career_fair": ["career fair", "ngày hội việc làm", "job fair"],
        }
        
        for event_type, keywords in type_keywords.items():
            if any(kw in message_lower for kw in keywords):
                info["event_type"] = event_type
                break
        
        # Extract date - support both DD/MM/YYYY and YYYY-MM-DD
        date_patterns = [
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', 'dmy'),  # DD/MM/YYYY
            (r'(\d{4})-(\d{2})-(\d{2})', 'ymd'),      # YYYY-MM-DD
            (r'ngày\s+(\d{1,2})[/ ](\d{1,2})[/ ](\d{4})', 'dmy'),  # ngày DD/MM/YYYY
        ]
        
        for pattern, date_format in date_patterns:
            match = re.search(pattern, message_lower)
            if match:
                if date_format == 'dmy':
                    day, month, year = match.groups()
                    try:
                        # Validate and convert to YYYY-MM-DD
                        date_obj = datetime(int(year), int(month), int(day))
                        info["event_date"] = date_obj.strftime("%Y-%m-%d")
                        break
                    except ValueError:
                        continue
                elif date_format == 'ymd':
                    info["event_date"] = match.group(0)
                    break
        
        # Extract venue
        venue_patterns = [
            r'(?:tại|ở|at|venue[::\s]+)([^,\d\.]+?)(?:\s*,|\s+với|\s+\d|$)',
            r'(đường 30m|phòng học|sảnh tòa học|tầng 5 gamma)',
        ]
        for pattern in venue_patterns:
            venue_match = re.search(pattern, message_lower)
            if venue_match:
                info["venue"] = venue_match.group(1).strip()
                break
        
        # Extract headcount
        headcount_patterns = [
            r'(\d+)\s*người',
            r'với\s+(\d+)',
            r'headcount[::\s]+(\d+)',
        ]
        for pattern in headcount_patterns:
            headcount_match = re.search(pattern, message_lower)
            if headcount_match:
                info["headcount_total"] = int(headcount_match.group(1))
                break
        
        # Extract departments
        dept_patterns = [
            r'ban\s+([^,\d]+?)(?:\s*,|\s+và|\s*$)',
            r'department[::\s]+([^,\d]+?)(?:\s*,|\s+và|\s*$)',
        ]
        
        # Common department names (include typos)
        dept_keywords = {
            "hậu cần": ["hậu cần", "hau can", "logistics", "hau can"],
            "marketing": ["marketing", "maketing", "media", "truyền thông", "truyen thong"],  # Added "maketing" typo
            "chuyên môn": ["chuyên môn", "chuyen mon", "technical", "kỹ thuật", "ky thuat"],
            "tài chính": ["tài chính", "tai chinh", "finance", "tai chinh"],
        }
        
        found_depts = []
        for dept_name, keywords in dept_keywords.items():
            if any(kw in message_lower for kw in keywords):
                # Capitalize properly
                if dept_name == "hậu cần":
                    if "Hậu cần" not in found_depts:
                        found_depts.append("Hậu cần")
                elif dept_name == "marketing":
                    if "Marketing" not in found_depts:
                        found_depts.append("Marketing")
                elif dept_name == "chuyên môn":
                    if "Chuyên môn" not in found_depts:
                        found_depts.append("Chuyên môn")
                elif dept_name == "tài chính":
                    if "Tài chính" not in found_depts:
                        found_depts.append("Tài chính")
        
        if found_depts:
            info["departments"] = found_depts  # Already unique
        
        return info
    
    def _has_sufficient_info(self, data: Dict[str, Any]) -> bool:
        """Check if we have enough info to generate WBS"""
        # Minimum requirements: event_type, event_date, departments
        # venue và headcount có thể để default
        required = ["event_date", "departments"]
        
        has_required = all(field in data and data[field] for field in required)
        
        # Nếu không có event_type, thử infer từ event_name hoặc dùng default
        if not data.get("event_type"):
            event_name = (data.get("event_name") or "").lower()
            if any(kw in event_name for kw in ["concert", "show", "khai giảng"]):
                data["event_type"] = "concert_opening"
            else:
                data["event_type"] = "conference"  # default
        
        # Nếu không có headcount, dùng default
        if not data.get("headcount_total"):
            data["headcount_total"] = 50  # default
        
        # Nếu không có venue, dùng default
        if not data.get("venue"):
            data["venue"] = "FPT University"  # default
        
        # Nếu không có event_name, generate từ event_type
        if not data.get("event_name"):
            type_names = {
                "concert_opening": "Concert",
                "conference": "Hội nghị",
                "food_festival": "Festival",
                "sport_competition": "Giải đấu",
                "career_fair": "Ngày hội việc làm"
            }
            data["event_name"] = type_names.get(data.get("event_type", ""), "Sự kiện")
        
        return has_required
    
    def _identify_missing_info(self, data: Dict[str, Any]) -> str:
        """Generate message asking for missing information"""
        missing = []
        
        if not data.get("event_name"):
            missing.append("tên sự kiện")
        if not data.get("event_type"):
            missing.append("loại sự kiện (concert, hội nghị, festival...)")
        if not data.get("event_date"):
            missing.append("ngày tổ chức")
        if not data.get("venue"):
            missing.append("địa điểm")
        if not data.get("headcount_total"):
            missing.append("số lượng người tham gia")
        if not data.get("departments"):
            missing.append("các ban tham gia (Marketing, Hậu cần...)")
        
        if not missing:
            return "Cảm ơn bạn! Tôi đã có đủ thông tin."
        
        known_info = []
        if data.get("event_name"):
            known_info.append(f"sự kiện '{data['event_name']}'")
        if data.get("venue"):
            known_info.append(f"tại {data['venue']}")
        
        context = f"Cảm ơn bạn đã cung cấp thông tin về {', '.join(known_info)}! " if known_info else ""
        
        missing_text = ", ".join(missing)
        
        return f"""{context}
Để tạo kế hoạch chi tiết, tôi cần thêm thông tin về: **{missing_text}**

Ví dụ: "Concert khai giảng ngày 25/12/2024 tại đường 30m, 50 người, có ban Marketing và Hậu cần"

Bạn có thể cung cấp thêm không? 😊"""
    
    def _format_wbs_summary(self, event_data: Dict[str, Any], wbs: Dict[str, Any]) -> str:
        """Format WBS summary message"""
        event_name = event_data.get("event_name", "Sự kiện")
        epic_count = len(wbs.get("epics_task", []))
        
        # Count total tasks from departments
        total_tasks = sum(len(tasks) for tasks in wbs.get("departments", {}).values())
        
        venue_tier = wbs["extracted_info"].get("venue_tier", "M")
        
        return f"""✅ Đã tạo thành công WBS cho "{event_name}"!

📊 **Thống kê:**
• {epic_count} Epic (nhóm công việc chính)
• {total_tasks} Task (công việc cụ thể)
• Venue tier: {venue_tier}
• Timeline: {event_data.get('event_date', 'N/A')}
• Địa điểm: {event_data.get('venue', 'Chưa xác định')}
• Quy mô: {event_data.get('headcount_total', 'N/A')} người

💡 Bạn có thể hỏi tôi về:
• "Show tasks của ban Marketing"
• "Rủi ro nào cần lưu ý?"
• "Công việc nào deadline gần nhất?"
"""
    
    def _llm_answer_query(self, question: str, wbs: Dict[str, Any], event_data: Dict[str, Any]) -> str:
        """Use LLM to answer query based on WBS data"""
        
        # Count total tasks from departments
        total_tasks = sum(len(tasks) for tasks in wbs.get("departments", {}).values())
        
        context = f"""
Dữ liệu sự kiện:
- Tên: {event_data.get('event_name')}
- Loại: {event_data.get('event_type')}
- Ngày: {event_data.get('event_date')}
- Địa điểm: {event_data.get('venue')}

Số lượng tasks: {total_tasks}
Số lượng epics: {len(wbs.get('epics_task', []))}

Departments (với số tasks):
{json.dumps({k: len(v) for k, v in wbs.get('departments', {}).items()}, ensure_ascii=False)}

Sample tasks:
{json.dumps({dept: tasks[:2] for dept, tasks in list(wbs.get('departments', {}).items())[:2]}, ensure_ascii=False, indent=2)}

Risks:
{json.dumps(wbs.get('risks', {}), ensure_ascii=False)}
"""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": f"""Bạn là AI assistant giúp trả lời câu hỏi về sự kiện dựa trên dữ liệu WBS.
Hãy trả lời chính xác, ngắn gọn dựa trên context bên dưới.
Nếu không có thông tin trong context, nói rõ là không có.

Context:
{context}
"""
                    },
                    {"role": "user", "content": question}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"Xin lỗi, tôi gặp lỗi khi xử lý câu hỏi: {str(e)}"
    
    def _rule_based_answer_query(self, question: str, wbs: Dict[str, Any], event_data: Dict[str, Any]) -> str:
        """Rule-based query answering (fallback)"""
        
        question_lower = question.lower()
        
        # Query about tasks
        if "task" in question_lower or "công việc" in question_lower:
            if "marketing" in question_lower:
                tasks = wbs["departments"].get("marketing", [])
                return f"Ban Marketing có {len(tasks)} tasks:\n" + "\n".join([f"• {t['name']}" for t in tasks[:10]])
            
            total_tasks = sum(len(tasks) for tasks in wbs.get("departments", {}).values())
            return f"Tổng cộng {total_tasks} tasks trong sự kiện."
        
        # Query about risks
        if "risk" in question_lower or "rủi ro" in question_lower:
            risks = wbs.get("risks", {})
            overall = risks.get("overall", [])
            return f"Có {len(overall)} rủi ro tổng thể. Rủi ro quan trọng nhất:\n" + "\n".join([f"• [{r['level']}] {r['title']}" for r in overall[:5]])
        
        return "Tôi có thể giúp bạn tra cứu về tasks, risks, deadline. Bạn muốn biết gì?"
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history"""
        if session_id not in self.sessions:
            raise ValueError("Session không tồn tại")
        return self.sessions[session_id]["messages"]
    
    def clear_session(self, session_id: str):
        """Clear session"""
        if session_id not in self.sessions:
            raise ValueError("Session không tồn tại")
        del self.sessions[session_id]
    
    def list_active_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions"""
        sessions = []
        for sid, data in self.sessions.items():
            sessions.append({
                "session_id": sid,
                "created_at": data["created_at"].isoformat(),
                "last_updated": data["last_updated"].isoformat(),
                "message_count": len(data["messages"]),
                "events_count": len(data.get("events", {})),
                "current_event": data.get("current_event"),
            })
        return sessions


# Example usage
if __name__ == "__main__":
    processor = ChatProcessor()
    session_id = "test-session-001"
    
    # Test conversation
    test_messages = [
        "Xin chào!",
        "Tôi muốn tổ chức concert khai giảng",
        "Ngày 25/12/2024 tại đường 30m, 50 người",
        "Ban Marketing và Hậu cần",
        "Show tasks của Marketing",
        "Rủi ro nào cần lưu ý?",
    ]
    
    for msg in test_messages:
        print(f"\n>>> USER: {msg}")
        response = processor.process_message(msg, session_id)
        print(f"<<< AI: {response['message'][:200]}...")