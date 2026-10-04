# 🛸 Google Antigravity Managed Agent Studio Pro (v3.6)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/tuna1710/Google_Antigravity_Agent_Studio_Pro_v3.5/blob/main/notebooks/antigravity_studio_pro_v36.ipynb)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Giao diện Studio toàn diện và mạnh mẽ được xây dựng bằng **Gradio** để tương tác với **Google Managed Antigravity Agent** (`antigravity-preview-05-2026`) thông qua **Google GenAI Interactions API**.

---

## 🌟 Tính Năng Nổi Bật

1. **📦 Giao Diện Quản Lý Sandbox & Tệp Tin Hợp Nhất**:
   - Duyệt và xem trực tiếp các file do Agent tạo ra trong Cloud Sandbox (code, hình ảnh, báo cáo, biểu đồ,...).
   - Tải tệp từ Sandbox về máy tính cá nhân chỉ với 1 click.
   - Tải tệp từ máy lên Sandbox của Agent.
2. **🧩 Hệ Thống Kỹ Năng Tùy Biến (Custom Skills)**:
   - Tích hợp sẵn bộ kỹ năng chuẩn: Web Scraping, Data Visualization, Code Refactoring,...
   - Tự do tạo và đồng bộ kỹ năng cá nhân hóa vào môi trường Sandbox đang hoạt động.
3. **🛡️ Cơ Chế Tự Động Phục Hồi (Self-Healing Fallback)**:
   - Tự động nhận diện và khôi phục khi Sandbox hết hạn hoặc gặp lỗi kết nối.
   - Cho phép quay trở lại Sandbox cũ hoặc chọn xóa Sandbox cụ thể để giải phóng quota.
4. **📎 Hỗ Trợ Đa Phương Tiện Toàn Diện**:
   - Đính kèm tệp linh hoạt: Ảnh, PDF, CSV, Excel, TXT, JSON, Code, ZIP,...
   - Hỗ trợ dán trực tiếp ảnh từ clipboard (`Ctrl + V`).

---

## 🚀 Cài Đặt & Khởi Chạy

### 1. Yêu cầu hệ thống
- Python 3.10 trở lên.
- Đã có [Google Gemini API Key](https://aistudio.google.com/app/apikey).

### 2. Cài đặt các thư viện phụ thuộc

```bash
# Clone repository
git clone https://github.com/tuna1710/Google_Antigravity_Agent_Studio_Pro_v3.5.git
cd Google_Antigravity_Agent_Studio_Pro_v3.5

# Cài đặt thư viện
pip install -r requirements.txt
```

### 3. Cấu hình API Key

Tạo file `.env` từ mẫu `.env.example`:

```bash
cp .env.example .env
```

Mở file `.env` và điền Gemini API Key của bạn:

```env
GEMINI_API_KEY=AIzaSy...
```

*(Lưu ý: Bạn cũng có thể nhập API Key trực tiếp trên giao diện web của ứng dụng).*

### 4. Khởi chạy ứng dụng

```bash
python app.py
```

Sau khi khởi chạy thành công, mở trình duyệt và truy cập:
👉 `http://localhost:7860`

---

## 📁 Cấu Trúc Thư Mục

```text
├── app.py                     # Mã nguồn ứng dụng chính (Gradio UI + Agent Logic)
├── requirements.txt           # Danh sách thư viện phụ thuộc
├── .env.example               # Mẫu file cấu hình biến môi trường
├── .gitignore                 # Danh sách loại trừ khi commit lên Git
├── notebooks/
│   └── antigravity_studio_pro_v36.ipynb  # Notebook Colab gốc
└── README.md                  # Tài liệu hướng dẫn
```

---

## 📖 Chạy Trực Tiếp Trên Google Colab

Nếu không muốn chạy trên máy tính cá nhân, bạn có thể chạy trực tiếp notebook trên Google Colab:
- Bấm vào biểu tượng: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/16em1reTK7wKrRIxBRtGwREgwbtRWwBRQ?usp=sharing)
- Lưu API Key vào mục **Secrets (🔑)** của Colab với tên `GEMINI_API_KEY`.
- Chạy lần lượt các ô lệnh từ Bước 1 đến Bước 3.

---

## 📜 Giấy Phép & Bản Quyền

Dự án được phân phối dưới giấy phép [MIT License](LICENSE).
