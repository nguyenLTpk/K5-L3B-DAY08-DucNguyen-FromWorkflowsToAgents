# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R1 |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Google Research 2026, Towards a Science of Scaling Agent Systems, https://arxiv.org/abs/2602.00000, benchmark |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Multi-agent scaling chỉ cải thiện hiệu năng khi task có thể chia nhỏ song song độc lập; với task có tính phụ thuộc tuần tự, multi-agent làm tăng chi phí và trễ mà không tăng độ chính xác. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Giới hạn trên các task agentic phân rã được, đánh giá trên benchmark giả lập tuần tự/song song với MockLLM và tập luật cố định. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Nếu chuyển từ Workflow (Shape A) sang Orchestrator có thêm Investigator (Shape C), pass rate không đổi (vẫn 1.0) nhưng cost/success sẽ tăng từ ~27.86 VND lên ~46.43 VND (+66.7%) do chi phí overhead phân phối tool. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Cố định: MockLLM, cùng 14 claims public, cùng 5 seeds (11,22,33,44,55), pricing.yaml, evaluator (lab8.metrics). Biến thay đổi duy nhất: Topology thực thi (A: workflow tuần tự trực tiếp vs C: orchestrator uỷ quyền cho investigator qua handoff). |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Đo lường bằng pass rate, pass^5, seed variance và cost_per_success_vnd thông qua lab8.benchmark. |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes workflow,orchestrator --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`
- Run id / file report: `reports/benchmark.json` (trials R-workflow-*-s* và R-orchestrator-*-s*)
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: Đúng. Cả hai kiến trúc đều đạt pass rate = 1.000 và pass^5 = 1.000 (variance = 0.0), tuy nhiên chi phí cost/success của Orchestrator là 46.43 VND, cao hơn 66.7% so với Workflow (27.86 VND) do số lượng tool calls trung bình tăng từ 2.79 lên 4.64.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
