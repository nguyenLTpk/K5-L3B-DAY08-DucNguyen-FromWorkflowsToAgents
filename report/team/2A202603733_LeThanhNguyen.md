# Báo cáo cá nhân — 2A202603733_LeThanhNguyen (Thành viên A)

## 1. Thông tin thành viên

- Họ tên: Lê Thành Nguyên
- MSSV: 2A202603733
- Email: nguyenngungonvc@gmail.com
- GitHub: nguyenLTpk
- Vai trò trong nhóm: Thành viên A (Phụ trách Shape A `workflow`, Shape B `single`, Idempotency & Durability)

## 2. Phần việc phụ trách

- **Cài đặt Shape A (`workflow`):** Hiện thực hóa quy trình nghiệp vụ bồi hoàn phí vận chuyển tuần tự, xác định (deterministic) trong `src/lab8/shapes/workflow.py`.
- **Cài đặt Shape B (`single`):** Hiện thực hóa ReAct single agent có kiểm soát số bước tối đa (max_steps=8) trong `src/lab8/shapes/single.py`.
- **Đảm bảo cơ chế tính tiền & Durability:**
  - Tiền bồi hoàn bắt buộc do code (`compute_compensation`) tính toán, model không được quyết định số tiền.
  - Gọi `durability.issue_refund` với quote đầy đủ, host tự kiểm tra approval và trừ phần tiền đã hoàn trước đó (per-order cap).
  - Idempotency key `refund:{claim_id}` đảm bảo gọi lại nhiều lần vẫn chỉ sinh 1 dòng bồi hoàn duy nhất.
  - Chuyển tiếp tham số `crash_at` vào host và để `InjectedCrash` lan truyền ra ngoài, đảm bảo an toàn sau crash (T11, T12 pass).
- **Viết kiểm thử:** Viết bộ test `src/tests/test_member_a_durability_and_shapes.py` kiểm tra chuyên biệt cho Idempotency, Crash recovery, Order cap và Policy denied audit.
- **Tài liệu & Báo cáo:** Khởi tạo bảng thành viên trong `TEAM.md`, soạn thảo đề xuất kiến trúc trong `report/team/decision_adr.md` và các mục giải pháp kỹ thuật trong `report/team/group_report.md`.

## 3. Đóng góp cụ thể

- **File code chính:**
  - `src/lab8/shapes/workflow.py`: Hoàn thiện toàn bộ logic tuần tự (12/12 public claims pass ở seed 11, 62/62 student tests pass).
  - `src/lab8/shapes/single.py`: Hoàn thiện ReAct agent với bounded loop, dispatching read-only tools, ghi nhận thought/decision vào trace (12/12 public claims pass ở seed 11, 62/62 student tests pass).
- **Kiểm thử tác giả:**
  - `src/tests/test_member_a_durability_and_shapes.py`: 4 test cases kiểm tra sâu về idempotency replay, crash-resume resilience, policy_denied audit khi sai approval, và partial refund cap.
- **Quyết định kỹ thuật đã đưa ra:**
  - Chọn không dùng model call trong Workflow để đạt 100% deterministic, 0 variance, chi phí token = 0 và chống hoàn toàn Prompt Injection.
  - Trong Single Agent, chỉ cho phép LLM gợi ý tool đọc; sau vòng lặp ReAct, host là bên duy nhất xác thực và ghi tiền bồi hoàn.
  - Toàn bộ dữ liệu ghi vào `Trace` tuân thủ Trace Contract v1, chỉ trích xuất các trường trong allowlist từ `order_view` và `claim_view`, tuyệt đối không ghi nhận PII (số điện thoại, địa chỉ) hay `CANARY_SECRET_*`.

## 4. Bằng chứng

- **Kết quả chạy pytest của Member A:**
  - `python -m pytest -q -m student -o addopts= -k workflow`: **62 passed**, 240 deselected.
  - `python -m pytest -q -m student -o addopts= -k "single and not orchestrator and not workflow and not swarm"`: **62 passed**, 240 deselected.
  - `python -m pytest -v tests/test_member_a_durability_and_shapes.py`: **4 passed** in 0.31s.
  - `python -m pytest -q` (host suite): **58 passed**, 248 deselected in 16.73s.
  - `python -m lab8.check_submission` (phần shapes của A):
    - `[ OK ] shape workflow: format đúng, 12/12 claim public pass ở seed 11`
    - `[ OK ] shape single: format đúng, 12/12 claim public pass ở seed 11`

## 5. Công cụ AI đã dùng

- **Công cụ:** Trợ lý AI Antigravity / Gemini 3.8.
- **Mục đích:** Phân tích cấu trúc starter repo, kiểm tra ràng buộc của Trace Contract v1, hỗ trợ thiết kế kịch bản kiểm thử biên cho Idempotency và Crash recovery.
- **Cách tự kiểm tra kết quả:** Tự thực thi toàn bộ test suite cục bộ (`pytest -q`, `pytest -m student`, `lab8.smoke`), kiểm tra bằng máy qua `check_submission` và đọc trực tiếp file trace JSON để kiểm tra secret leakage.

## 6. Tự đánh giá

- Hoàn thành xuất sắc 100% nhiệm vụ kỹ thuật của Thành viên A trên local.
- Cả hai shape A và B đều vượt qua toàn bộ ma trận kiểm thử public với độ tin cậy tuyệt đối, bảo toàn toàn vẹn dữ liệu tài chính (idempotency, crash safety) và ranh giới bảo mật thông tin.
