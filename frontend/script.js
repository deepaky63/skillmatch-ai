/* ═══════════════════════════════════════════════════════
   SkillMatch AI — script.js
   API integration · Results rendering · UI state
═══════════════════════════════════════════════════════ */

const API = "https://skillmatch-ai-mmpn.onrender.com";
const LAST_ANALYSIS_KEY = "skillmatch:last-analysis";

const state = { selectedFile: null };

const elements = {
  uploadZone:     document.getElementById("upload-zone"),
  fileInput:      document.getElementById("resume-file"),
  browseBtn:      document.getElementById("browse-btn"),
  fileName:       document.getElementById("file-name"),
  skillsInput:    document.getElementById("skills-input"),
  analyzeBtn:     document.getElementById("analyze-btn"),
  apiStatus:      document.getElementById("api-status"),
  apiDot:         document.getElementById("api-dot"),
  heroApiStatus:  document.getElementById("hero-api-status"),
  jobsCount:      document.getElementById("jobs-count"),
  analysesCount:  document.getElementById("analyses-count"),
  resultsSummary: document.getElementById("results-summary"),
  skillsResults:  document.getElementById("skills-results"),
  jobResults:     document.getElementById("job-results"),
  gapResults:     document.getElementById("gap-results"),
  careerPath:     document.getElementById("career-path"),
  navbar:         document.getElementById("navbar"),
};

/* ── Navbar scroll ──────────────────────────────────── */
window.addEventListener("scroll", () => {
  elements.navbar?.classList.toggle("scrolled", window.scrollY > 50);
});

/* ── API Status ─────────────────────────────────────── */
function setApiStatus(isOnline) {
  const label = isOnline ? "Online" : "Offline";
  if (elements.apiStatus)     elements.apiStatus.textContent = label;
  if (elements.heroApiStatus) elements.heroApiStatus.textContent = label;
  if (elements.apiDot) {
    elements.apiDot.className = "api-dot " + (isOnline ? "online" : "offline");
  }
}

/* ── Session storage helpers ────────────────────────── */
function saveLastAnalysis(data) {
  try { sessionStorage.setItem(LAST_ANALYSIS_KEY, JSON.stringify(data)); } catch (_) {}
}
function restoreLastAnalysis() {
  try {
    const raw = sessionStorage.getItem(LAST_ANALYSIS_KEY);
    if (!raw) return;
    const data = JSON.parse(raw);
    showResults(data);
    renderGaps(data.gaps || []);
    renderCareerPath(data.career_path || []);
  } catch (_) {
    sessionStorage.removeItem(LAST_ANALYSIS_KEY);
  }
}

/* ── Check API + load stats ─────────────────────────── */
async function checkAPI() {
  try {
    // Increase timeout to 15 seconds to handle Render cold starts
    const res = await fetch(`${API}/api/stats`, { signal: AbortSignal.timeout(15000) });
    if (!res.ok) throw new Error("bad");
    const data = await res.json();
    setApiStatus(true);
    animateCount(elements.jobsCount,      data.total_jobs      || 30);
    animateCount(elements.analysesCount,  data.total_analyses  || 0);
    return true;
  } catch {
    setApiStatus(false);
    return false;
  }
}

/* Animated number counter */
function animateCount(el, target) {
  if (!el) return;
  const from  = parseInt(el.textContent) || 0;
  const dur   = 900;
  const t0    = performance.now();
  const tick  = (now) => {
    const p = Math.min((now - t0) / dur, 1);
    const v = Math.round(from + (target - from) * (1 - Math.pow(1 - p, 3)));
    el.textContent = v;
    if (p < 1) requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
}

/* ── Run Analysis ───────────────────────────────────── */
async function runAnalysis(event) {
  if (event) { event.preventDefault(); event.stopPropagation(); }

  const hasFile    = Boolean(state.selectedFile);
  const typedSkills = elements.skillsInput.value.trim();

  if (!hasFile && !typedSkills) {
    showToast("Upload a resume or enter skills before running analysis.", "error");
    return;
  }

  elements.analyzeBtn.disabled = true;
  elements.analyzeBtn.textContent = "Analyzing…";
  elements.resultsSummary.textContent = "Processing profile";

  try {
    let response;

    if (hasFile) {
      const formData = new FormData();
      formData.append("file", state.selectedFile);
      response = await fetch(`${API}/api/analyze/resume`, { method: "POST", body: formData });
    } else {
      response = await fetch(`${API}/api/analyze/text`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ skills: typedSkills }),
      });
    }

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Analysis failed");

    showResults(data);
    renderGaps(data.gaps || []);
    renderCareerPath(data.career_path || []);
    saveLastAnalysis(data);
    checkAPI();  // refresh stats

    // Scroll to results
    document.getElementById("demo")?.scrollIntoView({ behavior: "smooth", block: "start" });

  } catch (err) {
    elements.resultsSummary.textContent = "Analysis failed";
    elements.skillsResults.innerHTML = '<span class="placeholder-tag">No skills extracted</span>';
    elements.jobResults.innerHTML    = `<div class="empty-state"><span class="empty-icon">⚠️</span>${esc(err.message)}</div>`;
    elements.gapResults.innerHTML    = '<div class="empty-state"><span class="empty-icon">📊</span>Skill gaps and course recommendations will appear after analysis.</div>';
    elements.careerPath.innerHTML    = '<div class="empty-state"><span class="empty-icon">🛤️</span>Career progression recommendations will appear here.</div>';
    showToast(err.message || "Analysis failed. Is the backend running?", "error");
  } finally {
    elements.analyzeBtn.disabled = false;
    elements.analyzeBtn.textContent = "Analyze Profile";
  }
}

