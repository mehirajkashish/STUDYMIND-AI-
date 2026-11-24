import os
import sys
from pathlib import Path
from fpdf import FPDF

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))


def create_sample_academic_pdf(filename="computer_vision_study_guide.pdf"):
    """Creates a sample multi-page academic PDF with real text using fpdf2."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Page 1: Convolutional Neural Networks
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Chapter 1: Convolutional Neural Networks", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", size=11)
    p1_text = (
        "Convolutional Neural Networks (CNNs) are specialized neural network architectures "
        "designed for processing grid-structured data such as digital images. The fundamental "
        "operations in a standard CNN are convolution, activation functions (such as ReLU), and max pooling. "
        "Max pooling reduces the spatial dimensions of feature maps while retaining salient activations, "
        "providing translation invariance and decreasing computational complexity."
    )
    pdf.multi_cell(0, 7, p1_text)

    # Page 2: Self-Attention and Transformers
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Chapter 2: Transformer Architectures and Self-Attention", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", size=11)
    p2_text = (
        "The Transformer model relies entirely on self-attention mechanisms to compute representations "
        "of its input and output without using sequence-aligned recurrent networks. The scaled dot-product "
        "attention is mathematically defined as Attention(Q, K, V) = softmax(Q * K^T / sqrt(d_k)) * V. "
        "Multi-head attention allows the model to jointly attend to information from different representation subspaces, "
        "capturing complex dependencies across input tokens simultaneously."
    )
    pdf.multi_cell(0, 7, p2_text)

    # Page 3: Retrieval-Augmented Generation (RAG)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Chapter 3: Retrieval-Augmented Generation (RAG) and FAISS", ln=True)
    pdf.ln(5)
    pdf.set_font("Helvetica", size=11)
    p3_text = (
        "Retrieval-Augmented Generation (RAG) enhances generative language models by retrieving relevant document "
        "chunks from an external vector index such as FAISS before generating an answer. This minimizes "
        "hallucinations and ensures that responses are grounded directly in uploaded study materials. "
        "A proper RAG system provides strict citations specifying both the document filename and exact page number."
    )
    pdf.multi_cell(0, 7, p3_text)

    test_pdf_path = backend_dir / filename
    pdf.output(str(test_pdf_path))
    return test_pdf_path


def run_rag_test():
    print("==================================================", flush=True)
    print("StudyMind AI - Real RAG Verification Test Suite", flush=True)
    print("==================================================", flush=True)

    # 1. Create Sample PDF
    pdf_path = create_sample_academic_pdf()
    print(f"[1/7] Created test academic PDF: {pdf_path.name} ({pdf_path.stat().st_size} bytes)", flush=True)

    # 2. Test PDF Ingestion & Extraction
    from app.rag.extractor import extract_text_from_pdf
    pages, meta = extract_text_from_pdf(str(pdf_path))
    print(f"[2/7] Page extraction: {len(pages)} pages extracted using {meta['extractor_used']}", flush=True)
    for p in pages:
        print(f"      - Page {p['page_number']}: {p['text'][:65]}...", flush=True)

    assert len(pages) == 3, f"Expected 3 pages, got {len(pages)}"

    # 3. Test Chunking
    from app.rag.chunker import chunk_document_pages
    chunks = chunk_document_pages(pages, "test_doc_1", pdf_path.name, chunk_size=300, chunk_overlap=50)
    print(f"[3/7] Text Chunking: Created {len(chunks)} chunks with preserved metadata", flush=True)
    for c in chunks:
        print(f"      [Chunk #{c.chunk_index} | Page {c.page_number}]: {c.text[:55]}...", flush=True)

    assert len(chunks) >= 3, "Expected at least 3 chunks"

    # 4. Test Embedding Generation
    from app.rag.embeddings import embedding_service
    texts = [c.text for c in chunks]
    vectors = embedding_service.embed_texts(texts)
    print(f"[4/7] Embeddings: Generated {vectors.shape[0]} vectors of dimension {vectors.shape[1]}", flush=True)
    assert vectors.shape[0] == len(chunks), "Vector count must match chunk count"

    # 5. Test Vector Store & Semantic Search
    from app.rag.vector_store import vector_store
    vector_store.add_chunks(chunks, vectors)
    print(f"[5/7] Vector Store: Added chunks. Total indexed in store: {vector_store.total_chunks()}", flush=True)

    # Query 1: Self-Attention
    query_1 = "What is the formula for scaled dot-product attention?"
    q_vec_1 = embedding_service.embed_query(query_1)
    results_1 = vector_store.search(q_vec_1, top_k=2)
    print(f"\n   Semantic Search 1: '{query_1}'", flush=True)
    print(f"   Top Match: Page {results_1[0][0].page_number} (Score: {results_1[0][1]:.4f})", flush=True)
    print(f"   Excerpt: \"{results_1[0][0].text}\"", flush=True)
    assert results_1[0][0].page_number == 2, f"Expected Page 2 for attention query, got {results_1[0][0].page_number}"

    # Query 2: Max Pooling
    query_2 = "What does max pooling do in convolutional networks?"
    q_vec_2 = embedding_service.embed_query(query_2)
    results_2 = vector_store.search(q_vec_2, top_k=2)
    print(f"\n   Semantic Search 2: '{query_2}'", flush=True)
    print(f"   Top Match: Page {results_2[0][0].page_number} (Score: {results_2[0][1]:.4f})", flush=True)
    print(f"   Excerpt: \"{results_2[0][0].text}\"", flush=True)
    assert results_2[0][0].page_number == 1, f"Expected Page 1 for max pooling query, got {results_2[0][0].page_number}"

    # 6. Test Grounded Answer Generation & Citations
    from app.services.gemini_service import gemini_service
    from app.models.schemas import SourceCitation
    citations = [
        SourceCitation(
            document_id=c.document_id,
            filename=c.filename,
            page_number=c.page_number,
            text=c.text,
            relevance_score=round(float(s), 4)
        )
        for c, s in results_1
    ]
    ans = gemini_service.generate_rag_answer(query_1, citations)
    print(f"\n[6/7] Grounded Answer Generated via {ans['model_used']}:", flush=True)
    print(f"      Citations: {len(citations)} source citations provided", flush=True)
    print(f"      Snippet: {ans['answer'][:160]}...", flush=True)

    # 7. Test Study Tools (Flashcards & Quiz)
    from app.services.document_service import document_service
    from app.core.database import SessionLocal
    from app.models.db_models import User
    from app.services.study_service import study_service

    test_db = SessionLocal()
    try:
        test_user = test_db.query(User).first()
        if not test_user:
            test_user = User(full_name="RAG Test User", email="rag.test@studymind.ai", hashed_password="mock")
            test_db.add(test_user)
            test_db.commit()
            test_db.refresh(test_user)

        with open(pdf_path, "rb") as f:
            doc_meta = document_service.process_and_add_pdf(test_db, test_user.id, pdf_path.name, f.read())

        flashcards_res = study_service.generate_flashcards(test_db, test_user.id, doc_meta.id, count=3)
        print(f"\n[7/7] Study Tools: Generated {len(flashcards_res.flashcards)} flashcards", flush=True)
        for fc in flashcards_res.flashcards:
            print(f"      - Page {fc.page_number} ({fc.key_concept}): Q: {fc.question}", flush=True)

        quiz_res = study_service.generate_quiz(test_db, test_user.id, doc_meta.id, count=3)
        print(f"      Generated {len(quiz_res.quiz)} practice MCQs:", flush=True)
        for q in quiz_res.quiz:
            print(f"      - Page {q.page_number}: {q.question} [Correct: {q.correct_option_id}]", flush=True)
    finally:
        test_db.close()

    print("\n==================================================", flush=True)
    print("ALL RAG PIPELINE & ACADEMIC TESTS PASSED VERIFIED!", flush=True)
    print("==================================================", flush=True)


if __name__ == "__main__":
    run_rag_test()
