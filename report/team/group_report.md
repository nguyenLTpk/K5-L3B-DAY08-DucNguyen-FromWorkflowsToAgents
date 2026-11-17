# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: LeThanhNguyen_Team
- Lớp: L3B
- Thành viên: xem `TEAM.md`
  - Lê Thành Nguyên (MSSV: 2A202603733)
  - Nguyễn Minh Đức (MSSV: 2A202603960)
- Commit chốt (trùng `report/team/decision_adr.md`): HEAD

## 2. Mục tiêu và cách tiếp cận

Bài toán yêu cầu giải quyết quy trình xử lý claim hoàn phí vận chuyển của LogiX-VN trên 4 kiến trúc khác nhau (Workflow, Single Agent, Orchestrator, Swarm) nhằm tìm ra kiến trúc **ít tự chủ nhất mà vẫn làm được việc**.

Để thực hiện hiệu quả trong nhóm 2 người và triệt tiêu xung đột mã nguồn (merge conflict), nhóm đã phân chia ranh giới theo chiều dọc rõ ràng:
- **Lê Thành Nguyên:** Đảm nhiệm kiến trúc tuần tự xác định Shape A (`workflow.py`), ReAct agent Shape B (`single.py`), bảo đảm tính toàn vẹn tài chính (Idempotency, Crash recovery, Host approval binding).
- **Nguyễn Minh Đức:** Đảm nhiệm kiến trúc điều phối Shape C (`orchestrator.py`), ranh giới an toàn thông tin (Handoff sanitization, chống secret/PII leak), cùng hệ thống đo lường benchmark & crash suite.

Thứ tự triển khai:
1. Xác lập môi trường và baseline test của host.
2. Hoàn thiện Shape A (`workflow`) làm mốc chuẩn (baseline) ổn định nhất.
3. Hoàn thiện Shape B (`single`) với vòng lặp ReAct có chặn số bước tối đa (step cap = 8).
4. Hoàn thiện Shape C (`orchestrator`) với bộ sanitizer lọc thông tin chặt chẽ qua allowlist.
5. Đo lường đối chứng với Shape D (`swarm_reference.py`).

## 3. Giải pháp

### Ranh giới Code / Model và Tính toán bồi hoàn
- Tiền bồi hoàn bắt buộc phải do code (`compute_compensation`) tính toán dựa trên dữ liệu chuẩn từ bảng `orders` và bảng `policies` hiện hành. Model (MockLLM) tuyệt đối không được tự tiện tính toán số tiền hoặc ra quyết định ghi tiền vào cơ sở dữ liệu.
- Mọi thao tác ghi nhận hoàn phí đều phải đi qua cổng kiểm duyệt duy nhất của host: `durability.issue_refund(conn, claim_id, proposal, crash_at=crash_at)`.
- Kiến trúc tuân thủ nguyên tắc truyền **quote đầy đủ (full quote)**: shape không tự ý trừ các khoản hoàn tiền trước đó của đơn hàng, mà để host tự kiểm tra per-order cap và khấu trừ chính xác trong cùng một transaction.

### Shape A — Workflow tuần tự (`src/lab8/shapes/workflow.py`)
- Thực hiện luồng cố định, không gọi model (0 model calls, 0 token cost).
- Đọc claim thông qua `get_claim_view` (chỉ lấy field cho phép, tránh `SELECT *`).
- Nếu thiếu `order_id` -> trả ngay `needs_info` (không ghi ledger).
- Tra cứu đơn hàng bằng `lookup_order`: nếu đơn không thuộc về principal tương ứng hoặc không tồn tại -> trả `escalated`.
- Tính quote từ bản ghi đơn hàng thông qua `compute_compensation`. Nếu quote = 0 -> trả `denied` (không gọi host).
- Nếu quote > 0 -> gọi `durability.issue_refund`. Nếu host từ chối (do thiếu approval hợp lệ hoặc đơn đã hoàn đủ) -> trả `denied` (host tự ghi nhận audit `policy_denied`). Nếu thành công -> trả `resolved`.

### Shape B — Single ReAct Agent (`src/lab8/shapes/single.py`)
- Sử dụng vòng lặp `run_react` với chặn số bước `max_steps=8`.
- Model được kích hoạt ở mỗi bước suy nghĩ để chọn các công cụ chỉ đọc (read-only tools: `get_claim_view`, `lookup_order`, `compute_compensation`).
- Model tuyệt đối không được cấp quyền gọi `issue_refund`. Sau khi vòng lặp ReAct đưa ra quyết định cuối cùng (`final`), mã nguồn shape mới đứng ra gọi `durability.issue_refund`.

### Shape C — Orchestrator (`src/lab8/shapes/orchestrator.py`)
- Orchestrator đóng vai trò trung tâm điều phối, không trực tiếp thực thi các tool tra cứu đơn hay policy mà tạo gói bàn giao `make_handoff` cho các read-only investigators.
- Bộ lọc allowlist loại bỏ hoàn toàn các secret của claim trước khi chuyển qua worker.
- Investigators được cô lập trong môi trường read-only, tuyệt đối bị chặn mọi lời gọi write tools.
- Sau khi nhận báo cáo từ investigator, Orchestrator trực tiếp kiểm tra và gọi cổng host `durability.issue_refund`.