/* ── Show Results ───────────────────────────────────── */
function showResults(data) {
  const skills  = data.extracted_skills || [];
  const matches = data.matches || [];

  // Summary pill
  const topMatch = matches[0];
  elements.resultsSummary.textContent = topMatch
    ? `${topMatch.match_percent}% best match`
    : "No matches found";

  // Extracted skills tags
  elements.skillsResults.innerHTML = skills.length
    ? skills.map(s => `<span class="tag">${esc(s)}</span>`).join("")
    : '<span class="placeholder-tag">No skills extracted</span>';

  // Job cards
  elements.jobResults.innerHTML = matches.length
    ? matches.map((m, i) => buildJobCard(m, i)).join("")
    : '<div class="empty-state"><span class="empty-icon">🎯</span>No job matches available for this profile.</div>';
}

function buildJobCard(m, idx) {
  const matchedSet = new Set((m.matched_skills || []).map(s => s.toLowerCase()));
  const allSkills  = m.required_skills || [];

  const skillsHTML = allSkills
    .map(s => `<span class="skill-chip ${matchedSet.has(s.toLowerCase()) ? "matched" : ""}">${esc(s)}</span>`)
    .join("");

  const missingSkills = allSkills.filter(s => !matchedSet.has(s.toLowerCase()));
  const missingHTML   = missingSkills.length
    ? missingSkills.slice(0, 3).map(s => `<span class="missing-chip">Gap: ${esc(s)}</span>`).join("")
    : '<span class="skill-chip">Strong alignment</span>';

  const pct   = m.match_percent || 0;
  const color = pct >= 70 ? "var(--accent)"
              : pct >= 45 ? "var(--amber)"
              : "var(--muted)";

  return `
    <article class="job-card" style="animation-delay:${idx * 0.06}s">
      <div class="job-card-top">
        <div>
          <h4>${esc(m.title)}</h4>
          <div class="job-meta">${esc(m.company)} · ${esc(m.type || "")}</div>
        </div>
        <div class="match-badge" style="color:${color}">${pct}%</div>
      </div>
      <div class="job-meta" style="margin-bottom:10px">💰 ${esc(m.salary || "")}</div>
      <div class="job-skills">${skillsHTML}</div>
      <div class="job-missing" style="margin-top:8px">${missingHTML}</div>
    </article>
  `;
}

/* ── Render Gaps ────────────────────────────────────── */
function renderGaps(gaps) {
  if (!gaps.length) {
    elements.gapResults.innerHTML = '<div class="empty-state"><span class="empty-icon">✅</span>No major gaps detected for the current profile.</div>';
    return;
  }

  elements.gapResults.innerHTML = gaps.map((gap, i) => {
    const course   = gap.course || {};
    const priority = gap.priority || "nice";
    return `
      <article class="gap-item" style="animation-delay:${i * 0.07}s">
        <div class="gap-top">
          <div>
            <h4>${esc(gap.skill)}</h4>
          </div>
          <span class="importance-chip ${esc(priority)}">${esc(priority)}</span>
        </div>
        <div class="course-block">
          <div class="course-label">Recommended Course</div>
          <div class="course-name">${esc(course.name || "Learning resource available")}</div>
          <div class="course-meta">${esc(course.provider || "")} · ${esc(course.duration || "")} · ${esc(course.level || "")}</div>
        </div>
      </article>
    `;
  }).join("");
}

