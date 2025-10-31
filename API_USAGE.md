# API Usage Guide - Event WBS Generator

## 🚀 Quick Start

### Server Info
- **URL**: `http://127.0.0.1:8000`
- **Port**: 8000
- **Docs**: `http://127.0.0.1:8000/docs`

---

## 📋 Main Endpoints

### 1. Chat-based WBS Generation (Recommended)
**Endpoint**: `POST /api/chat/generate-wbs`

Natural language interface với conversation memory.

#### Request Body:
```json
{
  "message": "Tổ chức lễ khai giảng năm học mới tại FPT University, 100 sinh viên, ngày 15/1/2025",
  "session_id": "unique-session-id"
}
```

#### Python Example:
```python
import requests

url = "http://127.0.0.1:8000/api/chat/generate-wbs"
payload = {
    "message": "Lễ khai giảng tại FPT University, 100 người, ngày 15/1/2025",
    "session_id": "session-123"
}

response = requests.post(url, json=payload)
print(response.json())
```

#### JavaScript Example:
```javascript
const axios = require('axios');

const url = 'http://127.0.0.1:8000/api/chat/generate-wbs';
const payload = {
  message: 'Lễ khai giảng tại FPT University, 100 người, ngày 15/1/2025',
  session_id: 'session-123'
};

axios.post(url, payload)
  .then(response => console.log(response.data))
  .catch(error => console.error(error));
```

#### cURL Example:
```bash
curl -X POST http://127.0.0.1:8000/api/chat/generate-wbs \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Lễ khai giảng tại FPT University, 100 người, ngày 15/1/2025",
    "session_id": "session-123"
  }'
```

---

### 2. Traditional JSON WBS Generation
**Endpoint**: `POST /api/wbs/generate`

Direct JSON input.

#### Request Body:
```json
{
  "event_type": "career_fair",
  "event_name": "Lễ khai giảng năm học 2025",
  "event_date": "2025-01-15",
  "venue": "FPT University",
  "headcount_total": 100,
  "departments": ["Hậu cần", "Media", "Tài chính"]
}
```

---

## 🎯 Supported Event Types

| Event Type | Keywords |
|-----------|----------|
| `concert_opening` | concert, hòa nhạc, show, nhạc, ca nhạc, đêm nhạc |
| `food_festival` | festival, lễ hội, food, ẩm thực, tiệc |
| `conference` | conference, hội nghị, seminar, workshop, toạ đàm, diễn đàn, talk |
| `sport_competition` | thi đấu, sport, tournament, thể thao, giải đấu, chạy |
| `career_fair` | career fair, ngày hội việc làm, job fair, tuyển dụng, hội chợ, khai giảng, tuyển sinh, tốt nghiệp, định hướng |

---

## 💬 Conversation Memory Features

### Continue Conversation
```python
# Message 1
requests.post(url, json={
    "message": "Tổ chức lễ khai giảng",
    "session_id": "session-123"
})

# Message 2 - Will remember previous context
requests.post(url, json={
    "message": "Đổi ngày thành 20/1",
    "session_id": "session-123"  # Same session
})
```

### Get Conversation History
```python
response = requests.get(f"http://127.0.0.1:8000/api/chat/sessions/session-123/history")
```

### Clear Session
```python
requests.delete(f"http://127.0.0.1:8000/api/chat/sessions/session-123")
```

### List Active Sessions
```python
response = requests.get("http://127.0.0.1:8000/api/chat/sessions")
```

---

## 📦 Response Structure

### Successful Response:
```json
{
  "session_id": "session-123",
  "message": "Đã tạo thành công WBS cho \"Lễ khai giảng\"!",
  "wbs_data": {
    "epics task": [...],
    "tasks": [...]
  },
  "extracted_info": {
    "event_name": "Lễ khai giảng",
    "event_type": "career_fair",
    "event_date": "2025-01-15",
    "venue": "FPT University",
    "headcount_total": 100,
    "departments": ["Hậu cần", "Media", "Tài chính"]
  },
  "error": null
}
```

### Missing Info Response:
```json
{
  "session_id": "session-123",
  "message": "Mình rất cảm ơn bạn vì đã cung cấp thông tin...",
  "wbs_data": null,
  "extracted_info": {...},
  "error": null
}
```

---

## 🔧 Integration Examples

### Python Integration
```python
import requests
from typing import Dict, Any

class WBSClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session_id = None
    
    def generate_wbs(self, message: str, session_id: str = None) -> Dict[str, Any]:
        if not session_id:
            session_id = f"session-{uuid.uuid4()}"
        
        url = f"{self.base_url}/api/chat/generate-wbs"
        response = requests.post(url, json={
            "message": message,
            "session_id": session_id
        })
        
        if response.status_code == 200:
            self.session_id = session_id
            return response.json()
        else:
            raise Exception(f"API Error: {response.status_code}")
    
    def update_event(self, update_message: str) -> Dict[str, Any]:
        if not self.session_id:
            raise Exception("No active session")
        
        return self.generate_wbs(update_message, self.session_id)

# Usage
client = WBSClient()
result = client.generate_wbs("Lễ khai giảng tại FPT, 100 người, ngày 15/1")
print(result['wbs_data'])

# Update
client.update_event("Đổi ngày thành 20/1")
```

### Node.js/TypeScript Integration
```typescript
class WBSClient {
  private baseUrl: string;
  private sessionId?: string;

  constructor(baseUrl: string = "http://127.0.0.1:8000") {
    this.baseUrl = baseUrl;
  }

  async generateWBS(message: string, sessionId?: string): Promise<any> {
    if (!sessionId) {
      sessionId = `session-${Date.now()}`;
    }

    const response = await fetch(`${this.baseUrl}/api/chat/generate-wbs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId })
    });

    const data = await response.json();
    this.sessionId = sessionId;
    return data;
  }

  async updateEvent(updateMessage: string): Promise<any> {
    if (!this.sessionId) {
      throw new Error('No active session');
    }
    return this.generateWBS(updateMessage, this.sessionId);
  }
}

// Usage
const client = new WBSClient();
const result = await client.generateWBS("Lễ khai giảng tại FPT, 100 người, ngày 15/1");
console.log(result.wbs_data);

await client.updateEvent("Đổi ngày thành 20/1");
```

---

## 🌐 Tích hợp vào dự án Anyf

### Frontend Call
```javascript
// In your anyf frontend
const callWBSAPI = async (eventDescription) => {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/chat/generate-wbs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: eventDescription,
        session_id: `anyf-${Date.now()}`
      })
    });
    
    const data = await response.json();
    return data.wbs_data; // Extract the WBS
  } catch (error) {
    console.error('WBS API Error:', error);
    throw error;
  }
};
```

### Backend Call (if anyf has backend)
```python
import requests

def get_wbs_from_description(description: str, session_id: str):
    """Call WBS API from anyf backend"""
    url = "http://127.0.0.1:8000/api/chat/generate-wbs"
    
    response = requests.post(url, json={
        "message": description,
        "session_id": session_id
    })
    
    if response.status_code == 200:
        return response.json()['wbs_data']
    else:
        raise Exception(f"WBS API failed: {response.status_code}")
```

---

## 📖 Full API Documentation

Visit: `http://127.0.0.1:8000/docs` for interactive Swagger documentation.


