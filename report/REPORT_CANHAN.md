# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Nguyễn Văn Hồng
**Nhóm:** 4AE
**Ngày:** 20/09/2026


> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản tại `REPORT_NHOM.md`. Thang điểm đối chiếu tại `docs\SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Cosine similarity cao nghĩa là hai vector có hướng gần nhau. Khi sử dụng mô hình embedding ngữ nghĩa phù hợp, điều này thường cho thấy hai đoạn văn bản có nội dung hoặc chủ đề tương đồng, dù có thể dùng từ ngữ khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: Tôi muốn trả lại sản phẩm bị hỏng.
- Câu B: Tôi cần gửi trả món hàng bị lỗi.
- Tại sao tương đồng: Hai câu cùng diễn đạt nhu cầu trả lại sản phẩm có vấn đề, dù sử dụng cách diễn đạt khác nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Tôi muốn trả lại sản phẩm bị hỏng.
- Câu B: Mặt Trăng quay quanh Trái Đất.
- Tại sao khác: Hai câu thuộc các chủ đề khác nhau và không truyền tải thông tin liên quan.

Các ví dụ trên là nhận định theo ý nghĩa, không phải kết quả đo bằng mock embedding.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine tập trung vào hướng của vector và không phụ thuộc độ lớn của chúng, phù hợp khi muốn so sánh nội dung được biểu diễn bởi embedding. Tuy nhiên, khi hai vector đều được chuẩn hóa về độ dài 1, khoảng cách Euclid và cosine có quan hệ trực tiếp là $d^2 = 2 - 2\cos\theta$, nên không thể khẳng định cosine luôn tốt hơn trong mọi trường hợp.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**

Với tài liệu dài hơn một chunk và `0 <= overlap < chunk_size`, áp dụng công thức của bài tập:

```text
step = chunk_size - overlap = 500 - 50 = 450 ký tự
N = ceil((độ_dài_tài_liệu - overlap) / (chunk_size - overlap))
  = ceil((10000 - 50) / (500 - 50))
  = ceil(9950 / 450)
  = 23 chunks
```

**Đáp án: 23 chunks.** Chunk cuối bắt đầu tại vị trí 9.900 (đếm từ 0) và có 100 ký tự.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**

```text
step = 500 - 100 = 400 ký tự
N = ceil((10000 - 100) / (500 - 100))
  = ceil(9900 / 400)
  = 25 chunks