### Tính bền vững và An toàn khi có sự cố (Durability & Crash Safety)
- Sử dụng khóa idempotency: `refund:{claim_id}`. Khi nhận yêu cầu trùng lặp hoặc gọi lại sau sự cố, hệ thống trả về kết quả đã commit trước đó mà không tạo thêm dòng mới trong ledger.
- Truyền nguyên vẹn tham số `crash_at` vào host và để `InjectedCrash` lan truyền ra ngoài, giúp hệ thống khôi phục trạng thái chuẩn xác khi chạy lại.

## 4. Kết quả

Số liệu trích xuất từ thực nghiệm benchmark (70 trials = 14 claims × 5 seeds) trong `src/reports/benchmark.json` và bộ crash test 20 điểm trong `src/reports/crash.json`:

| Kiến trúc (Shape) | Pass rate | Pass^5 | Seed Variance | Min Rate | Max Rate | Cost / Success (VND) | Mean Steps | Crash Safety |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A · Workflow** | **1.000** | **1.000** | **0.000000** | 1.000 | 1.000 | **27.86** | 2.86 | **20/20** |
| **B · Single ReAct** | 1.000 | 1.000 | 0.000000 | 1.000 | 1.000 | 29.81 | 6.57 | 20/20 |
| **C · Orchestrator** | 1.000 | 1.000 | 0.000000 | 1.000 | 1.000 | 46.43 | 3.79 | 20/20 |
| **D · Swarm (ref)** | 0.986 | 0.929 | 0.000816 | 0.929 | 1.000 | 49.57 | 2.80 | 20/20 |

### Nhận xét & Đánh giá:
- **Độ tin cậy:** Cả ba kiến trúc do nhóm xây dựng (Workflow, Single Agent, Orchestrator) đều đạt tỷ lệ pass tuyệt đối **100% (Pass rate = 1.0, Pass^5 = 1.0, Variance = 0.0)**. Ngược lại, Swarm bị rớt ở seed 55 trên claim C-002 do tin vào thông tin khai báo trong ticket của người dùng thay vì đối chiếu cơ sở dữ liệu (`status resolved != denied`).
- **Chi phí vận hành:** Workflow có chi phí thấp nhất (27.86 VND/success) do không tốn token gọi model. Single Agent tốn 29.81 VND (3.64 model calls/trial). Orchestrator tốn 46.43 VND do overhead gọi nhiều tool qua investigator. Swarm đắt nhất (49.57 VND) vì tốn nhiều lời gọi giao tiếp peer/draft.
- **Quyết định kiến trúc:** Nhóm chính thức lựa chọn **Shape A (Workflow)** cho bài toán này vì thỏa mãn hoàn hảo nguyên tắc *"ít tự chủ nhất mà vẫn làm được việc"*. Chi tiết xem `report/team/decision_adr.md`.

## 5. Khó khăn và cách xử lý

- **Xử lý xung đột quote và order cap:** Ban đầu có thể nhầm lẫn giữa việc shape tự trừ tiền đã hoàn trước đó hay host trừ. Nhóm đã bám sát docstring và contract: shape gửi toàn bộ quote, host là bên duy nhất trừ phần đã bồi hoàn để tránh bị trừ 2 lần.
- **Trace Contract v1:** Đảm bảo mọi đường nhánh return (kể cả nhánh lỗi `needs_info`, `escalated`, `denied`) đều xuất trace JSON hợp lệ có `run_id` và danh sách `events` sạch sẽ, không chứa thông tin nhạy cảm.
- **Cô lập ranh giới Handoff:** Đảm bảo `make_handoff` không bao giờ truyền nguyên context claim (chứa `parent_secret`), đồng thời runtime investigator chặn đứng mọi hành vi gọi write tools của worker.

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.
- **Lê Thành Nguyên (MSSV: 2A202603733):** Phụ trách Shape A (workflow), Shape B (single), kiểm thử tính bền vững và idempotency (`tests/test_member_a.py`).
- **Nguyễn Minh Đức (MSSV: 2A202603960):** Phụ trách Shape C (orchestrator), ranh giới Handoff, kiểm thử an toàn trace & crash recovery (`tests/test_member_b.py`), thực thi đo lường Benchmark & Crash Suite.

## 7. Hạn chế và hướng cải thiện

- MockLLM trong bài lab là mô hình giả lập theo seed, không đo lường được latency thực tế (`unavailable`).
- Trong môi trường thực tế với dữ liệu phi cấu trúc phức tạp (ảnh kiện hàng, văn bản khiếu nại dài), kiến trúc có thể cần kết hợp multimodal ReAct hoặc Multi-Agent trước khi chuyển cho Workflow xử lý nghiệp vụ tài chính.

## 8. Tài liệu tham khảo

- Giáo trình AI20K K5, Lab 8: From Workflows to Agents.
- Contract v1 & Business rules trong thư mục `docs/`.
- Google Research 2026, *Towards a Science of Scaling Agent Systems*.
