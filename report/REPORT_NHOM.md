# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** 4AE (Lớp K4-L3B — Truy xuất Chính sách Thương mại Điện tử)  
**Thành viên:**
1. Đậu Quang Ý — 2A202602661 (Report & Demo Lead)
2. Nguyễn Đình Lâm Phúc — 2A202602986 (Data Lead)
3. Hồ Thái Hòa — 2A202602915 (Benchmark Lead)
4. Nguyễn Văn Hồng — 2A202602800 (Strategy Lead)  
**Ngày:** 20/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách Thương mại Điện tử Shopee (Quy chế hoạt động, Đổi trả/Hoàn tiền, Bảo hành)

**Tại sao nhóm chọn chủ đề này?**
> Thương mại điện tử (Shopee) là nền tảng mua sắm trực tuyến phổ biến nhất hiện nay, nơi người mua và người bán thường xuyên phát sinh tranh chấp hoặc thắc mắc về quy định đổi trả, hoàn tiền và bảo hành. Các văn bản chính sách này có độ dài lớn, nhiều điều khoản chi tiết và phân hóa rõ rệt giữa đối tượng người mua (buyer) và người bán (seller), rất phù hợp để đánh giá năng lực của hệ thống RAG và kỹ thuật metadata filtering.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | QUY CHẾ HOẠT ĐỘNG SÀN THƯƠNG MẠI ĐIỆN TỬ SHOPEE.VN | https://help.shopee.vn/portal/4/article/77245 | 2026-09-20 / not-stated | 78,171 | audience: both, category: platform-regulation, lang: vi |
| 2 | [Trả hàng/Hoàn tiền] Những quy định chung về Trả hàng/Hoàn tiền của Shopee | https://help.shopee.vn/portal/4/article/188931 | 2026-09-20 / not-stated | 6,854 | audience: buyer, category: returns-refunds, lang: vi |
| 3 | CHÍNH SÁCH TRẢ HÀNG VÀ HOÀN TIỀN | https://help.shopee.vn/portal/4/article/77251 | 2026-09-20 / not-stated | 19,890 | audience: both, category: returns-refunds, lang: vi |
| 4 | [Trả hàng/ Hoàn tiền] Sản phẩm hạn chế trả hàng là gì? | https://help.shopee.vn/portal/4/article/79465 | 2026-09-20 / not-stated | 1,937 | audience: buyer, category: returns-refunds, lang: vi |
| 5 | Những điều cần biết về Trả hàng do "Đổi ý/không còn nhu cầu" | https://help.shopee.vn/portal/4/article/204305 | 2026-09-20 / not-stated | 7,854 | audience: buyer, category: returns-refunds, lang: vi |
| 6 | [Quy định] Chính sách bảo hành cho sản phẩm mua tại Shopee | https://help.shopee.vn/portal/4/article/79046 | 2026-09-20 / not-stated | 4,910 | audience: buyer, category: warranty-policy, lang: vi |
| 7 | [Trả hàng/ Hoàn tiền] Cách đóng gói đơn hàng hoàn trả | https://help.shopee.vn/portal/4/article/79508 | 2026-09-20 / not-stated | 3,915 | audience: buyer, category: returns-refunds, lang: vi |
| 8 | [Trả hàng/ Hoàn tiền] Quy trình Shopee xử lý yêu cầu Trả hàng/ Hoàn tiền | https://help.shopee.vn/portal/4/article/190242 | 2026-09-20 / not-stated | 8,430 | audience: buyer, category: returns-refunds, lang: vi |
| 9 | [Trả hàng/ Hoàn tiền] Các phương thức gửi hàng hoàn trả và phí hoàn trả | https://help.shopee.vn/portal/4/article/189477 | 2026-09-20 / not-stated | 6,247 | audience: buyer, category: returns-refunds, lang: vi |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `audience` | string | `buyer`, `seller`, `both` | Phân tách đối tượng áp dụng, tránh trả về quy định người bán cho thắc mắc của người mua. |
| `category` | string | `returns-refunds`, `warranty-policy`, `platform-regulation` | Khoanh vùng danh mục chính sách, tăng độ chính xác khi tìm kiếm theo chủ đề. |
| `language` | string | `vi` | Hỗ trợ mở rộng đa ngôn ngữ khi hệ thống có tài liệu tiếng Anh hoặc tiếng Việt. |
| `source_url` | string | `https://help.shopee.vn/...` | Đảm bảo tính minh bạch, hỗ trợ truy vết và trích dẫn nguồn cho người dùng. |
| `retrieved_at` | string | `2026-09-20` | Đánh giá độ mới và độ tin cậy của tài liệu theo thời gian. |
| `document_version` | string | `not-stated` | Theo dõi phiên bản hiệu lực của chính sách trên sàn. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `shopee-77251.md` (Chính sách trả hàng/hoàn tiền) | FixedSizeChunker (`fixed_size`) | 80 | 298.0 | Có thể cắt ngang câu tại ranh giới chunk |
| | SentenceChunker (`by_sentences`) | 48 | 410.6 | Giữ trọn vẹn từng câu, cấu trúc ngữ nghĩa rõ ràng |
| | RecursiveChunker (`recursive`) | 85 | 232.2 | Giữ tốt khối đoạn văn bản theo thứ tự phân tách tự nhiên |
| | HeadingChunker (`heading_section`) | 82 | 256.5 | Giữ trọn từng mục và điều khoản; section dài được chia tiếp bằng RecursiveChunker |
| `shopee-188931.md` (Quy định chung) | FixedSizeChunker (`fixed_size`) | 28 | 293.0 | Đều đặn về kích thước nhưng dễ mất mạch ý cuối đoạn |
| | SentenceChunker (`by_sentences`) | 10 | 678.5 | Các câu ghép trong chính sách dài làm chunk lớn |
| | RecursiveChunker (`recursive`) | 29 | 234.5 | Kích thước vừa phải, bảo toàn phân cấp tiêu đề |
| | HeadingChunker (`heading_section`) | 28 | 235 | Bảo toàn cấu trúc tiêu đề, giúp truy xuất đúng từng quy định cụ thể |
| `shopee-79046.md` (Chính sách bảo hành) | FixedSizeChunker (`fixed_size`) | 20 | 293.0 | Dễ áp dụng nhưng không linh hoạt theo độ dài đoạn văn |
| | SentenceChunker (`by_sentences`) | 6 | 814.8 | Giữ nguyên vẹn điều khoản bảo hành nhưng số chunk ít |
| | RecursiveChunker (`recursive`) | 22 | 221.4 | Chia nhỏ hợp lý, tối ưu cho tìm kiếm vector |
| | HeadingChunker (`heading_section`) | 23 | 220.7 | Giữ nguyên ngữ cảnh của từng điều khoản bảo hành, dễ truy vết theo heading |

