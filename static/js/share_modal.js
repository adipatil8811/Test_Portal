// Teacher Share Modal & Link Copy Engine — Android-compatible

let activeShareTest = null;

/** Cross-browser clipboard copy with Android fallback */
function copyToClipboard(text) {
  if (navigator.clipboard && window.isSecureContext) {
    return navigator.clipboard.writeText(text).catch(() => execCommandCopy(text));
  }
  return execCommandCopy(text);
}

function execCommandCopy(text) {
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.setAttribute("readonly", "");
  ta.style.cssText = "position:fixed;top:-9999px;left:-9999px;opacity:0;";
  document.body.appendChild(ta);
  ta.focus();
  ta.select();
  try { document.execCommand("copy"); } catch (_) {}
  document.body.removeChild(ta);
  return Promise.resolve();
}

async function openShareModal(testId) {
  const modal = document.getElementById("share-modal");
  if (!modal) return;

  try {
    const res = await fetch(`/admin/api/share-info/${testId}`);
    const data = await res.json();
    activeShareTest = data;

    document.getElementById("share-test-title").innerText = data.title;
    document.getElementById("share-student-link").value = data.shareUrl;

    const statusPill = document.getElementById("share-status-pill");
    if (statusPill) {
      if (data.published) {
        statusPill.className = "badge badge-success";
        statusPill.innerText = "Active & Live";
      } else {
        statusPill.className = "badge badge-danger";
        statusPill.innerText = "Draft / Disabled";
      }
    }

    const copiedMsg = document.getElementById("share-copied-msg");
    if (copiedMsg) copiedMsg.style.display = "none";

    modal.classList.add("active");
  } catch (err) {
    alert("Could not load share link. Please try again.");
  }
}

function closeShareModal() {
  const modal = document.getElementById("share-modal");
  if (modal) modal.classList.remove("active");
}

async function copyStudentLink() {
  const input = document.getElementById("share-student-link");
  if (!input) return;
  await copyToClipboard(input.value);
  const copiedMsg = document.getElementById("share-copied-msg");
  if (copiedMsg) {
    copiedMsg.style.display = "block";
    setTimeout(() => { copiedMsg.style.display = "none"; }, 3000);
  }
}

async function copyDirectFromCard(linkUrl) {
  await copyToClipboard(linkUrl);
  showToast("Student link copied! Ready to paste into WhatsApp.");
}

function shareViaWhatsApp() {
  if (activeShareTest && activeShareTest.whatsappUrl) {
    window.location.href = activeShareTest.whatsappUrl;
  }
}

function openStudentLink() {
  if (activeShareTest && activeShareTest.shareUrl) {
    window.open(activeShareTest.shareUrl, "_blank", "noopener");
  }
}

function showToast(message) {
  let toast = document.getElementById("gvt-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "gvt-toast";
    toast.style.cssText = "position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#0f172a;color:#fff;padding:0.75rem 1.25rem;border-radius:12px;font-size:0.875rem;font-weight:700;z-index:9999;box-shadow:0 4px 20px rgba(0,0,0,.35);max-width:90vw;text-align:center;pointer-events:none;transition:opacity 0.3s ease;";
    document.body.appendChild(toast);
  }
  toast.innerText = message;
  toast.style.opacity = "1";
  clearTimeout(toast._hideTimer);
  toast._hideTimer = setTimeout(() => { toast.style.opacity = "0"; }, 2800);
}