/* ── Render Career Path ─────────────────────────────── */
function renderCareerPath(path) {
  if (!path.length) {
    elements.careerPath.innerHTML = '<div class="empty-state"><span class="empty-icon">🛤️</span>Career path stages will appear after analysis.</div>';
    return;
  }

  const icons = ["🚀", "📈", "🏆"];
  elements.careerPath.innerHTML = path.map((item, i) => {
    const skills = (item.skills_to_gain || [])
      .map(s => `<span>${esc(s)}</span>`).join("");
    return `
      <article class="timeline-item" style="animation-delay:${i * 0.1}s">
        <div class="timeline-top">
          <div>
            <div class="timeline-stage">${icons[i] || "⭐"} ${esc(item.stage)}</div>
            <h4>${esc(item.title)}</h4>
            <div class="muted-text">${esc(item.description || "")}</div>
          </div>
        </div>
        ${skills ? `<div class="timeline-actions" style="margin-top:10px">${skills}</div>` : ""}
      </article>
    `;
  }).join("");
}

/* ── File Handling ──────────────────────────────────── */
function setFile(file) {
  if (!file) return;
  const ext = file.name.split(".").pop().toLowerCase();
  if (!["pdf", "docx", "txt"].includes(ext)) {
    showToast("Unsupported file. Please upload PDF, DOCX, or TXT.", "error");
    return;
  }
  state.selectedFile = file;
  if (elements.fileName) elements.fileName.textContent = `📎 ${file.name}`;
}

function attachUploadHandlers() {
  elements.browseBtn.addEventListener("click", () => elements.fileInput.click());

  elements.fileInput.addEventListener("change", (e) => {
    e.preventDefault();
    const [file] = e.target.files;
    if (file) setFile(file);
  });

  ["dragenter", "dragover"].forEach(ev =>
    elements.uploadZone.addEventListener(ev, (e) => {
      e.preventDefault();
      elements.uploadZone.classList.add("drag-over");
    })
  );

  ["dragleave", "drop"].forEach(ev =>
    elements.uploadZone.addEventListener(ev, (e) => {
      e.preventDefault();
      elements.uploadZone.classList.remove("drag-over");
    })
  );

  elements.uploadZone.addEventListener("drop", (e) => {
    e.preventDefault(); e.stopPropagation();
    const [file] = e.dataTransfer.files;
    if (file) setFile(file);
  });
}

/* ── Toast Notification ─────────────────────────────── */
function showToast(msg, type = "info") {
  let toast = document.getElementById("sm-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "sm-toast";
    Object.assign(toast.style, {
      position: "fixed", bottom: "28px", right: "28px", zIndex: "9999",
      padding: "14px 22px", borderRadius: "14px",
      fontFamily: "'DM Sans', sans-serif", fontSize: "0.88rem", fontWeight: "500",
      maxWidth: "340px", backdropFilter: "blur(16px)",
      border: "1px solid", transition: "all 0.3s ease",
      boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
    });
    document.body.appendChild(toast);
  }
  const styles = {
    error: { bg: "rgba(255,85,85,0.15)", border: "rgba(255,85,85,0.4)", color: "#ff8888" },
    info:  { bg: "rgba(0,194,168,0.12)", border: "rgba(0,194,168,0.35)", color: "#00c2a8" },
  };
  const s = styles[type] || styles.info;
  Object.assign(toast.style, { background: s.bg, borderColor: s.border, color: s.color, opacity: "1", transform: "translateY(0)" });
  toast.textContent = msg;
  clearTimeout(toast._t);
  toast._t = setTimeout(() => Object.assign(toast.style, { opacity: "0", transform: "translateY(10px)" }), 4000);
}

/* ── Escape helper ──────────────────────────────────── */
function esc(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

/* ── Init ───────────────────────────────────────────── */
// function init() {
//   attachUploadHandlers();
//   elements.analyzeBtn.addEventListener("click", runAnalysis);
//   restoreLastAnalysis();
//   checkAPI();
//   setInterval(checkAPI, 30_000);
// }


async function init() {
  attachUploadHandlers();
  elements.analyzeBtn.addEventListener("click", runAnalysis);

  const isOnline = await checkAPI();

  if (isOnline) {
    restoreLastAnalysis();
  }

  setInterval(checkAPI, 30000);
}

document.addEventListener("DOMContentLoaded", init);
