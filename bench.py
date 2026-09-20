from __future__ import annotations

import os
import re
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - fallback for a minimal environment
    def load_dotenv(dotenv_path: Path, override: bool = False) -> None:
        if not dotenv_path.exists():
            return
        for line in dotenv_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if override or not os.getenv(key):
                os.environ[key] = value

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.chunking import FixedSizeChunker
from src.agent import KnowledgeBaseAgent
from src.embeddings import GeminiEmbedder, LocalEmbedder, OpenAIEmbedder, _mock_embed
from src.models import Document
from src.store import EmbeddingStore


CORPUS_DIR = Path(__file__).resolve().parent / "data" / "doi-tra-bao-hanh"


def _parse_scalar(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value.split(" #", 1)[0].strip()


def read_markdown(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text

    lines = text.splitlines()
    end = next((index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---"), None)
    if end is None:
        return {}, text

    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            metadata[match.group(1)] = _parse_scalar(match.group(2))
    content = "\n".join(lines[end + 1:]).strip()
    return metadata, content


def load_chunk_documents(corpus_dir: Path, chunk_size: int = 500) -> list[Document]:
    chunker = FixedSizeChunker(chunk_size=chunk_size)
    documents: list[Document] = []
    for path in sorted(corpus_dir.glob("*.md")):
        frontmatter, content = read_markdown(path)
        for index, chunk in enumerate(chunker.chunk(content)):
            metadata = {
                **frontmatter,
                "doc_id": path.stem,
                "source": str(path),
                "chunk_index": str(index),
            }
            documents.append(Document(id=f"{path.stem}#{index}", content=chunk, metadata=metadata))
    return documents


def _get_embedder():
    has_gemini_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    provider = (os.getenv("EMBEDDING_PROVIDER") or ("gemini" if has_gemini_key else "mock")).strip().lower()
    if provider == "gemini":
        try:
            return GeminiEmbedder()
        except Exception as exc:  # pragma: no cover - diagnostic helper
            print(f"Gemini unavailable: {exc}")
            print("Set GEMINI_API_KEY and EMBEDDING_PROVIDER=gemini before running this benchmark.")
            return _mock_embed
    if provider == "local":
        try:
            return LocalEmbedder()
        except Exception as exc:  # pragma: no cover - optional dependency
            print(f"Local embedding unavailable: {exc}")
    if provider == "openai":
        try:
            return OpenAIEmbedder()
        except Exception as exc:  # pragma: no cover - optional dependency
            print(f"OpenAI embedding unavailable: {exc}")
    return _mock_embed


def _extractive_answer(prompt: str) -> str:
    """Return retrieved context when no generative LLM is configured."""
    context = prompt.split("\n\nQuestion:", 1)[0].removeprefix("Context:\n")
    return " ".join(context.split())[:500]


def _get_llm():
    has_gemini_key = bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"))
    provider = (os.getenv("EMBEDDING_PROVIDER") or ("gemini" if has_gemini_key else "mock")).strip().lower()
    if provider != "gemini":
        return _extractive_answer

    try:
        from google import genai

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY (or GOOGLE_API_KEY) is missing")

        client = genai.Client(api_key=api_key)
        model = os.getenv("GEMINI_LLM_MODEL", "gemini-2.0-flash")

        def gemini_llm(prompt: str) -> str:
            response = client.models.generate_content(model=model, contents=prompt)
            return response.text.strip()

        return gemini_llm
    except Exception as exc:  # pragma: no cover - optional API dependency
        print(f"Gemini generation unavailable: {exc}")
        print("Using extractive answers instead.")
        return _extractive_answer


QUESTIONS = [
    (
        "Khi chọn đơn vị vận chuyển đến lấy hàng hoàn trả, đơn vị vận chuyển hỗ trợ tối đa bao nhiêu lần và trong khoảng thời gian nào?",
        "Tối đa 3 lần lấy hàng, trong vòng 1–3 ngày kể từ ngày lấy hàng đã chọn.",
    ),
    (
        "Khi nào người mua được hoàn lại phí vận chuyển ban đầu của đơn hàng?",
        "Khi yêu cầu Trả hàng/Hoàn tiền cho tất cả sản phẩm trong đơn và được Shopee/Người bán đồng ý hoàn đầy đủ giá trị đã thanh toán. Nếu chỉ yêu cầu cho một số sản phẩm thì không được hoàn phí vận chuyển ban đầu.",
    ),
    (
        "Sau khi yêu cầu trả hàng được chấp nhận, người mua chọn đơn vị vận chuyển đến lấy hàng thì cần thực hiện những bước nào?",
        "Chọn thời gian và địa chỉ lấy hàng → đóng gói hàng → dán phiếu gửi hàng hoặc viết mã vận đơn Shopee cung cấp lên hộp → bàn giao cho đơn vị vận chuyển tại địa chỉ và thời gian đã chọn.",
    ),
    (
        "Có những hình thức gửi hàng hoàn trả nào?",
        "Đơn vị vận chuyển đến lấy hàng; trả hàng tại bưu cục; tự sắp xếp.",
    ),
    (
        "Với hình thức ‘Tự sắp xếp’ để trả hàng, tôi có phải thanh toán trước phí vận chuyển không?",
        "Với đối tượng người mua: Có, người mua cần thanh toán trước phí vận chuyển trả hàng.",
    ),
]


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for env_path in (PROJECT_ROOT / ".env", Path(__file__).with_name(".env")):
        load_dotenv(env_path, override=False)
    embedder = _get_embedder()
    documents = load_chunk_documents(CORPUS_DIR)
    store = EmbeddingStore(collection_name="returns_benchmark", embedding_fn=embedder)

    # search_with_filter operates on the in-memory records. Keep this benchmark
    # deterministic even when ChromaDB happens to be installed locally.
    store._use_chroma = False
    store._collection = None
    print(f"Indexing {len(documents)} chunks...")
    batch_size = 10
    for start in range(0, len(documents), batch_size):
        batch = documents[start : start + batch_size]
        store.add_documents(batch)
        indexed = min(start + batch_size, len(documents))
        print(f"  indexed {indexed}/{len(documents)} chunks", flush=True)
    llm_fn = _get_llm()
    agent = KnowledgeBaseAgent(store=store, llm_fn=llm_fn)

    print(f"Using embedding backend: {getattr(embedder, '_backend_name', embedder.__class__.__name__)}")
    print(f"Loaded {len(documents)} chunks from {CORPUS_DIR}")
    llm_name = getattr(llm_fn, "__name__", llm_fn.__class__.__name__)
    print(f"Agent backend: {llm_name}")
    print("\nTop-3 retrieval results (metadata filter: audience=buyer)\n")

    for index, (question, gold_answer) in enumerate(QUESTIONS, start=1):
        results = store.search_with_filter(
            question,
            top_k=3,
            metadata_filter={"audience": "buyer"},
        )
        print(f"\n{index}. Query: {question}")
        print(f"   Gold: {gold_answer}")
        agent_answer = agent.answer(
            question,
            top_k=3,
            metadata_filter={"audience": "buyer"},
        )
        print(f"   Agent answer: {agent_answer}")
        for rank, result in enumerate(results, start=1):
            preview = " ".join(result["content"].split())[:240]
            print(
                f"   Top-{rank}: score={result['score']:.6f} "
                f"doc_id={result['metadata'].get('doc_id')} "
                f"chunk_id={result['id']}"
            )
            print(f"           {preview}...")


if __name__ == "__main__":
    main()
