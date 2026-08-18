def evaluate_test_submission(test, student_answers):
    """
    Server-side authoritative evaluation of student test answers.
    Calculates marks, pass/fail status, and generates
    detailed question review breakdown.
    
    :param test: Test model instance
    :param student_answers: Dict mapping question_id -> string or list of strings
    :return: Dict containing score, percentage, counts, and question review list
    """
    total_marks = sum(q.marks for q in test.questions) or 1
    score = 0.0
    correct_count = 0
    incorrect_count = 0
    unanswered_count = 0
    question_reviews = []

    for i, q in enumerate(test.questions):
        student_ans = student_answers.get(q.question_id)
        q_marks = q.marks or 1
        is_correct = False
        marks_obtained = 0.0
        is_answered = False

        if isinstance(student_ans, list):
            is_answered = len(student_ans) > 0 and any(str(x).strip() for x in student_ans)
        elif isinstance(student_ans, str):
            is_answered = bool(student_ans.strip())

        if q.question_type in ("multiple-choice", "true-false"):
            if is_answered:
                if str(student_ans).strip() == str(q.correct_answer).strip():
                    marks_obtained = float(q_marks)
                    score += marks_obtained
                    correct_count += 1
                    is_correct = True
                else:
                    incorrect_count += 1
                    marks_obtained = 0.0
            else:
                unanswered_count += 1

        elif q.question_type == "multiple-correct":
            if is_answered:
                ans_list = student_ans if isinstance(student_ans, list) else [student_ans]
                given_sorted = sorted(str(x).strip() for x in ans_list if str(x).strip())
                correct_sorted = sorted(str(x).strip() for x in (q.correct_answers or []) if str(x).strip())

                if correct_sorted and given_sorted == correct_sorted:
                    marks_obtained = float(q_marks)
                    score += marks_obtained
                    correct_count += 1
                    is_correct = True
                else:
                    incorrect_count += 1
                    marks_obtained = 0.0
            else:
                unanswered_count += 1

        else:
            # Written / open response question
            if is_answered:
                marks_obtained = float(q_marks)
                score += marks_obtained
                correct_count += 1
                is_correct = True
            else:
                unanswered_count += 1

        question_reviews.append({
            "questionId": q.question_id,
            "questionNumber": i + 1,
            "question": q.question_text,
            "type": q.question_type,
            "studentAnswer": student_ans if student_ans is not None else "",
            "correctAnswer": q.correct_answers if q.question_type == "multiple-correct" else q.correct_answer,
            "isCorrect": is_correct,
            "marks": q_marks,
            "marksObtained": round(marks_obtained, 2),
            "explanation": q.explanation or "",
        })

    score = round(score, 2)
    # Format whole floats nicely (e.g. 8.0 -> 8)
    display_score = int(score) if score.is_integer() else score

    percentage = round((score / total_marks) * 100, 1) if total_marks > 0 else 0.0
    min_pass = test.certificate_min_percentage if test.certificate_min_percentage is not None else 40
    passed = percentage >= min_pass

    return {
        "score": display_score,
        "totalMarks": total_marks,
        "percentage": f"{percentage:.1f}",
        "passed": passed,
        "totalQuestions": len(test.questions),
        "correctCount": correct_count,
        "incorrectCount": incorrect_count,
        "unansweredCount": unanswered_count,
        "questionReviews": question_reviews,
    }
