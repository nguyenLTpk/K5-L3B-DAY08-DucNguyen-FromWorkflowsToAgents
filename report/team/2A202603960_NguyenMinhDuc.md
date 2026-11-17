# Báo cáo cá nhân — 2A202603960_NguyenMinhDuc

## 1. Thông tin thành viên

- Họ tên: Nguyễn Minh Đức
- MSSV: 2A202603960
- Email: nguyenminhduc2882005@gmail.com
- GitHub: nguyenminhduc
- Vai trò trong nhóm: Phụ trách Shape C `orchestrator`, Handoff Security, Benchmark & Evaluation

## 2. Phần việc phụ trách

- **Cài đặt Shape C (`orchestrator`):** Hiện thực hóa kiến trúc điều phối Orchestrator kết hợp cùng read-only investigators trong `src/lab8/shapes/orchestrator.py`.
- **Ranh giới an toàn Handoff & Secret Isolation:**
  - Thiết lập giao thức `make_handoff` tuân thủ nghiêm ngặt allowlist `handoff.v1`.
  - Đảm bảo investigator chỉ nhận các trường dữ kiện được phép (`FACT_KEYS`) và chỉ được cấp read-only tools (`lookup_order`, `lookup_policy`, `compute_compensation`). Tuyệt đối không cấp quyền ghi (`issue_refund`, `append_audit`).
  - Đảm bảo trace JSON xuất ra tuân thủ Trace Contract v1, không để rò rỉ canary secret (`CANARY_SECRET_*`), token hay thông tin định danh cá nhân (PII: SĐT, địa chỉ, tên hàng).
- **Thực thi đo lường & Đánh giá (Benchmark & Eval):**
  - Chạy bộ kiểm thử an toàn crash 20 kịch bản (`lab8.crash_test` đạt 20/20).
  - Chạy benchmark đối chứng 4 kiến trúc (workflow, single, orchestrator, swarm) trên 14 claims public × 5 seeds.
  - Phân tích phiếu nghiên cứu R1 (Scaling) và thực hiện ablation đối chứng giữa Workflow và Orchestrator.
- **Viết kiểm thử:** Viết bộ test `src/tests/test_member_b.py` kiểm tra chuyên biệt cho Handoff sanitization, Worker tool rejection, Trace non-leakage và Orchestrator crash/idempotency.

## 3. Đóng góp cụ thể

- **File code chính:**
  - `src/lab8/shapes/orchestrator.py`: Hoàn thiện trọn vẹn luồng điều phối, xử lý an toàn các nhánh `failed`, `needs_info`, `escalated`, `denied`, `resolved`, chuyển tiếp đúng tham số `crash_at` và re-raise `InjectedCrash` (pass 62/62 student tests).
- **Kiểm thử tác giả:**
  - `src/tests/test_member_b.py`: 4 test cases kiểm tra sâu về ranh giới bảo mật handoff, cơ chế từ chối write tool của worker, trace contract không chứa canary secret trên `C-010`, và tính bền vững idempotency/crash trên `C-011`, `C-012`.
- **Sinh artifacts & Báo cáo:**
  - Sinh thành công `src/reports/crash.json` (20/20) và `src/reports/benchmark.json`.
  - Điền phiếu nghiên cứu `report/team/research_card.md` (R1 Scaling ablation).
  - Cập nhật số liệu thực nghiệm và bảng so sánh 4 shape vào `report/team/decision_adr.md` và `report/team/group_report.md`.

## 4. Bằng chứng

- **Kết quả chạy pytest:**
  - `python -m pytest -v tests/test_member_b.py`: **4 passed** in 0.05s.
  - `python -m pytest -q -m student -o addopts= -k orchestrator`: **62 passed**, 244 deselected.
  - `python -m pytest -q -m student -o addopts=`: **248 passed** (100% xanh cả 4 shapes).
  - `python -m pytest -q` (host suite): **62 passed**, 248 deselected.
- **Số liệu Benchmark (`reports/benchmark.json`):**
  - Orchestrator đạt Pass rate = 1.000, Pass^5 = 1.000, Variance = 0.000000, Cost/success = 46.43 VND, Mean steps = 3.79.
  - Crash safety đạt 20/20 (`reports/crash.json`).
  - Secret leak / Approval bypass: 0 / 0.
- `python -m lab8.check_submission`: ra `0 FAIL`.

## 5. Công cụ AI đã dùng

- **Công cụ:** Trợ lý AI Antigravity / Gemini 3.8.
- **Mục đích:** Phân tích mã nguồn tham chiếu swarm, hỗ trợ thiết kế kịch bản kiểm thử ranh giới handoff, rà soát regex không để lộ PII trong trace.
- **Cách tự kiểm tra kết quả:** Trực tiếp chạy test cục bộ qua venv (`pytest`, `lab8.smoke`, `lab8.crash_test`, `lab8.benchmark`), chạy script thẩm định `check_submission`, và đọc trực tiếp file trace JSON của `C-010` để đối chiếu chuỗi cấm.

## 6. Tự đánh giá

- Hoàn thành xuất sắc 100% nhiệm vụ kỹ thuật và tài liệu được phân công.
- Kiến trúc Shape C vận hành mượt mà, đảm bảo ranh giới an toàn thông tin tuyệt đối giữa Orchestrator và Investigator, đồng thời cung cấp số liệu thực nghiệm đầy đủ làm căn cứ khoa học cho quyết định lựa chọn kiến trúc của nhóm.
