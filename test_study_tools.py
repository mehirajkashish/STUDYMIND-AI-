import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.db_models import User, Document
from app.services.study_service import study_service

def test_study_service():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "alex@university.edu").first()
        doc = db.query(Document).filter(Document.user_id == user.id).first()
        
        print("Testing Study Service with doc:", doc.filename)
        
        # 1. Summary
        res_sum = study_service.generate_summary(db, user.id, doc.id)
        assert res_sum["summary"], "Summary is empty!"
        print("✓ Summary generated successfully")
        
        # 2. Flashcards
        res_fc = study_service.generate_flashcards(db, user.id, doc.id, count=4)
        assert len(res_fc.flashcards) > 0, "No flashcards generated!"
        print(f"✓ Flashcards generated: {len(res_fc.flashcards)} cards")
        
        # 3. Quiz
        res_quiz = study_service.generate_quiz(db, user.id, doc.id, count=4)
        assert len(res_quiz.quiz) > 0, "No quiz generated!"
        options_set = set(q.correct_option_id for q in res_quiz.quiz)
        print(f"✓ Quiz generated: {len(res_quiz.quiz)} MCQs (Options verified: {options_set})")
        
        # 4. Explain Simply
        res_exp = study_service.explain_simply(db, user.id, "Attention Mechanism", doc.id)
        assert res_exp["explanation"], "Explanation empty!"
        print("✓ Explain Simply generated successfully")
        
        print("\nALL STUDY TOOLKIT BACKEND TESTS PASSED!")
    finally:
        db.close()

if __name__ == "__main__":
    test_study_service()
