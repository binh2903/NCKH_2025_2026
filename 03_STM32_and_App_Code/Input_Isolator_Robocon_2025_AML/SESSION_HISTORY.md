# Nhật ký phát triển - AML Robocon 2025 (24/03/2026)

## 1. Tổng quan Dự án
- **Thiết bị:** STM32F103 (ARM Cortex-M3).
- **Mục tiêu:** Giám sát 16 chân Input cách ly thời gian thực.
- **Giao tiếp:** UART (115200 bps), định dạng dữ liệu `IN:0xABCD`.

## 2. Các mốc quan trọng (Milestones)

### A. Khởi tạo tài liệu (`GEMINI.md`)
- Tạo file hướng dẫn cấu hình build (CMake/Keil) và sơ đồ chân (Mapping).
- Xác định xung đột tiềm ẩn trên chân `PA10` (vừa là LED vừa là RX).

### B. Sửa lỗi thư viện Serial
- **Lỗi:** `module 'serial' has no attribute 'Serial'`.
- **Nguyên nhân:** Cài đặt cả thư viện `serial` và `pyserial` gây xung đột.
- **Giải quyết:** Gỡ sạch cả hai và cài đặt lại duy nhất `pyserial`.

### C. Tối ưu hóa App Giám sát (`io_monitor.py`)
- **Vấn đề:** App bị lag, giật khi nhận dữ liệu tốc độ cao.
- **Giải pháp:**
    - Chuyển việc đọc Serial sang **luồng riêng (Threading)**.
    - Sử dụng **Hàng đợi (Queue)** để chỉ giữ lại dữ liệu mới nhất.
    - **Smart Redraw:** Chỉ vẽ lại biểu đồ khi trạng thái bit thay đổi (giảm tải CPU).

### D. Phát triển tính năng Log CSV
- Tạo thư mục `logs/` riêng biệt.
- Tự động đặt tên file theo mốc thời gian (`run_YYYYMMDD_HHMMSS.csv`).
- Thêm cột **Event_No** để đếm số lần thay đổi tín hiệu (hỗ trợ đếm xung/cảm biến).
- Cơ chế `flush()` đảm bảo dữ liệu được ghi xuống đĩa ngay cả khi app crash.

## 3. Hướng dẫn sử dụng App
1. Chạy app: `python io_monitor.py`.
2. Chọn đúng cổng COM của STM32 và nhấn **Kết nối**.
3. Nhấn **Bắt đầu ghi Log** khi robot chuẩn bị chạy trận.
4. Kiểm tra file kết quả trong thư mục `logs/`.

---
*Ghi chú: File này được tạo tự động bởi Gemini CLI để lưu lại lịch sử phiên làm việc.*
