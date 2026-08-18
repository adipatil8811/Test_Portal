import unittest
import json
from app import create_app
from models import db
from models.test import Test
from models.response import Response
from models.certificate import Certificate

class E2EWorkflowTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        with self.app.app_context():
            db.create_all()

    def tearDown(self):
        self.app_context.pop()

    def test_complete_teacher_and_student_lifecycle(self):
        """End-to-end lifecycle test for teacher and student flows"""
        
        # 1. Teacher Login
        login_res = self.client.post("/login", data={"password": "12345"}, follow_redirects=True)
        self.assertEqual(login_res.status_code, 200)
        self.assertIn(b"Teacher Dashboard", login_res.data)

        # 2. Teacher Creates a New Test
        test_payload = {
            "testId": "t_unit_math_101",
            "title": "Mathematics Mastery Quiz",
            "description": "Calculus and Algebra basics",
            "subject": "Mathematics",
            "class": "Grade 11",
            "division": "A",
            "duration": 20,
            "settings": {
                "startDate": "",
                "endDate": "",
                "enableCertificate": True,
                "certificateMinPercentage": 50,
                "instituteName": "Greenwood International School",
                "certificateTemplate": "academic",
                "certificateTitle": "Certificate of Mathematical Excellence",
            },
            "questions": [
                {
                    "id": "q_math_1",
                    "type": "multiple-choice",
                    "question": "What is the derivative of x^2?",
                    "options": ["x", "2x", "x^3", "2"],
                    "correctAnswer": "2x",
                    "marks": 2,
                    "required": True,
                    "explanation": "By the power rule, d/dx(x^n) = n*x^(n-1). Thus d/dx(x^2) = 2x."
                },
                {
                    "id": "q_math_2",
                    "type": "multiple-correct",
                    "question": "Which of the following are prime numbers?",
                    "options": ["2", "4", "5", "9"],
                    "correctAnswers": ["2", "5"],
                    "marks": 3,
                    "required": True,
                    "explanation": "2 and 5 have only two distinct positive divisors: 1 and themselves."
                }
            ]
        }

        save_res = self.client.post("/admin/api/tests/save", json=test_payload)
        self.assertEqual(save_res.status_code, 200)
        self.assertTrue(save_res.get_json()["success"])

        # 3. Publish Test
        pub_res = self.client.post("/admin/tests/t_unit_math_101/publish", json={"published": True})
        self.assertEqual(pub_res.status_code, 200)
        self.assertTrue(pub_res.get_json()["published"])

        # 4. Student Takes and Submits Test
        student_form = {
            "studentName": "Rohan Gupta",
            "studentEmail": "rohan@example.com",
            "studentClass": "Grade 11",
            "studentDivision": "A",
            "rollNumber": "15",
            "answer_q_math_1": "2x",                # Correct (+2 marks)
            "answer_q_math_2": ["2", "5"],          # Correct (+3 marks)
        }
        submit_res = self.client.post("/test/t_unit_math_101/submit", data=student_form, follow_redirects=True)
        self.assertEqual(submit_res.status_code, 200)
        self.assertIn(b"PASSED ASSESSMENT", submit_res.data)
        self.assertIn(b"100.0% Score", submit_res.data)

        # 5. Check Certificate was Generated in DB
        cert = Certificate.query.filter_by(student_name="Rohan Gupta").first()
        self.assertIsNotNone(cert)
        self.assertEqual(cert.score, 5)
        self.assertEqual(cert.total_marks, 5)
        self.assertEqual(cert.percentage, "100.0")
        self.assertFalse(cert.is_revoked)

        # 6. Student Downloads PDF
        pdf_res = self.client.get(f"/certificate/{cert.certificate_id}/download")
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res.content_type, "application/pdf")
        self.assertTrue(len(pdf_res.data) > 1000)

        # 7. Public Authenticity Verification
        verify_res = self.client.get(f"/verify/{cert.certificate_id}")
        self.assertEqual(verify_res.status_code, 200)
        self.assertIn(b"OFFICIAL CERTIFICATE VERIFIED", verify_res.data)
        self.assertIn(b"Rohan Gupta", verify_res.data)

        # 8. Teacher Views Submissions
        resp_table_res = self.client.get("/admin/tests/t_unit_math_101/responses")
        self.assertEqual(resp_table_res.status_code, 200)
        self.assertIn(b"Rohan Gupta", resp_table_res.data)

        # 9. Teacher Revokes Certificate
        revoke_res = self.client.post(
            f"/admin/certificates/{cert.certificate_id}/revoke",
            data={"reason": "Academic Dishonesty Check"},
            follow_redirects=True
        )
        self.assertEqual(revoke_res.status_code, 200)

        # Verification page now shows Revoked
        verify_revoked_res = self.client.get(f"/verify/{cert.certificate_id}")
        self.assertIn(b"CERTIFICATE REVOKED", verify_revoked_res.data)
        self.assertIn(b"Academic Dishonesty Check", verify_revoked_res.data)

        # 10. Teacher Reinstates Certificate
        reinstate_res = self.client.post(
            f"/admin/certificates/{cert.certificate_id}/reinstate",
            follow_redirects=True
        )
        self.assertEqual(reinstate_res.status_code, 200)

        verify_active_res = self.client.get(f"/verify/{cert.certificate_id}")
        self.assertIn(b"OFFICIAL CERTIFICATE VERIFIED", verify_active_res.data)

        # 11. Duplicate & Delete Test
        dup_res = self.client.post("/admin/tests/t_unit_math_101/duplicate", follow_redirects=True)
        self.assertEqual(dup_res.status_code, 200)
        self.assertIn(b"Mathematics Mastery Quiz (Copy)", dup_res.data)

        del_res = self.client.post("/admin/tests/t_unit_math_101/delete", follow_redirects=True)
        self.assertEqual(del_res.status_code, 200)
        self.assertIsNone(Test.query.filter_by(test_id="t_unit_math_101").first())

if __name__ == "__main__":
    unittest.main()