```

Số chunk tăng từ **23 lên 25** vì bước dịch của cửa sổ giảm từ 450 xuống 400 ký tự. Overlap lớn hơn giúp giữ ngữ cảnh ở ranh giới chunk nhưng tăng nội dung trùng lặp, số embedding cần tính và chi phí lưu trữ.

**Kiểm chứng bằng `FixedSizeChunker` hiện tại:** Với đầu vào `"x" * 10000`, overlap 50 trả 23 chunk (chunk cuối 100 ký tự); overlap 100 trả 25 chunk (chunk cuối 400 ký tự).

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Các mô tả dưới đây đối chiếu với mã nguồn hiện đang lưu và được kiểm thử, không chỉ là phương án dự kiến.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex `(?<=[.!?])\s+` để tách ở khoảng trắng ngay sau dấu kết thúc câu và giữ lại dấu câu, sau đó gom các câu theo `max_sentences_per_chunk`. Đầu vào rỗng hoặc chỉ có khoảng trắng trả `[]`, tham số số câu được giới hạn tối thiểu là 1 và khoảng trắng giữa các câu được chuẩn hóa khi nối. Hạn chế là regex có thể tách sai chữ viết tắt như “TS. Nguyễn Văn A” và không phát hiện ranh giới câu nếu sau dấu câu không có khoảng trắng.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Ưu tiên separator theo thứ tự `\n\n`, `\n`, `. `, khoảng trắng rồi chuỗi rỗng; mảnh quá dài được chia đệ quy bằng separator tiếp theo, sau đó gom các mảnh liền kề trong giới hạn `chunk_size`. Thuật toán giữ nguyên separator để không mất ký tự; các trường hợp dừng là văn bản rỗng, văn bản đã đủ ngắn hoặc hết separator/chạm separator rỗng thì cắt theo ký tự. Hàm `chunk` từ chối kích thước không dương bằng `ValueError`; khác với sentence chunker, recursive giới hạn theo ký tự và không thêm overlap.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Store lưu danh sách record trong RAM, mỗi `Document` thành một record gồm ID, nội dung, metadata sao chép sâu và embedding; store không tự chia chunk và không ghi đè khi ID trùng. Embedding được kiểm tra giá trị hữu hạn, số chiều và chuẩn hóa L2; query được embed một lần, tính dot product với các vector đã chuẩn hóa rồi xếp giảm dần để lấy top-k. Query rỗng, top-k không dương hoặc không có ứng viên trả `[]`; kết quả trả metadata được sao chép và điểm số, không trả vector nội bộ.

Store giữ vector 0 ở dạng 0 và cho điểm 0 theo quy ước; dữ liệu không được lưu bền vững sau khi chương trình kết thúc. `get_collection_size` trả số record đang lưu.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Lọc metadata trước khi xếp hạng và lấy top-k để tài liệu ngoài điều kiện không chiếm chỗ; nhiều điều kiện kết hợp bằng AND và so khớp chính xác, nên `audience="buyer"` không tự bao gồm `"both"`. Metadata giữ `doc_id` gốc nếu đã có, nếu chưa thì bổ sung từ `Document.id`, nhờ đó `delete_document` xóa tất cả record/chunk thuộc cùng tài liệu gốc. Hàm trả `True` nếu có record bị xóa và `False` nếu không tìm thấy; filter rỗng tương đương tìm kiếm thông thường.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Agent nhận store và `llm_fn` từ bên ngoài, truy xuất top-k rồi ghép các nội dung được đánh số `[1]`, `[2]` kèm nguồn ưu tiên `source_url`, `source`, cuối cùng là `doc_id`. Prompt gồm câu hỏi, reference context và yêu cầu chỉ dựa trên context, coi tài liệu là dữ liệu chứ không phải chỉ dẫn, trích dẫn nguồn, trả lời cùng ngôn ngữ và nói rõ khi thông tin chưa đủ. Nếu không có kết quả, agent trả thông báo ngay mà không gọi LLM; nếu có, agent gọi `llm_fn` và trả nguyên kết quả.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                          [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                   [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                            [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                             [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                  [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                  [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                        [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                         [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                       [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                         [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                         [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                    [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                          [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                 [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                     [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED               [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                     [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                         [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                           [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                             [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                   [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                        [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                          [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED              [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                           [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                    [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                   [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                              [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                          [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                     [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                         [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                               [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                         [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED      [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                    [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                   [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED       [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                  [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED           [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED     [100%]

================================================ 42 passed in 0.09s =================================================
```

**Số lượng bài test vượt qua (pass): 42 / 42.**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Shopee hiện chưa hỗ trợ yêu cầu đổi hàng. | Hiện tại, người mua chưa thể yêu cầu đổi sản phẩm trên Shopee. | Cao — cùng nói chưa hỗ trợ đổi hàng | 0.961735 | Đúng |
| 2 | Đối với sản phẩm bảo hành điện tử, thời hạn bảo hành được tính từ thời điểm kích hoạt bảo hành điện tử | Với sản phẩm bảo hành điện tử, thời gian bảo hành bắt đầu khi bảo hành điện tử được kích hoạt. | Cao — cùng mốc bắt đầu bảo hành điện tử | 0.974234 | Đúng |
| 3 | Luôn ghi hình lại quá trình đóng gói hàng hoàn, nhằm đảm bảo quyền lợi khi Người bán có phát sinh khiếu nại hàng hoàn trả. | Hãy quay video lúc đóng gói hàng trả lại để bảo vệ quyền lợi nếu người bán khiếu nại về hàng hoàn. | Cao — cùng mục đích quay video đóng gói | 0.937226 | Đúng |
| 4 | Shopee hiện chưa hỗ trợ yêu cầu đổi hàng. | Đối với sản phẩm bảo hành điện tử, thời hạn bảo hành được tính từ thời điểm kích hoạt bảo hành điện tử | Thấp — hỗ trợ đổi hàng khác mốc bảo hành | 0.547479 | Đúng |
| 5 | Sản phẩm hạn chế trả hàng là những sản phẩm có tính đặc thù cao, dễ hư hỏng hoặc cần điều kiện bảo quản nghiêm ngặt. | Luôn ghi hình lại quá trình đóng gói hàng hoàn, nhằm đảm bảo quyền lợi khi Người bán có phát sinh khiếu nại hàng hoàn trả. | Thấp — định nghĩa sản phẩm khác hướng dẫn ghi hình | 0.681478 | Đúng |


