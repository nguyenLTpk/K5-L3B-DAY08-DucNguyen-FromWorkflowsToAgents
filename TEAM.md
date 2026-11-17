# Team

## Thông tin nhóm

- Tên nhóm: LeThanhNguyen_Team
- Lớp: L3A
- Repo nhóm: `K5-L3A-DAY08-LeThanhNguyen-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/nguyenLTpk/K5-L3B-DAY08-DucNguyen-FromWorkflowsToAgents.git, main

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Lê Thành Nguyên | 2A202603733 | nguyenngungonvc@gmail.com | nguyenLTpk | Thành viên A: Shape Workflow, Shape Single, Idempotency & Durability |
|   2 | Thành viên B | 2A202600000 | member.b@example.com | memberB | Thành viên B: Shape Orchestrator, Handoff Security, Benchmark & Evaluation |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.
- Nhóm 2 người: Thành viên A (Workflow + Single + Durability), Thành viên B (Orchestrator + Benchmark + Evaluation).

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Lê Thành Nguyên | Workflow & Single Agent | 03b06f9 | tests/test_member_a_durability_and_shapes.py |
| Thành viên B | Orchestrator & Evaluation | PENDING | tests/test_member_b.py |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/2A202603733_LeThanhNguyen.md`.

Sao chép mục dưới đây cho từng thành viên.

## 2A202603733_LeThanhNguyen

### Phần việc phụ trách

- Cài đặt Shape A (workflow tuần tự) và Shape B (single ReAct agent).
- Đảm bảo cơ chế tính bồi hoàn ở code, gửi quote đầy đủ cho host `durability.issue_refund`.
- Idempotency và an toàn crash (chuyển tiếp `crash_at`, không nuốt `InjectedCrash`).
- Viết bộ test `tests/test_member_a_durability_and_shapes.py`.

### Đóng góp cụ thể

- `src/lab8/shapes/workflow.py`: Hoàn thiện toàn bộ logic tuần tự (pass 62/62 student tests).
- `src/lab8/shapes/single.py`: Hoàn thiện ReAct agent với bounded loop 8 bước (pass 62/62 student tests).
- `src/tests/test_member_a_durability_and_shapes.py`: 4 test cases kiểm tra idempotency, crash resilience, policy denial audit, order cap.

### Bằng chứng

- Pytest suite cho `workflow` đạt 62/62 pass.
- Pytest suite cho `single` đạt 62/62 pass.
- 4 test mới trong `test_member_a_durability_and_shapes.py` pass.
- Host pytest: 58 passed.
