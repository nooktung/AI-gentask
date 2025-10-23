# 🤖 AI Event WBS Generator - Hệ thống tạo cấu trúc phân chia công việc sự kiện

---

## 1. Giới thiệu hệ thống

**AI Event WBS Generator** là hệ thống AI thông minh sử dụng **RAG (Retrieval-Augmented Generation)** và **LLM** để tự động tạo ra **Work Breakdown Structure (WBS)** cho các sự kiện.

### Mục tiêu chính:
- Tự động **sinh ra cấu trúc phân chia công việc (WBS)** cho các loại sự kiện khác nhau
- Tạo ra **Epics** và **Tasks** chi tiết với dependencies, timeline và phân công phù hợp
- Hỗ trợ nhiều loại sự kiện: Concert, Food Festival, Conference, Sport Competition, Career Fair
- Tích hợp **Knowledge Base** để đảm bảo tính chính xác và phù hợp với từng loại sự kiện

### Tính năng nổi bật:
- **RAG Pipeline**: Truy hồi thông tin từ Knowledge Base dựa trên loại sự kiện
- **Smart Scheduling**: Tự động tính toán timeline và dependencies giữa các tasks
- **Department Assignment**: Phân công công việc phù hợp với từng ban phụ trách
- **Milestone Tracking**: Xác định các mốc quan trọng trong quá trình tổ chức
- **Feasibility Check**: Kiểm tra tính khả thi của kế hoạch dựa trên số lượng nhân sự

---

## 2. Cấu trúc Repository
```
AI-gentask/
├─ main.py                    # Entry point FastAPI
├─ requirements.txt           # Dependencies
├─ .env                      # Cấu hình API keys (không commit)
│
├─ models/
│ └─ schemas.py              # Pydantic schemas cho API
│
├─ modules/
│ └─ wbs/                    # Work Breakdown Structure module
│    ├─ router.py            # FastAPI router cho WBS endpoints
│    ├─ generator.py         # WBS generation logic
│    ├─ scheduler.py         # Task scheduling & critical path
│    ├─ validate.py          # Input validation
│    └─ templates/
│       └─ concert_opening.json  # Event templates
│
├─ services/
│ ├─ pipeline.py             # Main pipeline orchestration
│ ├─ retriever.py            # RAG retrieval system
│ └─ llm_generator.py        # LLM integration & task generation
│
├─ kb/
│ └─ global/                 # Knowledge Base
│    ├─ career_fair.json     # Career fair event template
│    ├─ concert_festival.json # Concert event template
│    └─ workshop_ai.json     # Workshop event template
│
├─ scripts/
│ └─ ingest_global_chroma.py # KB ingestion script
│
└─ chroma_db/                # Vector database storage
```

---

## 3. Cài đặt và chạy dự án

### **Bước 1 – Cài đặt dependencies**
```bash
pip install -r requirements.txt
```

### **Bước 2 – Cấu hình môi trường**
Tạo file `.env` trong thư mục gốc:
```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxx
LLM_MODEL=gpt-4o-mini
USE_LLM=1
EMBED_MODEL=all-MiniLM-L6-v2
CHROMA_DIR=./chroma_db
CHROMA_COLLECTION=global_kb
```

### **Bước 3 – Khởi tạo Knowledge Base**
```bash
python scripts/ingest_global_chroma.py
```

### **Bước 4 – Chạy server**
```bash
python -m uvicorn main:app --reload --port 8000
```

Truy cập Swagger UI: http://127.0.0.1:8000/docs

---

## 4. API Endpoints

### **POST /api/wbs/generate**
Tạo WBS cho sự kiện mới

**Request Body:**
```json
{
  "event_name": "Concert Opening Night",
  "event_type": "concert_opening",
  "event_date": "2024-12-25",
  "start_date": "2024-12-01",
  "venue": "FPT University HCM",
  "headcount_total": 20,
  "departments": ["Hậu cần", "Media", "Đối ngoại", "Tài chính"]
}
```

**Response:**
```json
{
  "status": "ok",
  "event_id": "EVT-20241225-001",
  "meta": {
    "event_name": "Concert Opening Night",
    "event_type": "concert_opening",
    "event_date": "2024-12-25",
    "venue": "FPT University HCM",
    "headcount_total": 20,
    "generated_at": "2024-12-01"
  },
  "epics": [
    {
      "epic_id": "EP-001",
      "name": "Sân khấu & Âm thanh",
      "department": "Hậu cần",
      "description": "Hạ tầng sân khấu, âm thanh, ánh sáng, tổng duyệt"
    }
  ],
  "tasks": [
    {
      "task_id": "T-001",
      "epic_id": "EP-001",
      "name": "Khảo sát địa điểm & đo đạc",
      "depends_on": [],
      "can_parallel": false,
      "planned_start": "2024-12-01",
      "planned_end": "2024-12-02",
      "milestone": false
    }
  ],
  "milestones": [
    {
      "name": "Final Rehearsal Complete",
      "task_id": "T-015",
      "date": "2024-12-24"
    }
  ],
  "summary": {
    "epic_count": 4,
    "task_count": 20,
    "critical_path_example": ["T-001", "T-002", "T-015"],
    "feasibility": {
      "status": "feasible",
      "min_required_headcount": 15
    }
  }
}
```

