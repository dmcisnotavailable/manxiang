from manxiang.retrieval import KeywordRetriever
from manxiang.schema import SourceChunk


def chunk(chunk_id: str, text: str) -> SourceChunk:
    return SourceChunk(
        id=chunk_id,
        artifact_id="artifact_1",
        text=text,
        start_offset=0,
        end_offset=len(text),
        anchor=f"text:{chunk_id}",
        embedding_status="not_embedded",
        created_at="2026-08-06T10:00:00+08:00",
    )


def test_chunk_helper_creates_source_chunk():
    source_chunk = chunk("chunk_1", "一段测试文本")

    assert isinstance(source_chunk, SourceChunk)
    assert source_chunk.id == "chunk_1"
    assert source_chunk.artifact_id == "artifact_1"
    assert source_chunk.end_offset == len("一段测试文本")
    assert source_chunk.anchor == "text:chunk_1"


def test_keyword_retriever_returns_ranked_chunks():
    retriever = KeywordRetriever()
    chunks = [
        chunk("chunk_1", "普拉多博物馆收藏了大量西班牙王室相关画作。"),
        chunk("chunk_2", "伊莎贝拉一世资助哥伦布远航，开启大航海叙事。"),
        chunk("chunk_3", "这是一段和主题无关的文字。"),
    ]

    results = retriever.retrieve("伊莎贝拉 哥伦布 王室", chunks, limit=2)

    assert [result.chunk.id for result in results] == ["chunk_2", "chunk_1"]
    assert results[0].score > results[1].score


def test_keyword_retriever_coverage_dominates_density():
    retriever = KeywordRetriever()
    chunks = [
        chunk("short_partial", "王室"),
        chunk("long_full", "王室收藏的画作记录了很多宫廷故事，也呈现了历史里的权力结构。"),
    ]

    results = retriever.retrieve("王 室 画作", chunks, limit=2)

    assert [result.chunk.id for result in results] == ["long_full", "short_partial"]


def test_keyword_retriever_strictly_prioritizes_coverage_over_extreme_density():
    retriever = KeywordRetriever()
    terms = ["a" * length for length in range(1, 121)]
    chunks = [
        chunk("short_partial", "a" * 119),
        chunk("long_full", "a" * 120 + " padding" * 200),
    ]

    results = retriever.retrieve(" ".join(terms), chunks, limit=2)

    assert [result.chunk.id for result in results] == ["long_full", "short_partial"]
    assert results[0].coverage == 1.0
    assert results[0].density < results[1].density
    assert results[1].coverage == 119 / 120


def test_keyword_retriever_splits_common_punctuation():
    retriever = KeywordRetriever()
    chunks = [chunk("chunk_1", "伊莎贝拉一世资助哥伦布远航，也关联西班牙王室叙事。")]

    results = retriever.retrieve("伊莎贝拉.哥伦布、王室", chunks, limit=3)

    assert [result.chunk.id for result in results] == ["chunk_1"]
    assert results[0].matched_terms == ("伊莎贝拉", "哥伦布", "王室")


def test_keyword_retriever_filters_zero_score_chunks():
    retriever = KeywordRetriever()
    chunks = [chunk("chunk_1", "完全无关的内容")]

    assert retriever.retrieve("伊莎贝拉 哥伦布", chunks, limit=3) == []


def test_keyword_retriever_returns_empty_for_empty_query():
    retriever = KeywordRetriever()
    chunks = [chunk("chunk_1", "伊莎贝拉一世资助哥伦布远航。")]

    assert retriever.retrieve(" ，。、 ", chunks, limit=3) == []


def test_keyword_retriever_returns_empty_for_non_positive_limit():
    retriever = KeywordRetriever()
    chunks = [
        chunk("chunk_1", "王室收藏"),
        chunk("chunk_2", "王室画作"),
    ]

    assert retriever.retrieve("王室", chunks, limit=0) == []
    assert retriever.retrieve("王室", chunks, limit=-1) == []


def test_keyword_retriever_deduplicates_and_lowercases_query_terms():
    retriever = KeywordRetriever()
    chunks = [chunk("chunk_1", "Python 与 RAG 可以组合成检索系统。")]

    results = retriever.retrieve("PYTHON python RAG rag", chunks, limit=3)

    assert [result.chunk.id for result in results] == ["chunk_1"]
    assert results[0].matched_terms == ("python", "rag")


def test_keyword_retriever_preserves_input_order_for_score_ties():
    retriever = KeywordRetriever()
    chunks = [
        chunk("chunk_1", "王室"),
        chunk("chunk_2", "王室"),
    ]

    results = retriever.retrieve("王室", chunks, limit=2)

    assert [result.chunk.id for result in results] == ["chunk_1", "chunk_2"]
