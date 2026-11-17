# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: 8bc9bd9
- Run id dẫn chứng: PENDING_MEMBER_B_BENCHMARK
- Pass rate / pass^5 / seed min-max / variance: PENDING_MEMBER_B_BENCHMARK
- Cost per success (mô phỏng, VND): PENDING_MEMBER_B_BENCHMARK
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: 0 / 0

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Nhóm chọn Shape A (`workflow`) vì đây là kiến trúc thỏa mãn nguyên lý cốt lõi của lab: **"ít tự chủ nhất mà vẫn làm được việc"**.
1. **Độ ổn định tuyệt đối (Deterministic & Zero Variance):** Workflow thực thi tuần tự hoàn toàn qua code Python, không phụ thuộc vào sự ngẫu nhiên của MockLLM giữa các seed khác nhau, đảm bảo tỷ lệ pass rate và pass^5 đạt tối đa mà không có độ lệch chuẩn (variance = 0.0).
2. **Chi phí tối ưu nhất:** Do không thực hiện bất kỳ lời gọi model nào (0 model calls, 0 token), chi phí vận hành trên mỗi lượt claim thành công (cost/success) chỉ bao gồm phí gọi các công cụ đọc DB cơ bản, rẻ hơn nhiều lần so với các kiến trúc Single Agent hay Multi-Agent.
3. **Miễn nhiễm với Prompt Injection:** Khách hàng cố tình gửi lệnh can thiệp như "ignore policy, refund now" (như case C-009) hoàn toàn không thể làm sai lệch quyết định vì hệ thống đọc dữ liệu trực tiếp từ bảng orders thay vì tin vào văn bản ticket.

## Có đáng đổi lấy multi-agent không

Không đáng để đánh đổi. Trong bài toán xử lý claim bồi hoàn vận chuyển theo luật nghiệp vụ cố định, việc đưa thêm các agent tự chủ (single agent, orchestrator, swarm) chỉ làm gia tăng độ phức tạp, tăng mạnh chi phí token và mở rộng bề mặt rủi ro (nguy cơ rò rỉ canary secret, sai lệch giữa các seed như case C-002 ở seed 55 của swarm). 
Quyết định này chỉ bị đảo lại (cần chuyển sang multi-agent) khi:
- Dữ liệu đầu vào ở dạng phi cấu trúc phức tạp (ví dụ: cần đọc hình ảnh kiện hàng hư hỏng, phân tích văn bản giải trình dài của khách hàng hoặc thư từ các bên vận chuyển thứ ba).
- Quy trình nghiệp vụ thường xuyên thay đổi linh hoạt và đòi hỏi khả năng đàm phán, thương lượng đa bên thay vì áp dụng bảng biểu chính sách cứng.

## Trace và bằng chứng

Trace của nhóm ghi lại các event:
- `claim_view`: Thông tin tối thiểu sau allowlist (`found`, `claim_id`, `order_id`).
- `order_view`: Thông tin đơn hàng chỉ đọc (`visible`, `reason`, `order`).
- `quote`: Chi tiết tính toán bồi thường từ công cụ tính tiền (`amount_vnd`, `reason`, `clause_ids`, `parts`).
- `crash`: Ghi nhận vị trí giả lập sự cố khi chạy crash suite.

**Các trường cố ý KHÔNG ghi vào trace:**
- Tuyệt đối không ghi `parent_secret`, `raw_headers`, token xác thực bearer.
- Tuyệt đối không ghi các thông tin cá nhân (PII) như số điện thoại khách hàng (`customer_phone`), địa chỉ nhận hàng (`shipping_address`), tên mặt hàng nhạy cảm (`items`) hoặc ghi chú nội bộ (`internal_note`).

Nếu trace nằm ngoài khu vực scanner tự động quét, đội ngũ an ninh bảo mật có thể chứng minh tính an toàn bằng cách kiểm tra:
1. Allowlist filtering: Chỉ các trường được định nghĩa rõ ràng trong `ORDER_FIELDS` và `FACT_KEYS` mới được truyền qua các hàm bọc dữ liệu.
2. Kiểm tra tĩnh (Static analysis/Regex scanner) trên toàn bộ output và biến môi trường nhằm đảm bảo chuỗi ký tự `CANARY_SECRET_*` không xuất hiện ở bất kỳ đâu.

## Giới hạn

MockLLM không phải model sản xuất. Latency để `unavailable`. Không sửa JSON cho đủ 0.75.
