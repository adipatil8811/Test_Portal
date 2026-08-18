import io
import unittest
from app import create_app
from models import db
from models.test import Test
from models.question import Question
from models.response import Response
from models.certificate import Certificate
from services.evaluation_service import evaluate_test_submission
from services.certificate_service import generate_certificate_pdf
from services.link_service import get_test_share_url, get_certificate_verify_url

class TestPlatformTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_database_and_demo_seed(self):
        """Verify database tables and seeded demo test"""
        test = Test.query.filter_by(test_id="t_demo_science").first()
        self.assertIsNotNone(test)
        self.assertEqual(len(test.questions), 4)
        self.assertTrue(test.published)

    def test_evaluation_service_scoring(self):
        """Verify server-side answer evaluation and negative marking"""
        test = Test.query.filter_by(test_id="t_demo_science").first()
        
        # Test all correct answers
        answers_all_correct = {
            "q_101": "Ampere",
            "q_102": "True",
            "q_103": ["Helium", "Neon", "Argon"],
            "q_104": "H2O"
        }
        res = evaluate_test_submission(test, answers_all_correct)
        self.assertEqual(res["score"], 5)
        self.assertEqual(res["percentage"], "100.0")
        self.assertTrue(res["passed"])
        self.assertEqual(res["correctCount"], 4)
        self.assertEqual(res["incorrectCount"], 0)

        # Test partial incorrect (incorrect answers get 0 marks)
        answers_partial = {
            "q_101": "Ampere",   # +1 (correct)
            "q_102": "False",    # 0 (wrong)
            "q_103": ["Helium"], # 0 (incomplete combo)
            "q_104": "H2O"       # +1 (correct)
        }
        res2 = evaluate_test_submission(test, answers_partial)
        # Expected score: 1 + 0 + 0 + 1 = 2
        self.assertEqual(res2["score"], 2)
        self.assertEqual(res2["correctCount"], 2)
        self.assertEqual(res2["incorrectCount"], 2)

    def test_reportlab_pdf_generation(self):
        """Verify ReportLab generates non-empty A4 landscape PDF"""
        sample_data = {
            "studentName": "Alex Sharma",
            "testTitle": "General Science & Physics",
            "score": 5,
            "totalMarks": 5,
            "percentage": "100.0",
            "certificateId": "CERT-2026-TEST99",
            "date": "18 August 2026",
            "instituteName": "GVT",
            "certificateTemplate": "classic",
        }
        pdf_bytes = generate_certificate_pdf(sample_data, verify_url="http://localhost:5000/verify/CERT-2026-TEST99")
        self.assertIsInstance(pdf_bytes, bytes)
        self.assertTrue(len(pdf_bytes) > 1000)
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))

    def test_public_url_generation(self):
        """Verify public share URLs and verification URLs"""
        share_url = get_test_share_url("t_demo_science")
        self.assertTrue(share_url.endswith("/test/t_demo_science"))
        
        verify_url = get_certificate_verify_url("CERT-2026-TEST99")
        self.assertTrue(verify_url.endswith("/verify/CERT-2026-TEST99"))

    def test_routes_status_codes(self):
        """Verify web routes return 200 OK"""
        # Login page
        res = self.client.get("/login")
        self.assertEqual(res.status_code, 200)

        # Student test taking page
        res = self.client.get("/test/t_demo_science")
        self.assertEqual(res.status_code, 200)

        # Student certificate lookup
        res = self.client.get("/student/certificates")
        self.assertEqual(res.status_code, 200)

        # Public verification page
        res = self.client.get("/verify/NON_EXISTENT_ID")
        self.assertEqual(res.status_code, 200)

if __name__ == "__main__":
    unittest.main()
