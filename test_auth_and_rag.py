import sys
import json
from pathlib import Path
from fpdf import FPDF

backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from app.core.database import SessionLocal, init_db
from app.models.db_models import User, Document, ChatConversation, ChatMessage
from app.api.auth import register, login, get_current_user_profile
from app.api.documents import upload_documents, get_user_documents, delete_document
from app.api.chat import chat_with_rag, get_user_conversations, get_conversation_messages
from app.api.dashboard import get_dashboard_stats
from app.models.schemas import (
    UserRegisterRequest, UserLoginRequest, ChatRequest
)
from app.services.document_service import document_service

def create_test_pdf(filename="deep_learning_handbook.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Chapter 1: Neural Networks and Backpropagation")
    pdf.ln(10)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 7, "Neural networks learn representations through backpropagation, computing the gradient of the loss with respect to weights using the chain rule.")

    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Chapter 2: Scaled Dot-Product Attention")
    pdf.ln(10)
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(0, 7, "Scaled dot-product attention is computed as Attention(Q, K, V) = softmax(Q * K^T / sqrt(d_k)) * V, allowing direct modeling of relationships regardless of distance.")

    path = backend_dir / filename
    pdf.output(str(path))
    return path

def run_tests():
    print("==================================================", flush=True)
    print("StudyMind AI – Comprehensive Full-Stack Test Suite", flush=True)
    print("==================================================", flush=True)

    init_db()
    db = SessionLocal()

    # Clean old test data
    db.query(ChatMessage).delete()
    db.query(ChatConversation).delete()
    db.query(Document).delete()
    db.query(User).delete()
    db.commit()

    # 1. Test Registration
    reg_req = UserRegisterRequest(
        full_name="Alex Academic",
        email="alex@university.edu",
        password="securePassword123",
        confirm_password="securePassword123"
    )
    auth_res = register(reg_req, db)
    user_1 = db.query(User).filter(User.id == auth_res.user.id).first()
    print(f"[1/10] User Registered: {user_1.full_name} ({user_1.email})", flush=True)
    assert auth_res.access_token is not None

    # 2. Test Duplicate Email Prevention
    try:
        register(reg_req, db)
        assert False, "Duplicate registration should fail"
    except Exception as e:
        print(f"[2/10] Duplicate registration rejected properly: {e.detail}", flush=True)

    # 3. Test Login
    login_req = UserLoginRequest(email="alex@university.edu", password="securePassword123")
    login_res = login(login_req, db)
    print(f"[3/10] User Logged In successfully. JWT token issued.", flush=True)

    # 4. Test PDF Upload & Ingestion with Database Record
    pdf_path = create_test_pdf()
    with open(pdf_path, "rb") as f:
        doc = document_service.process_and_add_pdf(db, user_1.id, pdf_path.name, f.read())
    print(f"[4/10] PDF Ingested & DB Record Created: {doc.filename} (ID: {doc.id}, Pages: {doc.total_pages}, Chunks: {doc.total_chunks})", flush=True)
    assert doc.total_pages == 2
    assert doc.total_chunks >= 2

    # 5. Test Greeting Handling in Chat
    greet_req = ChatRequest(question="Hello StudyMind!")
    greet_res = chat_with_rag(greet_req, current_user=user_1, db=db)
    print(f"[5/10] Chat Greeting Response:\n      {greet_res.answer[:120]}...", flush=True)
    assert "Hello" in greet_res.answer
    assert greet_res.model_used == "StudyMind Conversational"

    # 6. Test Academic RAG Question with Exact Citations
    chat_req = ChatRequest(question="What is the formula for scaled dot-product attention?")
    chat_res = chat_with_rag(chat_req, current_user=user_1, db=db)
    print(f"[6/10] Grounded RAG Answer Generated:\n      {chat_res.answer[:140]}...", flush=True)
    print(f"      Citations: {len(chat_res.sources)} found. Top source: {chat_res.sources[0].filename} (Page {chat_res.sources[0].page_number})", flush=True)
    assert len(chat_res.sources) > 0
    assert chat_res.sources[0].page_number == 2

    # 7. Test Question with Unavailable Information
    unavail_req = ChatRequest(question="What is the boiling point of liquid nitrogen on Mars?")
    unavail_res = chat_with_rag(unavail_req, current_user=user_1, db=db)
    print(f"[7/10] Unrelated Topic Handled:\n      {unavail_res.answer[:120]}...", flush=True)

    # 8. Test Conversation History in Database
    convs = get_user_conversations(current_user=user_1, db=db)
    print(f"[8/10] Saved Conversations in DB: {len(convs)} conversation(s)", flush=True)
    for c in convs:
        print(f"      - Conversation '{c.title}' (Messages: {c.message_count})", flush=True)
    assert len(convs) > 0

    # 9. Test Dashboard Stats from Database
    stats = get_dashboard_stats(current_user=user_1, db=db)
    print(f"[9/10] Real Dashboard Stats: {stats.total_documents} docs, {stats.total_chunks} chunks, {stats.total_questions} questions", flush=True)
    assert stats.total_documents == 1
    assert stats.total_questions == 3  # greeting + attention + nitrogen

    # 10. Test Multi-User Isolation (User 2 should see 0 docs and 0 conversations)
    reg_user_2 = UserRegisterRequest(
        full_name="Bob Student",
        email="bob@college.edu",
        password="bobPassword123",
        confirm_password="bobPassword123"
    )
    auth_res_2 = register(reg_user_2, db)
    user_2 = db.query(User).filter(User.id == auth_res_2.user.id).first()
    docs_user_2 = get_user_documents(current_user=user_2, db=db)
    convs_user_2 = get_user_conversations(current_user=user_2, db=db)
    print(f"[10/10] Multi-User Isolation Verified: User 2 sees {len(docs_user_2)} docs and {len(convs_user_2)} conversations.", flush=True)
    assert len(docs_user_2) == 0
    assert len(convs_user_2) == 0

    print("==================================================", flush=True)
    print("ALL 10 INTEGRATION TESTS PASSED WITH 100% SUCCESS!", flush=True)
    print("==================================================", flush=True)

if __name__ == "__main__":
    run_tests()