---

## 5. Các loại sự kiện được hỗ trợ

| Event Type | Mô tả | Đặc điểm chính |
|------------|-------|----------------|
| `concert_opening` | Concert khai mạc | Sân khấu, âm thanh, nghệ sĩ, an ninh |
| `food_festival` | Lễ hội ẩm thực | An toàn thực phẩm, vendor, layout |
| `conference` | Hội nghị | Diễn giả, venue, đăng ký, sponsor |
| `sport_competition` | Thi đấu thể thao | Vận động viên, sân bãi, trọng tài |
| `career_fair` | Ngày hội việc làm | Doanh nghiệp, gian hàng, tuyển dụng |

---

## 6. Kiến trúc hệ thống

### **RAG Pipeline**
1. **Retrieval**: Tìm kiếm thông tin liên quan từ Knowledge Base dựa trên loại sự kiện
2. **Augmentation**: Kết hợp thông tin từ KB với input của người dùng
3. **Generation**: Sử dụng LLM để tạo ra WBS phù hợp

### **WBS Generation Process**
1. **Event Analysis**: Phân tích loại sự kiện và yêu cầu
2. **Template Selection**: Chọn template phù hợp từ Knowledge Base
3. **Epic Creation**: Tạo các Epic dựa trên departments
4. **Task Generation**: Sinh ra các task chi tiết với dependencies
5. **Scheduling**: Tính toán timeline và critical path
6. **Validation**: Kiểm tra tính khả thi và tối ưu hóa

---

## 7. Knowledge Base

Knowledge Base chứa các template sự kiện chuẩn với:
- **Event Types**: Các loại sự kiện được hỗ trợ
- **Context Tags**: Các đặc điểm ngữ cảnh (outdoor, sponsor, vip, etc.)
- **Baseline Tasks**: Danh sách task mẫu cho từng loại sự kiện
- **Milestones**: Các mốc quan trọng trong timeline

### **Cấu trúc KB Entry:**
```json
{
  "doc_id": "career_fair",
  "event_type": ["Career Fair", "Ngày hội việc làm"],
  "context_tags": ["outdoor", "sponsor", "vip"],
  "baseline_tasks": [
    {
      "name": "Lập kế hoạch truyền thông",
      "owner_department": "Media/Marketing",
      "description": "Xác định mục tiêu, kênh và timeline truyền thông",
      "priority": "high",
      "suggested_duration_days": 3,
      "dependencies": []
    }
  ],
  "milestones": [
    {
      "name": "Vendor Contracts Signed",
      "deadline": "T-30",
      "description": "Tất cả hợp đồng đã ký"
    }
  ]
}
```

---

## 8. Cấu hình nâng cao

### **Environment Variables**
```env
# OpenAI Configuration
OPENAI_API_KEY=your_api_key_here
LLM_MODEL=gpt-4o-mini
USE_LLM=1

# Embedding Model
EMBED_MODEL=all-MiniLM-L6-v2

# ChromaDB Configuration
CHROMA_DIR=./chroma_db
CHROMA_COLLECTION=global_kb

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

### **Custom Event Templates**
Thêm template mới vào `kb/global/` với cấu trúc JSON chuẩn.

---

## 9. Phát triển và đóng góp

### **Cấu trúc code chính:**
- `modules/wbs/`: Logic tạo WBS
- `services/`: RAG pipeline và LLM integration
- `models/`: Pydantic schemas
- `kb/global/`: Knowledge Base templates

### **Thêm loại sự kiện mới:**
1. Tạo file JSON template trong `kb/global/`
2. Cập nhật `EventInput` schema trong `models/schemas.py`
3. Thêm logic xử lý trong `services/llm_generator.py`
4. Chạy `scripts/ingest_global_chroma.py` để cập nhật KB

---

## 10. Troubleshooting

### **Lỗi thường gặp:**
- **ChromaDB connection error**: Kiểm tra quyền ghi trong thư mục `chroma_db/`
- **OpenAI API error**: Xác nhận API key và quota
- **Import error**: Cài đặt đầy đủ dependencies từ `requirements.txt`

### **Debug mode:**
```bash
export USE_LLM=0  # Tắt LLM, chỉ dùng template
python -m uvicorn main:app --reload --log-level debug
```

---

## 📞 Liên hệ

Dự án được phát triển bởi team AI tại FPT University.
Repository: https://github.com/nooktung/AI-gentask.git