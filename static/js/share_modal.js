// Teacher Share Modal & Link Copy Engine

let activeShareTest = null;

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
        statusPill.innerText = "🟢 Active & Live";
      } else {
        statusPill.className = "badge badge-danger";
        statusPill.innerText = "🔴 Disabled / Draft";
      }
    }

    modal.classList.add("active");
  } catch (err) {
    alert("Could not load share link.");
  }
}

function closeShareModal() {
  const modal = document.getElementById("share-modal");
  if (modal) modal.classList.remove("active");
}

function copyStudentLink() {
  const input = document.getElementById("share-student-link");
  if (!input) return;
  input.select();
  navigator.clipboard.writeText(input.value);

  const copiedMsg = document.getElementById("share-copied-msg");
  if (copiedMsg) {
    copiedMsg.style.display = "block";
    setTimeout(() => { copiedMsg.style.display = "none"; }, 2500);
  }
}

function copyDirectFromCard(linkUrl) {
  navigator.clipboard.writeText(linkUrl);
  alert("✅ Student test link copied! Ready to paste into WhatsApp.");
}

function shareViaWhatsApp() {
  if (activeShareTest && activeShareTest.whatsappUrl) {
    window.open(activeShareTest.whatsappUrl, "_blank");
  }
}

function openStudentLink() {
  if (activeShareTest && activeShareTest.shareUrl) {
    window.open(activeShareTest.shareUrl, "_blank");
  }
}
