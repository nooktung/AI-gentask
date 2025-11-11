"""
Conversational NLU Engine - Natural Language Understanding
Thay thế regex cứng nhắc bằng intent classification + entity extraction

Components:
1. Intent Classification
2. Entity Extraction  
3. Context Management
4. Response Generation
"""

from typing import Dict, List, Tuple, Optional
import re
from datetime import datetime
import random


class ConversationalNLU:
    """
    NLU framework cho chatbot tự nhiên
    
    Không dùng regex cứng, mà dùng:
    - Pattern matching linh hoạt
    - Context awareness
    - Confidence scoring
    """
    
    def __init__(self):
        self.intents = self._build_intent_database()
        self.entity_extractors = self._build_entity_extractors()
        
    def _build_intent_database(self) -> Dict:
        """Build intent patterns database"""
        
        return {
            "greeting": {
                "patterns": [
                    r"^(xin\s*chào|chào|hi|hello|hey|yo)",
                    r"^(bạn\s*là\s*ai|giới\s*thiệu)",
                    r"(chào\s*buổi|good\s*morning|good\s*afternoon)",
                ],
                "keywords": ["chào", "hi", "hello", "hey"],
                "responses": {
                    "morning": [
                        "Chào buổi sáng! ☀️ Mình là AI giúp bạn plan sự kiện. Bạn đang nghĩ đến event gì?",
                        "Sáng tốt lành! 🌅 Kể cho mình nghe về sự kiện bạn muốn tổ chức nhé!",
                    ],
                    "afternoon": [
                        "Chào buổi chiều! 👋 Sẵn sàng plan 1 event đỉnh chưa?",
                        "Hi! Buổi chiều năng suất nào! Bạn cần giúp gì về event? 🎉",
                    ],
                    "evening": [
                        "Chào buổi tối! 🌙 Làm việc tối nhỉ? Mình giúp được gì không?",
                        "Hi! Tối rồi mà vẫn plan event à? Respect! 💪 Mình giúp nhé!",
                    ],
                    "default": [
                        "Hey! 👋 Mình là AI giúp bạn tổ chức sự kiện. Bạn muốn plan event gì?",
                        "Chào bạn! 😊 Kể cho mình nghe về event của bạn nhé!",
                    ]
                }
            },
            
            "event_planning": {
                "triggers": [
                    "has_event_type",
                    "has_date",
                    "has_venue",
                    "has_headcount"
                ],
                "confidence_threshold": 0.5,  # Cần ít nhất 50% match
                "missing_prompts": {
                    "event_type": [
                        "Bạn muốn tổ chức sự kiện gì nhỉ? Concert, hội nghị, career fair, hay gì khác? 🎪",
                        "Cho mình biết loại event được không? Mình sẽ customize plan phù hợp! 🎯",
                    ],
                    "event_date": [
                        "Event diễn ra ngày nào bạn? 📅",
                        "Bạn dự định tổ chức vào lúc nào? Cho mình biết date nhé! 📆",
                    ],
                    "venue": [
                        "Địa điểm tổ chức ở đâu? Hoặc bạn cần gợi ý venue không? 📍",
                        "Venue đã có chưa? Hay cần mình suggest? 🏟️",
                    ],
                    "headcount_total": [
                        "Team tổ chức có bao nhiêu người nhỉ? 👥",
                        "Bạn có bao nhiêu người trong team plan event? 🙋",
                    ],
                    "departments": [
                        "Các team nào sẽ tham gia? (Marketing, Hậu cần, Tài chính...) 📋",
                        "Chia team như nào? Kể mình nghe nhé! 👨‍💼",
                    ]
                }
            },
            
            "ask_help": {
                "patterns": [
                    r"(giúp|help|hỗ\s*trợ|trợ\s*giúp)",
                    r"(làm\s*gì|có\s*thể|can\s*you)",
                ],
                "keywords": ["giúp", "help", "làm gì", "hỗ trợ"],
                "responses": [
                    "Mình có thể giúp bạn:\n\n✅ **Tạo WBS chi tiết** - Phân rã công việc thành tasks cụ thể\n✅ **Phân công team** - Gợi ý số người cho mỗi task\n✅ **Phân tích rủi ro** - Identify risks và mitigation plans\n✅ **Lên timeline** - Schedule deadline dựa trên CPM\n\nKể cho mình về event nhé! 🚀",
                    "Mình là AI chuyên về event planning! Có thể giúp bạn:\n\n🎯 Breakdown sự kiện thành tasks chi tiết\n👥 Suggest team size optimal\n⚠️ Identify risks trước khi gặp\n📅 Schedule timeline hợp lý\n\nBạn muốn bắt đầu từ đâu? 😊"
                ]
            },
            
            "confirm_generate": {
                "patterns": [
                    r"(tạo|generate|làm|bắt\s*đầu|start)",
                    r"(ok|oke|okay|yes|đồng\s*ý|được)",
                ],
                "keywords": ["tạo", "generate", "ok", "yes", "được"],
                "responses": [
                    "Perfect! Để mình generate WBS chi tiết cho bạn... ⚡",
                    "Ngon! Đang xử lý... 🚀",
                    "Roger that! Mình đang làm việc... 💪"
                ]
            },
            
            "gratitude": {
                "patterns": [
                    r"(cảm\s*ơn|thank|thanks|cám\s*ơn|tks)",
                ],
                "keywords": ["cảm ơn", "thank", "thanks"],
                "responses": [
                    "Không có gì! 😊 Cần gì cứ gọi mình nhé!",
                    "Hehe, easy! 🎉 Event của bạn sẽ đỉnh lắm!",
                    "You're welcome! 🙌 Good luck với event!"
                ]
            },
        }
    
    def _build_entity_extractors(self) -> Dict:
        """Build entity extraction patterns"""
        
        return {
            "event_type": {
                "patterns": [
                    (r"(concert|hòa\s*nhạc|nhạc\s*hội)", "concert_opening"),
                    (r"(hội\s*nghị|conference|seminar)", "conference"),
                    (r"(career\s*fair|ngày\s*hội\s*việc\s*làm|job\s*fair)", "career_fair"),
                    (r"(food\s*festival|lễ\s*hội\s*ẩm\s*thực|ẩm\s*thực)", "food_festival"),
                    (r"(sport|thể\s*thao|competition|thi\s*đấu)", "sport_competition"),
                    (r"(workshop|đào\s*tạo|training)", "workshop"),
                ]
            },
            
            "date": {
                "patterns": [
                    r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",  # DD/MM/YYYY
                    r"(\d{1,2}\s+tháng\s+\d{1,2})",      # DD tháng MM
                    r"(ngày\s+\d{1,2}\s+tháng\s+\d{1,2})",
                ]
            },
            
            "headcount": {
                "patterns": [
                    r"(\d+)\s*(người|members?|ppl|attendees?)",
                    r"(team|đội)\s*(\d+)",
                    r"(\d+)\s*(workers?|staff)",
                ]
            },
            
            "venue": {
                "keywords": [
                    "hội trường", "auditorium", "trung tâm", "nhà hát",
                    "sân vận động", "stadium", "arena", "convention center",
                    "outdoor", "ngoài trời", "công viên", "park"
                ]
            }
        }
    
    def process_message(
        self,
        message: str,
        context: Dict
    ) -> Dict:
        """
        Main NLU pipeline
        
        Returns:
            {
                "intent": str,
                "confidence": float,
                "entities": Dict,
                "response": str,
                "action": str  # "generate_wbs", "ask_clarification", etc
            }
        """
        
        message_lower = message.lower().strip()
        
        # Step 1: Classify intent
        intent, confidence = self._classify_intent(message_lower, context)
        
        # Step 2: Extract entities
        entities = self._extract_entities(message_lower, context)
        
        # Step 3: Determine action
        action = self._determine_action(intent, entities, context)
        
        # Step 4: Generate response
        response = self._generate_response(intent, entities, context, action)
        
        return {
            "intent": intent,
            "confidence": confidence,
            "entities": entities,
            "response": response,
            "action": action
        }
    
    def _classify_intent(
        self,
        message: str,
        context: Dict
    ) -> Tuple[str, float]:
        """
        Classify intent với confidence score
        
        Returns: (intent, confidence)
        """
        
        # Check direct patterns first
        for intent, config in self.intents.items():
            patterns = config.get("patterns", [])
            for pattern in patterns:
                if re.search(pattern, message):
                    return intent, 0.9  # High confidence
        
        # Check keywords
        for intent, config in self.intents.items():
            keywords = config.get("keywords", [])
            if any(kw in message for kw in keywords):
                return intent, 0.7  # Medium confidence
        
        # Check event_planning triggers
        triggers = self.intents["event_planning"]["triggers"]
        matches = 0
        
        if self._has_event_type(message):
            matches += 1
        if self._has_date(message):
            matches += 1
        if self._has_venue(message):
            matches += 1
        if self._has_headcount(message):
            matches += 1
        
        confidence = matches / len(triggers)
        
        if confidence >= 0.5:
            return "event_planning", confidence
        
        # Default: general chat
        return "general_chat", 0.5
    
    def _extract_entities(
        self,
        message: str,
        context: Dict
    ) -> Dict:
        """Extract entities from message"""
        
        entities = {}
        
        # Event type
        for pattern, event_type in self.entity_extractors["event_type"]["patterns"]:
            if re.search(pattern, message):
                entities["event_type"] = event_type
                break
        
        # Date
        for pattern in self.entity_extractors["date"]["patterns"]:
            match = re.search(pattern, message)
            if match:
                entities["event_date"] = match.group(0)
                break
        
        # Headcount
        for pattern in self.entity_extractors["headcount"]["patterns"]:
            match = re.search(pattern, message)
            if match:
                # Extract number
                numbers = re.findall(r'\d+', match.group(0))
                if numbers:
                    entities["headcount_total"] = int(numbers[0])
                break
        
        # Venue
        venue_keywords = self.entity_extractors["venue"]["keywords"]
        for keyword in venue_keywords:
            if keyword in message:
                entities["venue"] = keyword
                break
        
        return entities
    
    def _determine_action(
        self,
        intent: str,
        entities: Dict,
        context: Dict
    ) -> str:
        """Determine what action to take"""
        
        if intent == "event_planning":
            # Check if we have enough info
            required_fields = ["event_type", "event_date", "headcount_total"]
            missing = [f for f in required_fields if f not in entities and f not in context]
            
            if not missing:
                return "generate_wbs"
            else:
                return "ask_clarification"
        
        elif intent == "confirm_generate":
            return "generate_wbs"
        
        else:
            return "respond_only"
    
    def _generate_response(
        self,
        intent: str,
        entities: Dict,
        context: Dict,
        action: str
    ) -> str:
        """Generate natural response"""
        
        # Time-aware greeting
        hour = datetime.now().hour
        if hour < 12:
            time_context = "morning"
        elif hour < 18:
            time_context = "afternoon"
        else:
            time_context = "evening"
        
        if intent == "greeting":
            responses = self.intents["greeting"]["responses"].get(
                time_context,
                self.intents["greeting"]["responses"]["default"]
            )
            return random.choice(responses)
        
        elif intent == "event_planning" and action == "ask_clarification":
            # Identify missing info
            required = ["event_type", "event_date", "headcount_total"]
            missing = [f for f in required if f not in entities and f not in context]
            
            if missing:
                field = missing[0]
                prompts = self.intents["event_planning"]["missing_prompts"].get(field, [])
                return random.choice(prompts) if prompts else "Bạn có thể cho mình thêm thông tin không?"
        
        elif intent == "event_planning" and action == "generate_wbs":
            return "Perfect! Đã đủ thông tin. Để mình tạo WBS chi tiết cho bạn nhé! ⚡"
        
        elif intent == "ask_help":
            return random.choice(self.intents["ask_help"]["responses"])
        
        elif intent == "gratitude":
            return random.choice(self.intents["gratitude"]["responses"])
        
        else:
            return "Mình chưa hiểu lắm. Bạn thử diễn đạt lại xem? 🤔"
    
    def _has_event_type(self, message: str) -> bool:
        """Check if message has event type"""
        for pattern, _ in self.entity_extractors["event_type"]["patterns"]:
            if re.search(pattern, message):
                return True
        return False
    
    def _has_date(self, message: str) -> bool:
        """Check if message has date"""
        for pattern in self.entity_extractors["date"]["patterns"]:
            if re.search(pattern, message):
                return True
        return False
    
    def _has_venue(self, message: str) -> bool:
        """Check if message mentions venue"""
        keywords = self.entity_extractors["venue"]["keywords"]
        return any(kw in message for kw in keywords)
    
    def _has_headcount(self, message: str) -> bool:
        """Check if message has headcount"""
        for pattern in self.entity_extractors["headcount"]["patterns"]:
            if re.search(pattern, message):
                return True
        return False


# Backward compatible alias
ConversationalAI = ConversationalNLU


# Singleton
_nlu_engine = None

def get_nlu_engine() -> ConversationalNLU:
    """Get singleton instance"""
    global _nlu_engine
    if _nlu_engine is None:
        _nlu_engine = ConversationalNLU()
    return _nlu_engine