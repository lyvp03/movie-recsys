# 🎬 Movie Recommendation System (Movie RecSys)

Hệ thống gợi ý phim (Movie Recommendation System) với kiến trúc Clean Architecture. Dự án hỗ trợ nhiều phương pháp gợi ý phim bao gồm Content-Based, Collaborative Filtering, lai (Hybrid) và gợi ý dựa trên cảm xúc (Emotion-based).

## 🌟 Tính năng chính
- **Gợi ý phim đa dạng**: Hỗ trợ nhiều mô hình (SVD, TF-IDF, FastEmbed) và vector database (Qdrant).
- **Phân tích cảm xúc**: Gợi ý phim dựa trên cảm xúc của người dùng qua văn bản.
- **Kiến trúc mã nguồn sạch**: Áp dụng triệt để Clean Architecture (Domain, Application, Infrastructure, API) và TDD.
- **Giao diện hiện đại**: Frontend tương tác mượt mà và trực quan.

## 🏗️ Kiến trúc dự án
Dự án được chia thành 2 phần chính:
- **Backend (`backend/`)**: Python (FastAPI, Qdrant, SQLAlchemy, pytest). Tổ chức theo mô hình `api -> application -> domain <- infrastructure`.
- **Frontend (`frontend/`)**: Node.js/TypeScript (React, Vite, Vitest).

## 🚀 Hướng dẫn cài đặt

### 1. Cài đặt Backend
```bash
cd backend
python -m venv venv
# Active venv (Windows):
venv\Scripts\activate
# Active venv (macOS/Linux):
source venv/bin/activate

pip install -r ../requirements.txt
```

Thiết lập biến môi trường:
Copy file `.env.example` thành `.env` và cấu hình các thông số cần thiết (Qdrant, Database, v.v.).

### 2. Cài đặt Frontend
```bash
cd frontend
npm install
```

## 🛠️ Chạy ứng dụng

### Chạy bằng Docker
Hệ thống cung cấp sẵn `docker-compose.yml` để khởi chạy các service:
```bash
docker-compose up -d
```

### Chạy thủ công
**Backend:**
```bash
cd backend
uvicorn src.api.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm run dev
```

## 🧪 Kiểm thử (Testing)
Dự án tuân thủ Test-Driven Development (TDD).

**Backend:**
```bash
cd backend
pytest --cov=src --cov-fail-under=80
```

**Frontend:**
```bash
cd frontend
npx vitest run --coverage
```

## 📝 Quy ước Commit (Git)
Dự án áp dụng quy ước commit rõ ràng:
- `feat(scope): message` - Thêm tính năng mới
- `fix(scope): message` - Sửa lỗi
- `test(scope): message` - Thêm/Sửa test
- `refactor(scope): message` - Refactor code
- `docs(scope): message` - Cập nhật tài liệu
