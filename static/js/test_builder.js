// Test Builder Interactive Engine
let questions = [];

function initTestBuilder(initialQuestions) {
  questions = initialQuestions || [];
  if (questions.length === 0) {
    addQuestion();
  } else {
    renderQuestions();
  }
  updateTotalMarks();
}

function renderQuestions() {
  const container = document.getElementById("questions-container");
  if (!container) return;
  container.innerHTML = "";

  questions.forEach((q, index) => {
    const card = document.createElement("div");
    card.className = "question-card";
    card.id = `q-card-${index}`;

    let optionsHtml = "";
    if (q.type === "multiple-choice" || q.type === "multiple-correct") {
      const isMulti = q.type === "multiple-correct";
      optionsHtml = `
        <div class="options-container" style="margin-top: 0.75rem;">
          <div style="font-size: 0.75rem; font-weight: 700; color: #64748b; margin-bottom: 0.4rem; text-transform: uppercase;">
            ${isMulti ? "Check all correct options" : "Select the single correct option"}
          </div>
          ${(q.options || ["", "", "", ""]).map((opt, optIdx) => `
            <div class="option-row">
              <input type="${isMulti ? 'checkbox' : 'radio'}"
                name="correct_${q.id}"
                value="${optIdx}"
                ${isMulti ? (Array.isArray(q.correctAnswers) && q.correctAnswers.includes(opt) && opt ? 'checked' : '') : (q.correctAnswer === opt && opt ? 'checked' : '')}
                onchange="updateCorrectAnswer(${index}, ${optIdx}, this.checked, '${q.type}')"
                title="Mark this option as correct"
                style="cursor: pointer; width: 1.1rem; height: 1.1rem;"
              />
              <input type="text"
                class="form-control"
                placeholder="Option ${optIdx + 1}"
                value="${escapeHtml(opt)}"
                oninput="updateOptionText(${index}, ${optIdx}, this.value)"
                style="font-size: 0.85rem; padding: 0.45rem 0.65rem;"
              />
              ${q.options && q.options.length > 2 ? `
                <button type="button" class="btn btn-secondary btn-sm" onclick="removeOption(${index}, ${optIdx})" title="Delete option" style="color: #ef4444; padding: 0.35rem 0.55rem;">✕</button>
              ` : ''}
            </div>
          `).join("")}
          <button type="button" class="btn btn-secondary btn-sm" onclick="addOption(${index})" style="margin-top: 0.3rem;">
            + Add Option
          </button>
        </div>
      `;
    } else if (q.type === "true-false") {
      optionsHtml = `
        <div style="margin-top: 0.75rem; display: flex; gap: 1rem; align-items: center;">
          <span style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Correct Answer:</span>
          <label class="choice-label">
            <input type="radio" name="correct_${q.id}" value="True" ${q.correctAnswer === 'True' ? 'checked' : ''} onchange="updateTFAnswer(${index}, 'True')"> True
          </label>
          <label class="choice-label">
            <input type="radio" name="correct_${q.id}" value="False" ${q.correctAnswer === 'False' ? 'checked' : ''} onchange="updateTFAnswer(${index}, 'False')"> False
          </label>
        </div>
      `;
    }

    card.innerHTML = `
      <div class="question-card-header">
        <div style="display: flex; align-items: center; gap: 0.6rem;">
          <span class="badge badge-primary">Q${index + 1}</span>
          <select class="form-control form-select" onchange="changeQuestionType(${index}, this.value)" style="width: auto; padding: 0.25rem 1.8rem 0.25rem 0.55rem; font-size: 0.75rem; font-weight: 700;">
            <option value="multiple-choice" ${q.type === 'multiple-choice' ? 'selected' : ''}>Single Choice MCQ</option>
            <option value="multiple-correct" ${q.type === 'multiple-correct' ? 'selected' : ''}>Multiple Correct Checkboxes</option>
            <option value="true-false" ${q.type === 'true-false' ? 'selected' : ''}>True / False</option>
            <option value="short-answer" ${q.type === 'short-answer' ? 'selected' : ''}>Short Answer</option>
            <option value="paragraph" ${q.type === 'paragraph' ? 'selected' : ''}>Paragraph</option>
          </select>
        </div>
        
        <div style="display: flex; align-items: center; gap: 0.35rem;">
          <div style="display: flex; align-items: center; gap: 0.3rem; margin-right: 0.5rem;">
            <span style="font-size: 0.75rem; font-weight: 700; color: #64748b;">Marks:</span>
            <input type="number" min="1" max="100" class="form-control" value="${q.marks || 1}" oninput="updateMarks(${index}, this.value)" style="width: 55px; padding: 0.2rem 0.4rem; font-size: 0.75rem; text-align: center;" />
          </div>
          <button type="button" class="btn btn-secondary btn-sm" onclick="moveQuestion(${index}, -1)" ${index === 0 ? 'disabled' : ''} title="Move Up">↑</button>
          <button type="button" class="btn btn-secondary btn-sm" onclick="moveQuestion(${index}, 1)" ${index === questions.length - 1 ? 'disabled' : ''} title="Move Down">↓</button>
          <button type="button" class="btn btn-secondary btn-sm" onclick="duplicateQuestion(${index})" title="Duplicate Question">❐</button>
          <button type="button" class="btn btn-danger btn-sm" onclick="deleteQuestion(${index})" title="Delete Question">🗑</button>
        </div>
      </div>

      <div class="form-group" style="margin-bottom: 0.6rem;">
        <input type="text" class="form-control" placeholder="Enter question text here..." value="${escapeHtml(q.question)}" oninput="updateQuestionText(${index}, this.value)" style="font-weight: 600;" required />
      </div>

      ${optionsHtml}

      <div style="margin-top: 0.75rem; padding-top: 0.6rem; border-top: 1px dashed #e2e8f0;">
        <input type="text" class="form-control" placeholder="Optional: Solution hint or explanation shown after submission..." value="${escapeHtml(q.explanation || '')}" oninput="updateExplanation(${index}, this.value)" style="font-size: 0.75rem; color: #64748b;" />
      </div>
    `;

    container.appendChild(card);
  });

  updateTotalMarks();
}

function addQuestion() {
  const newId = "q_" + Date.now() + "_" + Math.random().toString(36).slice(2, 6);
  questions.push({
    id: newId,
    type: "multiple-choice",
    question: "",
    options: ["", "", "", ""],
    correctAnswer: "",
    correctAnswers: [],
    marks: 1,
    required: true,
    explanation: ""
  });
  renderQuestions();
  const lastCard = document.getElementById(`q-card-${questions.length - 1}`);
  if (lastCard) lastCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function changeQuestionType(index, newType) {
  questions[index].type = newType;
  if (newType === "multiple-choice" || newType === "multiple-correct") {
    if (!questions[index].options || questions[index].options.length === 0) {
      questions[index].options = ["", "", "", ""];
    }
  } else if (newType === "true-false") {
    questions[index].options = ["True", "False"];
    if (!questions[index].correctAnswer) questions[index].correctAnswer = "True";
  }
  renderQuestions();
}

function updateQuestionText(index, val) { questions[index].question = val; }
function updateExplanation(index, val) { questions[index].explanation = val; }
function updateMarks(index, val) {
  questions[index].marks = parseInt(val) || 1;
  updateTotalMarks();
}

function updateOptionText(qIdx, optIdx, val) {
  const oldVal = questions[qIdx].options[optIdx];
  questions[qIdx].options[optIdx] = val;
  if (questions[qIdx].correctAnswer === oldVal) {
    questions[qIdx].correctAnswer = val;
  }
  if (Array.isArray(questions[qIdx].correctAnswers)) {
    const pos = questions[qIdx].correctAnswers.indexOf(oldVal);
    if (pos >= 0) questions[qIdx].correctAnswers[pos] = val;
  }
}

function addOption(qIdx) {
  if (!questions[qIdx].options) questions[qIdx].options = [];
  questions[qIdx].options.push("");
  renderQuestions();
}

function removeOption(qIdx, optIdx) {
  const removed = questions[qIdx].options.splice(optIdx, 1)[0];
  if (questions[qIdx].correctAnswer === removed) questions[qIdx].correctAnswer = "";
  if (Array.isArray(questions[qIdx].correctAnswers)) {
    questions[qIdx].correctAnswers = questions[qIdx].correctAnswers.filter(x => x !== removed);
  }
  renderQuestions();
}

function updateCorrectAnswer(qIdx, optIdx, checked, type) {
  const val = questions[qIdx].options[optIdx] || "";
  if (type === "multiple-choice") {
    questions[qIdx].correctAnswer = val;
  } else if (type === "multiple-correct") {
    if (!Array.isArray(questions[qIdx].correctAnswers)) questions[qIdx].correctAnswers = [];
    if (checked) {
      if (!questions[qIdx].correctAnswers.includes(val)) questions[qIdx].correctAnswers.push(val);
    } else {
      questions[qIdx].correctAnswers = questions[qIdx].correctAnswers.filter(x => x !== val);
    }
  }
}

function updateTFAnswer(qIdx, val) {
  questions[qIdx].correctAnswer = val;
}

function moveQuestion(index, direction) {
  const target = index + direction;
  if (target < 0 || target >= questions.length) return;
  const temp = questions[index];
  questions[index] = questions[target];
  questions[target] = temp;
  renderQuestions();
}

function duplicateQuestion(index) {
  const original = questions[index];
  const copy = JSON.parse(JSON.stringify(original));
  copy.id = "q_" + Date.now() + "_" + Math.random().toString(36).slice(2, 6);
  questions.splice(index + 1, 0, copy);
  renderQuestions();
}

function deleteQuestion(index) {
  if (questions.length === 1) {
    alert("A test must have at least one question.");
    return;
  }
  if (confirm("Are you sure you want to delete this question?")) {
    questions.splice(index, 1);
    renderQuestions();
  }
}

function updateTotalMarks() {
  const total = questions.reduce((sum, q) => sum + (parseInt(q.marks) || 1), 0);
  const badge = document.getElementById("total-marks-badge");
  if (badge) badge.innerText = `${total} Marks (${questions.length} Qs)`;
}

function collectFormData() {
  const title = (document.getElementById("test-title")?.value || "").trim();
  const description = (document.getElementById("test-description")?.value || "").trim();
  const subject = (document.getElementById("test-subject")?.value || "").trim();
  const className = (document.getElementById("test-class")?.value || "").trim();
  const division = (document.getElementById("test-division")?.value || "").trim();
  const duration = parseInt(document.getElementById("test-duration")?.value) || 0;
  const testId = document.getElementById("test-id")?.value;

  const startDate = document.getElementById("test-start-date")?.value || "";
  const endDate = document.getElementById("test-end-date")?.value || "";

  const enableCert = document.getElementById("test-enable-cert")?.checked ?? true;
  const certMinPct = parseInt(document.getElementById("test-cert-min-pct")?.value) || 40;
  const instituteName = document.getElementById("test-institute-name")?.value || "";
  const certTemplate = document.getElementById("test-cert-template")?.value || "classic";
  const certTitle = document.getElementById("test-cert-title")?.value || "Certificate of Achievement";

  return {
    testId,
    title,
    description,
    subject,
    class: className,
    division,
    duration,
    questions,
    settings: {
      startDate,
      endDate,
      enableCertificate: enableCert,
      certificateMinPercentage: certMinPct,
      instituteName,
      certificateTemplate: certTemplate,
      certificateTitle: certTitle,
    }
  };
}

async function saveDraftTest() {
  const data = collectFormData();
  const statusEl = document.getElementById("save-status");
  if (statusEl) statusEl.innerText = "Saving draft...";

  try {
    const res = await fetch("/admin/api/tests/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    const result = await res.json();
    if (result.success) {
      if (statusEl) statusEl.innerText = "✓ Draft saved";
      setTimeout(() => { if (statusEl) statusEl.innerText = ""; }, 2500);
    } else {
      if (statusEl) statusEl.innerText = "Error: " + (result.error || "Save failed");
    }
  } catch (err) {
    if (statusEl) statusEl.innerText = "Error saving draft.";
  }
}

async function publishTestWithValidation(testId) {
  const data = collectFormData();
  if (!data.title) {
    alert("Please provide a Test Title before publishing.");
    document.getElementById("test-title")?.focus();
    return;
  }
  if (!questions || questions.length === 0) {
    alert("Please add at least one question before publishing.");
    return;
  }

  for (let i = 0; i < questions.length; i++) {
    const q = questions[i];
    if (!q.question.trim()) {
      alert(`Question ${i + 1} is missing text. Please enter the question.`);
      return;
    }
    if (q.type === "multiple-choice" || q.type === "true-false") {
      if (!q.correctAnswer.trim()) {
        alert(`Question ${i + 1} does not have a correct answer selected. Please choose the correct option.`);
        return;
      }
    } else if (q.type === "multiple-correct") {
      if (!q.correctAnswers || q.correctAnswers.length === 0) {
        alert(`Question ${i + 1} must have at least one correct checkbox selected.`);
        return;
      }
    }
  }

  // First save test
  await fetch("/admin/api/tests/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data)
  });

  // Then publish
  const res = await fetch(`/admin/tests/${testId}/publish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ published: true })
  });
  const result = await res.json();
  if (result.success) {
    window.location.href = `/admin?published=${testId}`;
  } else {
    alert("Cannot publish: " + (result.error || "Failed to publish."));
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}
