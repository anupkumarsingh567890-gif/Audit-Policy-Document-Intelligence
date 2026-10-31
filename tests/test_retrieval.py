from src.chatbot.assistant import MODE_RAG, MODE_RETRIEVAL, APDISAssistant
from src.retrieval.retriever import Retriever
from src.vector_store.chroma_db import ChromaVectorStore


class FakeLLM:
    last_model_used = "fake-model"

    def __init__(self):
        self.calls = []

    def generate(self, system_prompt, user_prompt):
        self.calls.append((system_prompt, user_prompt))
        return "Internal auditors evaluate controls [1]."


def make_assistant(hash_embedder, llm=None, name="t"):
    store = ChromaVectorStore(persist_dir=None, collection_name=f"test_{name}")
    store.reset()
    return APDISAssistant(embedder=hash_embedder, vector_store=store, llm=llm, top_k=3)


def test_ingest_and_retrieve_correct_page(hash_embedder, sample_pdf):
    a = make_assistant(hash_embedder, name="retrieve")
    report = a.ingest_file(sample_pdf, save_intermediate=False)
    assert report.num_pages == 4 and report.num_chunks == 3 and report.empty_pages == [3]

    results = a.retriever.retrieve("responsibilities of internal auditors", top_k=1)
    assert results[0].source == "policy.pdf" and results[0].page == 2
    assert -1.0 <= results[0].score <= 1.0

    results = a.retriever.retrieve("who approves the risk appetite", top_k=1)
    assert results[0].page == 4


def test_reingest_does_not_duplicate(hash_embedder, sample_pdf):
    a = make_assistant(hash_embedder, name="dupe")
    a.ingest_file(sample_pdf, save_intermediate=False)
    a.ingest_file(sample_pdf, save_intermediate=False)
    assert a.documents() == {"policy.pdf": 3}
    a.remove_document("policy.pdf")
    assert a.documents() == {}


def test_references_are_unique(hash_embedder, sample_pdf):
    a = make_assistant(hash_embedder, name="refs")
    a.ingest_file(sample_pdf, save_intermediate=False)
    refs = Retriever.references(a.retriever.retrieve("internal audit", top_k=3))
    assert len(refs) == len({(r.source, r.page) for r in refs})


def test_retrieval_mode_does_not_call_llm(hash_embedder, sample_pdf):
    llm = FakeLLM()
    a = make_assistant(hash_embedder, llm=llm, name="mode1")
    a.ingest_file(sample_pdf, save_intermediate=False)
    ans = a.ask("internal auditor responsibilities", mode=MODE_RETRIEVAL)
    assert llm.calls == []
    assert "policy.pdf — Page 2" in ans.answer


def test_rag_mode_sends_context_to_llm(hash_embedder, sample_pdf):
    llm = FakeLLM()
    a = make_assistant(hash_embedder, llm=llm, name="mode2")
    a.ingest_file(sample_pdf, save_intermediate=False)
    ans = a.ask("internal auditor responsibilities", mode=MODE_RAG)
    system_prompt, user_prompt = llm.calls[0]
    assert "ONLY" in system_prompt
    assert "[1] Source: policy.pdf | Page 2" in user_prompt
    assert ans.answer.endswith("[1].") and ans.model == "fake-model"


def test_empty_store_returns_message(hash_embedder):
    a = make_assistant(hash_embedder, llm=FakeLLM(), name="empty")
    ans = a.ask("anything")
    assert ans.results == [] and "Upload PDFs" in ans.answer