### Chiến lược của từng thành viên

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

**Thành viên 1 — Hồ Thái Hòa — 2A202602915 (Benchmark Lead)**
- **Loại chiến lược:** RecursiveChunker (`chunk_size=500` hoặc `400`)
- **Mô tả & lý do chọn cho chủ đề này:** Dùng giải thuật chia để trị với danh sách phân tách ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Chiến lược này tối ưu cho văn bản chính sách vì tôn trọng cấu trúc phân đoạn tự nhiên của Shopee, chia nhỏ linh hoạt mà không cắt đôi câu giữa chừng.

**Thành viên 2 — Nguyễn Văn Hồng — 2A202602800 (Strategy Lead)** 
- **Loại chiến lược:** FixedSizeChunker (`chunk_size=500`, `overlap=50`)
- **Mô tả & lý do chọn:** Cắt văn bản thành các khối có kích thước cố định kèm độ chồng chéo (overlap) để giữ ngữ cảnh giữa các ranh giới cắt. Dễ triển khai, kiểm soát đồng đều độ dài vector đưa vào embedding store.

**Thành viên 3 — Đậu Quang Ý — 2A202602661 (Report & Demo Lead)** 
- **Loại chiến lược:** SentenceChunker (`max_sentences_per_chunk=3`)
- **Mô tả & lý do chọn:** Nhận diện ranh giới câu bằng biểu thức chính quy và gom thành từng nhóm câu hoàn chỉnh. Đảm bảo tính trọn vẹn về mặt ngữ pháp và diễn đạt ý của từng điều khoản.