**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:* Kết quả bất ngờ nhất là cặp 5. Hai câu không diễn đạt cùng một thông tin cụ thể nhưng vẫn đạt cosine similarity khá cao, 0.681478. Điều này cho thấy embedding không chỉ biểu diễn sự giống nhau ở mức câu chữ hoặc ý nghĩa chính xác, mà còn có thể phản ánh chủ đề và ngữ cảnh chung. Cả hai câu đều thuộc miền trả hàng/hoàn trả trên Shopee nên vector của chúng vẫn tương đối gần nhau. Ngược lại, ba cặp được dự đoán có độ tương tự cao đều đạt trên 0.93, cho thấy Gemini embedding nhận diện tốt các câu diễn đạt cùng ý bằng từ ngữ khác nhau.
---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|---|---|---:|---|---|
| 1 | Khi chọn đơn vị vận chuyển đến lấy hàng hoàn trả, đơn vị vận chuyển hỗ trợ tối đa bao nhiêu lần và trong khoảng thời gian nào? | Chunk `shopee-79508#6`, nói về thời gian chọn hình thức trả hàng, thời hạn giao hàng hoàn trả và mã vận đơn. | 0.788131 | Không trực tiếp chứa đáp án cần tìm | Agent trả lời đúng: tối đa **3 lần** lấy hàng trong vòng **1–3 ngày** kể từ ngày đã chọn. |
| 2 | Khi nào người mua được hoàn lại phí vận chuyển ban đầu của đơn hàng? | Chunk `shopee-189477#8`, chứa điều kiện hoàn phí vận chuyển khi hoàn toàn bộ sản phẩm và trường hợp không được hoàn khi chỉ trả một số sản phẩm. | 0.804875 | Có | Agent trả lời đúng các điều kiện được hoàn phí vận chuyển ban đầu và trường hợp không được hoàn. |
| 3 | Sau khi yêu cầu trả hàng được chấp nhận, người mua chọn đơn vị vận chuyển đến lấy hàng thì cần thực hiện những bước nào? | Chunk `shopee-189477#1`, chứa các bước chọn thời gian/địa chỉ, đóng gói, dán phiếu hoặc ghi mã vận đơn. | 0.816389 | Có | Agent trả lời đúng 4 bước: chọn thời gian và địa chỉ → đóng gói → dán phiếu/ghi mã vận đơn → bàn giao cho đơn vị vận chuyển. |
| 4 | Có những hình thức gửi hàng hoàn trả nào? | Chunk `shopee-189477#0`, nói về các phương thức gửi hàng hoàn trả nhưng context truy xuất không chứa đầy đủ cả 3 hình thức. | 0.806084 | Có liên quan nhưng chưa đủ thông tin | Agent chỉ trả lời được **2 hình thức**: đơn vị vận chuyển đến lấy hàng và trả hàng tại bưu cục; thiếu **Tự sắp xếp**. |
| 5 | Với hình thức “Tự sắp xếp” để trả hàng, tôi có phải thanh toán trước phí vận chuyển không? | Chunk `shopee-189477#9`, chứa trực tiếp nội dung người mua cần thanh toán trước phí trả hàng khi chọn hình thức Tự sắp xếp. | 0.775806 | Có | Agent trả lời đúng: **Có**, người mua cần thanh toán trước phí trả hàng; sau đó Shopee hỗ trợ hoàn phí theo chính sách. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?**  5 / 5 

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Điều hay nhất tôi học được từ thành viên khác là cách đánh giá hệ thống retrieval không chỉ dựa vào việc tài liệu đúng có xuất hiện trong Top-3 hay không, mà còn phải kiểm tra chunk truy xuất được có thực sự chứa thông tin cần để trả lời câu hỏi. Qua demo, tôi nhận ra một kết quả có thể đúng `doc_id` nhưng vẫn sai ở mức nội dung, dẫn đến Agent trả lời thiếu hoặc sai. Điều này giúp tôi hiểu rõ hơn vai trò của chiến lược chunking, metadata filter và cách phân tích failure case trong hệ thống RAG.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |