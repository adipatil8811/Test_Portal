// Resilient Student Test Timer & Auto-Save Engine

let timeRemaining = null;
let timerInterval = null;
let testDurationSeconds = 0;
let currentTestId = "";

function initStudentTest(testId, durationMinutes) {
  currentTestId = testId;
  testDurationSeconds = durationMinutes * 60;

  // Restore saved answers from sessionStorage if available
  restoreSavedAnswers();

  // Attach input auto-save listener
  const form = document.getElementById("student-test-form");
  if (form) {
    form.addEventListener("input", saveAnswersToSession);
    form.addEventListener("change", saveAnswersToSession);
  }

  // If timer is enabled (duration > 0)
  if (durationMinutes > 0) {
    const storageKey = `test_timer_${testId}`;
    const storedRemaining = sessionStorage.getItem(storageKey);

    if (storedRemaining !== null && !isNaN(parseInt(storedRemaining))) {
      timeRemaining = Math.max(0, parseInt(storedRemaining));
    } else {
      timeRemaining = testDurationSeconds;
      sessionStorage.setItem(storageKey, timeRemaining);
    }

    updateTimerDisplay();
    timerInterval = setInterval(() => {
      timeRemaining--;
      sessionStorage.setItem(storageKey, timeRemaining);
      updateTimerDisplay();

      if (timeRemaining <= 0) {
        clearInterval(timerInterval);
        autoSubmitTest();
      }
    }, 1000);
  }
}

function updateTimerDisplay() {
  const displayEl = document.getElementById("timer-display");
  if (!displayEl || timeRemaining === null) return;

  const mins = Math.floor(timeRemaining / 60);
  const secs = timeRemaining % 60;
  const formatted = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  displayEl.innerText = formatted;

  // Visual low-time warnings
  if (timeRemaining <= 60) {
    displayEl.classList.add("timer-critical");
  } else {
    displayEl.classList.remove("timer-critical");
  }
}

function saveAnswersToSession() {
  if (!currentTestId) return;
  const form = document.getElementById("student-test-form");
  if (!form) return;

  const formData = new FormData(form);
  const answers = {};
  for (const [key, value] of formData.entries()) {
    if (key.startsWith("answer_")) {
      if (!answers[key]) {
        answers[key] = value;
      } else {
        if (!Array.isArray(answers[key])) answers[key] = [answers[key]];
        answers[key].push(value);
      }
    }
  }
  sessionStorage.setItem(`test_answers_${currentTestId}`, JSON.stringify(answers));
}

function restoreSavedAnswers() {
  if (!currentTestId) return;
  try {
    const raw = sessionStorage.getItem(`test_answers_${currentTestId}`);
    if (!raw) return;
    const answers = JSON.parse(raw);

    for (const [key, val] of Object.entries(answers)) {
      const inputs = document.getElementsByName(key);
      if (Array.isArray(val)) {
        inputs.forEach(input => {
          if (val.includes(input.value)) input.checked = true;
        });
      } else {
        inputs.forEach(input => {
          if (input.type === "radio") {
            if (input.value === val) input.checked = true;
          } else if (input.type === "text" || input.tagName === "TEXTAREA") {
            input.value = val;
          }
        });
      }
    }
  } catch (e) {}
}

function confirmSubmission() {
  const form = document.getElementById("student-test-form");
  if (!form) return;

  // Count unanswered
  const questionBlocks = document.querySelectorAll(".question-block");
  let unanswered = 0;

  questionBlocks.forEach(block => {
    const inputs = block.querySelectorAll("input, textarea");
    let answered = false;
    inputs.forEach(inp => {
      if ((inp.type === "radio" || inp.type === "checkbox") && inp.checked) answered = true;
      if ((inp.type === "text" || inp.tagName === "TEXTAREA") && inp.value.trim()) answered = true;
    });
    if (!answered) unanswered++;
  });

  let message = "Are you ready to submit your assessment?";
  if (unanswered > 0) {
    message = `⚠️ You have ${unanswered} unanswered question${unanswered > 1 ? 's' : ''}.\n\nAre you sure you want to submit now?`;
  }

  if (confirm(message)) {
    // Clear timer from session storage
    sessionStorage.removeItem(`test_timer_${currentTestId}`);
    sessionStorage.removeItem(`test_answers_${currentTestId}`);
    form.submit();
  }
}

function autoSubmitTest() {
  alert("⏰ Time is up! Your assessment is being submitted automatically.");
  sessionStorage.removeItem(`test_timer_${currentTestId}`);
  sessionStorage.removeItem(`test_answers_${currentTestId}`);
  const form = document.getElementById("student-test-form");
  if (form) form.submit();
}