**Thành viên 4 — Nguyễn Đình Lâm Phúc — 2A202602986 (Data Lead)**
- **Loại chiến lược:** Heading/Section Chunking (Custom Chunker)
- **Mô tả & lý do chọn:** Phân tách tài liệu dựa trên các tiêu đề mục (`#`, `##`, `1.1`, `1.2`, `Bước 1`...) của chính sách Shopee. Đây là biến thể bắt buộc của K4-L3B giúp mỗi chunk chứa trọn vẹn một quy định hoặc một bước thủ tục.
- **Code snippet:**
```python
class HeadingSectionChunker:
    def chunk(self, text: str) -> list[str]:
        # Tách văn bản theo các tiêu đề Markdown hoặc các bước số thứ tự
        sections = re.split(r'(?m)^(?=#{1,4}\s+|\d+\.\d*\s+)', text)
        return [s.strip() for s in sections if s.strip()]
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Hồ Thái Hòa (2A202602915) | RecursiveChunker | 10 / 10 | Phân đoạn thông minh, tôn trọng cấu trúc tự nhiên của văn bản | Cần tinh chỉnh danh sách ký tự phân tách cho từng định dạng |
| Nguyễn Văn Hồng (2A202602800) | FixedSizeChunker | 8 / 10 | Kích thước chunk đồng đều, dễ kiểm soát độ dài vector | Vẫn có rủi ro cắt ngang câu tại điểm chia dù có overlap |
| Đậu Quang Ý (2A202602661) | SentenceChunker | 9 / 10 | Giữ nguyên vẹn từng câu, bảo toàn trọn vẹn ngữ pháp | Kích thước chunk không đều, câu ghép dài làm chunk lớn |
| Nguyễn Đình Lâm Phúc (2A202602986) | Heading/Section Chunker | 10 / 10 | Bảo toàn ngữ cảnh hoàn hảo theo từng điều khoản chính sách | Một số section quá ngắn hoặc quá dài nếu văn bản không chuẩn |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> **RecursiveChunker** và **Heading/Section Chunking** là hai chiến lược tốt nhất cho chủ đề chính sách TMĐT. Bởi vì văn bản quy chế, đổi trả và bảo hành có cấu trúc phân cấp mục rất rõ ràng (`Điều khoản`, `Mục`, `Bước`), việc cắt theo cấu trúc heading hoặc đệ quy giúp giữ trọn vẹn ngữ cảnh của từng quy định mà không làm đứt đoạn logic giữa các câu.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Khi chọn đơn vị vận chuyển đến lấy hàng hoàn trả, đơn vị vận chuyển hỗ trợ tối đa bao nhiêu lần và trong khoảng thời gian nào? | Tối đa **3 lần lấy hàng**, trong vòng **1–3 ngày kể từ ngày lấy hàng đã chọn**. | `shopee-189477.md`, mục 1.2 |
| 2 | Khi nào người mua được hoàn lại phí vận chuyển ban đầu của đơn hàng? | Khi yêu cầu Trả hàng/Hoàn tiền cho **tất cả sản phẩm trong đơn** và được Shopee/Người bán đồng ý hoàn đầy đủ giá trị đã thanh toán. Nếu chỉ yêu cầu cho một số sản phẩm thì không được hoàn phí vận chuyển ban đầu. | `shopee-189477.md`, mục 2.1 |
| 3 | Sau khi yêu cầu trả hàng được chấp nhận, người mua chọn đơn vị vận chuyển đến lấy hàng thì cần thực hiện những bước nào? | Chọn thời gian và địa chỉ lấy hàng → đóng gói hàng → dán phiếu gửi hàng hoặc viết mã vận đơn Shopee cung cấp lên hộp → bàn giao cho đơn vị vận chuyển tại địa chỉ và thời gian đã chọn. | `shopee-189477.md`, mục 1.1 |
| 4 | Có những hình thức gửi hàng hoàn trả nào? | **Đơn vị vận chuyển đến lấy hàng; trả hàng tại bưu cục; tự sắp xếp.** | `shopee-189477.md`, mục 1.1 |
| 5 | Với hình thức “Tự sắp xếp” để trả hàng, tôi có phải thanh toán trước phí vận chuyển không? *(Lọc: `audience="buyer"`)* | Với đối tượng **người mua**: **Có**, người mua cần thanh toán trước phí vận chuyển trả hàng. | `shopee-189477.md`, mục 2.2; `shopee-77251.md`, mục 8 |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú (Chunk ID & Score) |
|---|---------|-------------------------------|-------------------------------|----------------------------|
| 1 | Số lần và thời gian lấy hàng hoàn trả | RecursiveChunker | Có (Top-1) | `shopee-189477#4` (score: 0.8857) — chứa mốc 1-3 ngày và tối đa 3 lần |
| 2 | Điều kiện hoàn phí vận chuyển ban đầu | RecursiveChunker | Có (Top-1) | `shopee-189477#9` (score: 0.8020) — điều kiện hoàn tiền toàn bộ đơn |
| 3 | Quy trình 4 bước đơn vị vận chuyển lấy hàng | SentenceChunker / Recursive | Có (Top-2) | `shopee-189477#1` (score: 0.8079) — quy trình đủ 4 bước tuần tự |
| 4 | Các hình thức gửi hàng hoàn trả | FixedSizeChunker / Recursive | Có (Top-1) | `shopee-189477#5` (score: 0.8233) — đủ 3 hình thức gửi hàng |
| 5 | Phí vận chuyển tự sắp xếp (người mua) | RecursiveChunker (filter `audience="buyer"`) | Có (Top-1) | `shopee-189477#8` (score: 0.7932) — lọc chính xác nghĩa vụ người mua |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Lọc bằng metadata phát huy hiệu quả đặc biệt rõ rệt ở **Câu hỏi số 5** (`audience="buyer"`). Do các văn bản chính sách TMĐT có nhiều điều khoản quy định về cùng một hành động ("trả hàng", "chịu phí vận chuyển") nhưng nghĩa vụ hoàn toàn trái ngược giữa người mua (phải thanh toán trước) và người bán (được miễn hoặc chịu phạt sau), việc tiền lọc theo `audience` giúp loại bỏ toàn bộ tài liệu quy định phía đối tác bán hàng, ngăn chặn hoàn toàn tình trạng AI lấy nhầm ngữ cảnh.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> 1. **Metadata Pre-filtering là "chìa khóa" cho văn bản chính sách:** Trong TMĐT, nhiều quy định dùng chung từ khóa nhưng phân quyền ngược nhau giữa Người mua và Người bán. Tiền lọc theo metadata giúp loại bỏ 100% tài liệu sai đối tượng.
> 2. **Sức mạnh của Semantic Embedding:** Chuyển từ mock hash sang mô hình nhúng ngữ nghĩa (Gemini / Sentence-Transformers) nâng điểm tương đồng từ mức nhiễu (<0.1) lên >0.8, giúp câu hỏi tìm đúng chính xác mục quy định trong tài liệu.
> 3. **Chiến lược phân chia theo ngữ cảnh (Context-aware Chunking):** Với văn bản chính sách, việc cắt theo tiêu đề hoặc chia đệ quy vượt trội hoàn toàn so với cắt kích thước cố định vì giữ trọn vẹn một điều khoản hoặc một quy trình xử lý.

**Bài học rút ra khi so sánh trong nhóm:**
> Khi so sánh kết quả cùng một bộ dữ liệu giữa 4 thành viên, nhóm nhận thấy cùng một câu hỏi nhưng cách chia chunk khác nhau sẽ dẫn đến việc AI nhận ngữ cảnh khác nhau: nếu chunk quá nhỏ thì thiếu thông tin, nếu chunk quá to thì làm loãng vector khiến điểm tương đồng giảm. Kích thước chunk tối ưu cho chính sách Shopee là khoảng 300–500 ký tự (hoặc theo từng section).

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ thực hiện tiền xử lý (data cleaning) kỹ càng hơn bằng cách loại bỏ các đoạn văn bản boilerplate (như menu, lời chào trợ giúp) ngay từ bước crawl, đồng thời bổ sung thêm các trường metadata chuyên sâu như `sub_category` (ví dụ: `giao-hang`, `doi-tra-quoc-te`) để tăng cường khả năng lọc đa chiều.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
