from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import urllib.request
import urllib.error

# Gemini API configuration
# Set GEMINI_API_KEY in Windows before starting AURA.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"
GEMINI_MODEL = "gemini-3.8-flash"


def gemini_answer(question):
    """Ask Gemini for an AURA school-tutor answer."""
    if not GEMINI_API_KEY:
        return (
            "🔐 Gemini API key अभी configured नहीं है.\n\n"
            "AURA में GEMINI_API_KEY set करके नया CMD खोलकर server restart करो."
        )

    payload = {
        "systemInstruction": {
            "parts": [{
                "text": (
                    "You are AURA AI, a friendly school learning assistant for "
                    "Class 11-12 MP Board students. Answer in simple Hindi with "
                    "useful English terms when appropriate. Explain step-by-step "
                    "for study questions, use formulas and examples when useful, "
                    "and keep the answer exam-friendly. Do not reveal hidden "
                    "chain-of-thought or private reasoning. If unsure, say so "
                    "clearly rather than inventing facts."
                )
            }]
        },
        "contents": [{
            "role": "user",
            "parts": [{"text": question}]
        }],
        "generationConfig": {
            "maxOutputTokens": 2000
        }
    }

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        GEMINI_API_URL,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        }
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
        candidates = result.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            text = "".join(part.get("text", "") for part in parts).strip()
            if text:
                return text
        return "⚠️ Gemini ने कोई text answer नहीं दिया."
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", errors="replace")
        except Exception:
            detail = str(e)
        return "⚠️ Gemini API error (HTTP " + str(e.code) + ").\n" + detail[:700]
    except urllib.error.URLError as e:
        return "🌐 Gemini से connection नहीं हो पाया. Internet connection check करो.\n" + str(e.reason)
    except Exception as e:
        return "⚠️ AURA AI error: " + str(e)


test_question = 0
test_score = 0
test_active = False

class AuraServer(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path != "/":
            self.send_response(404)
            self.end_headers()
            return

        page = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AURA AI</title>
<style>
:root{
  --bg:#f4f7fb; --panel:#ffffff; --panel2:#eef3f9; --text:#152238;
  --muted:#66758a; --line:#dfe6ef; --accent:#315efb; --accent2:#6c63ff;
  --shadow:0 12px 35px rgba(24,40,72,.10);
}
*{box-sizing:border-box}
body{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;background:var(--bg);color:var(--text)}
button,input{font:inherit}
.app{display:flex;height:100vh;overflow:hidden}
.sidebar{width:245px;background:var(--panel);border-right:1px solid var(--line);padding:18px 12px;display:flex;flex-direction:column}
.brand{display:flex;align-items:center;gap:10px;padding:10px 12px 22px}
.brand-icon{font-size:34px}.brand-name{font-size:22px;font-weight:800}.brand-sub{font-size:11px;color:var(--muted);margin-top:2px}
.section{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#8793a5;padding:12px 13px 6px}
.nav{border:0;background:transparent;width:100%;text-align:left;padding:11px 13px;border-radius:11px;color:var(--text);cursor:pointer;margin:2px 0}
.nav:hover,.nav.active{background:#edf2ff;color:var(--accent);font-weight:700}
.nav.subject{padding-left:25px;font-size:14px}
.sidebar-bottom{margin-top:auto;padding:10px 8px;font-size:12px;color:var(--muted)}
.main{flex:1;display:flex;flex-direction:column;min-width:0}
.topbar{height:70px;background:var(--panel);border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 24px}
.top-title{font-weight:750}.top-actions{display:flex;gap:8px}
.icon-btn{border:1px solid var(--line);background:var(--panel);border-radius:10px;padding:9px 12px;cursor:pointer}
.content{flex:1;overflow:auto;padding:0 24px}
.hero{max-width:1180px;width:100%;min-height:calc(100vh - 70px);height:calc(100vh - 70px);margin:0 auto;display:flex;flex-direction:column;justify-content:flex-start;align-items:center;padding:26px 0 18px}
.welcome{font-size:32px;font-weight:800;margin:22px 0 28px;text-align:center;letter-spacing:-.5px;flex:0 0 auto}.description{display:none}
.chat-card{width:100%;max-width:none;flex:1;min-height:0;display:flex;flex-direction:column;background:transparent;border:0;border-radius:0;box-shadow:none;overflow:visible}
.chat-head{display:none}
.chat-card:has(.msg.user) .messages{display:block}
.messages{display:none;flex:1;min-height:0;max-height:none;overflow:auto;padding:10px 12px 22px;margin-bottom:10px;scroll-behavior:smooth}
.msg{display:flex;margin:14px 0}.msg.user{justify-content:flex-end}.bubble{max-width:min(820px,78%);padding:13px 16px;border-radius:16px;line-height:1.6;white-space:pre-wrap}
.msg.aura .bubble{background:var(--panel2)}.msg.user .bubble{background:var(--accent);color:#fff}
.composer{width:100%;padding:18px 20px;background:var(--panel);border:1px solid var(--line);border-radius:24px;box-shadow:0 12px 45px rgba(35,65,120,.08);margin-top:auto;flex:0 0 auto}
.input-row{display:flex;gap:9px;align-items:center}
.question{flex:1;border:0;background:transparent;border-radius:14px;padding:7px 4px;outline:none;font-size:17px}
.question:focus{border-color:#9aaeff;box-shadow:0 0 0 3px #e9edff}
.action{border:0;border-radius:13px;padding:13px 16px;cursor:pointer;background:var(--accent);color:#fff;font-weight:700}
.mic{background:#111c31}.mic.listening{background:#dc3545;animation:pulse 1s infinite}
@keyframes pulse{50%{transform:scale(1.05);box-shadow:0 0 0 8px rgba(220,53,69,.12)}}
/* ===== CHAT HISTORY + AI ANIMATIONS ===== */
.history-wrap{margin-top:10px;padding:0 7px 8px;max-height:245px;overflow:auto}
.history-title{display:flex;align-items:center;justify-content:space-between;padding:8px 6px 5px;font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#8793a5}
.history-clear{border:0;background:transparent;color:#8a95a5;font-size:11px;cursor:pointer}.history-clear:hover{color:#e14b4b}
.history-item{display:flex;align-items:center;gap:5px;margin:3px 0}
.history-open{flex:1;border:0;background:transparent;text-align:left;padding:8px 8px;border-radius:9px;color:var(--text);cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:12px}
.history-open:hover{background:#f0f4fa}.dark .history-open:hover{background:#1d2940}
.history-delete{width:28px;height:28px;border:0;background:transparent;color:#9aa5b5;border-radius:8px;cursor:pointer;opacity:.65}.history-delete:hover{background:#fff0f0;color:#d33;opacity:1}
.typing{display:flex;align-items:center;gap:5px;padding:4px 2px}.typing i{width:7px;height:7px;border-radius:50%;background:#7892d8;display:block;animation:typingDot 1.1s infinite}.typing i:nth-child(2){animation-delay:.15s}.typing i:nth-child(3){animation-delay:.3s}
@keyframes typingDot{0%,60%,100%{transform:translateY(0);opacity:.35}30%{transform:translateY(-5px);opacity:1}}
.msg-in{animation:msgIn .28s ease-out both}.msg.aura .bubble.answer-in{animation:answerIn .4s ease-out both}
@keyframes msgIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes answerIn{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:none}}
.msg-actions{display:flex;gap:5px;margin-top:8px;opacity:.75}.msg-actions button{border:1px solid var(--line);background:var(--panel);border-radius:9px;padding:4px 7px;font-size:11px;cursor:pointer;color:var(--muted)}.msg-actions button:hover{color:var(--accent)}
.stop-generating{display:none;border:1px solid #f0b7b7;background:#fff7f7;color:#c33;border-radius:10px;padding:6px 10px;font-size:12px;cursor:pointer;margin-top:9px}.stop-generating.show{display:inline-block}
.voice-gender{display:inline-flex;gap:7px;align-items:center;margin-top:8px;font-size:12px;color:#d9e4ff}.voice-gender button{border:1px solid rgba(255,255,255,.3);background:rgba(255,255,255,.08);color:#fff;border-radius:10px;padding:6px 9px;cursor:pointer}.voice-gender button.active{background:#fff;color:#203b73}
.sidebar-scroll{overflow:auto;flex:1;min-height:0}
.voice-panel{display:none;margin-top:12px;background:linear-gradient(135deg,#111c31,#273b6b);color:#fff;border-radius:18px;padding:22px;text-align:center}
.voice-panel.show{display:block}.orb{width:80px;height:80px;margin:5px auto 12px;border-radius:50%;display:grid;place-items:center;background:rgba(255,255,255,.13);font-size:35px}
.voice-panel.listening .orb{animation:orb 1s infinite}
@keyframes orb{50%{transform:scale(1.13);box-shadow:0 0 35px rgba(120,160,255,.45)}}
.voice-text{font-size:14px;opacity:.9}.stop{margin-top:12px;border:1px solid rgba(255,255,255,.3);background:transparent;color:#fff;padding:8px 14px;border-radius:10px;cursor:pointer}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:15px;margin-top:22px}
.subject-card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:19px;cursor:pointer;transition:.18s;box-shadow:0 5px 18px rgba(24,40,72,.05)}
.subject-card:hover{transform:translateY(-2px);box-shadow:var(--shadow)}
.subject-icon{font-size:28px}.subject-name{font-weight:800;margin-top:8px}.subject-info{font-size:12px;color:var(--muted);margin-top:4px}
.tools{display:flex;gap:8px;margin-top:12px}.tool{border:1px solid var(--line);background:var(--panel);padding:7px 10px;border-radius:14px;cursor:pointer;font-size:12px}
.dark{--bg:#0d1422;--panel:#141d2d;--panel2:#1c2940;--text:#eef4ff;--muted:#9aa8bd;--line:#2a3850}
.dark .sidebar,.dark .topbar,.dark .composer,.dark .chat-card{background:var(--panel)}
.dark .icon-btn,.dark .tool,.dark .question{background:var(--panel);color:var(--text)}
@media(max-width:850px){ .content{padding:0 12px}.hero{padding:18px 0 12px}.welcome{font-size:25px;margin:12px 0 18px}.bubble{max-width:88%}.composer{border-radius:20px;padding:15px}}
@media(max-width:850px){
 .sidebar{width:72px;padding:10px 7px}.brand-name,.brand-sub,.section,.nav span,.sidebar-bottom{display:none}
 .brand{justify-content:center}.nav{font-size:20px;text-align:center;padding:12px 5px}.nav.subject{padding-left:5px}
 .content{padding:18px 12px}.grid{grid-template-columns:repeat(2,1fr)}.welcome{font-size:25px}
}
@media(max-width:560px){
 .topbar{padding:0 12px}.content{padding:14px 9px}.grid{grid-template-columns:1fr}
 .bubble{max-width:90%}.action{padding:12px}.question{min-width:0}
}

/* ===== AURA LANDING + LOGIN ===== */
.landing{position:fixed;inset:0;z-index:1000;overflow:auto;background:radial-gradient(circle at 50% 20%,#ffffff 0,#eef5ff 48%,#e7f0ff 100%);color:#14274a}
.landing.hidden{display:none}
.land-head{height:82px;display:flex;align-items:center;justify-content:space-between;padding:0 48px}
.land-brand{display:flex;align-items:center;gap:11px}.land-logo{font-size:38px;line-height:1}.land-brand strong{font-size:25px}.land-brand small{display:block;color:#6d82a5;margin-top:2px}
.land-tools{display:flex;gap:10px}.land-pill{border:1px solid #cbd9ee;background:rgba(255,255,255,.65);border-radius:24px;padding:10px 16px;color:#24406e}
.land-center{max-width:900px;margin:55px auto 0;text-align:center;padding:0 20px}.land-badge{display:inline-block;padding:9px 17px;border-radius:22px;background:#e5efff;color:#3164dc;font-size:14px;font-weight:700}
.land-center h1{font-size:54px;margin:20px 0 10px;letter-spacing:-1.5px}.land-sub{font-size:19px;color:#7488aa;line-height:1.55;margin-bottom:30px}
.land-chat{max-width:860px;margin:auto;background:rgba(255,255,255,.78);border:1px solid #d8e3f3;border-radius:24px;padding:22px;box-shadow:0 18px 60px rgba(49,94,180,.12);text-align:left}
.land-chat-title{font-size:20px;font-weight:800;margin-bottom:5px}.land-chat-sub{color:#8295b5;margin-bottom:15px}
.land-input{height:118px;width:100%;resize:none;border:1px solid #d4e0ef;border-radius:17px;padding:18px;font-size:16px;outline:none;background:#fff;color:#203558}.land-input:focus{border-color:#86a8ee;box-shadow:0 0 0 4px #eaf1ff}
.land-chat-bottom{display:flex;justify-content:space-between;align-items:center;margin-top:12px}.land-modes{display:flex;gap:8px}.land-mode{border:1px solid #cbd9ee;background:#f7faff;border-radius:18px;padding:8px 13px;color:#315cae}
.land-send{border:0;background:#3164dc;color:white;width:45px;height:45px;border-radius:50%;font-size:21px;cursor:pointer}
.land-actions{display:flex;justify-content:center;gap:14px;margin-top:25px}.land-btn{border-radius:25px;padding:12px 35px;font-weight:750;cursor:pointer;font-size:15px}.land-login{border:0;background:#3164dc;color:#fff}.land-create{border:1px solid #b9cbe5;background:#fff;color:#264575}
.land-features{max-width:900px;margin:46px auto 30px;display:grid;grid-template-columns:repeat(5,1fr);gap:0}.land-feature{text-align:center;border-right:1px solid #cbd9ee;padding:0 15px}.land-feature:last-child{border:0}.land-feature b{display:block;margin-top:7px}.land-feature small{color:#7a8dab;line-height:1.35}
.auth-back{position:fixed;inset:0;background:rgba(10,27,55,.35);backdrop-filter:blur(7px);z-index:1100;display:none;align-items:center;justify-content:center;padding:20px}.auth-back.show{display:flex}
.auth-box{width:min(410px,100%);background:#fff;border-radius:22px;padding:28px;box-shadow:0 25px 80px rgba(0,0,0,.2)}.auth-box h2{margin:0 0 7px}.auth-box p{color:#74839a;margin-top:0}.auth-input{width:100%;padding:13px 14px;border:1px solid #d5deea;border-radius:11px;margin:7px 0;outline:none}.auth-submit{width:100%;border:0;border-radius:11px;padding:13px;background:#3164dc;color:#fff;font-weight:750;cursor:pointer;margin-top:8px}.auth-close{float:right;border:0;background:#eef3fa;border-radius:50%;width:30px;height:30px;cursor:pointer}
.auth-error{color:#c62828;font-size:13px;min-height:18px}.auth-note{font-size:12px;color:#8795a8;margin-top:12px}
.logged-user{display:flex;align-items:center;gap:8px}.logout-btn{border:1px solid var(--line);background:var(--panel);border-radius:10px;padding:8px 11px;cursor:pointer}
@media(max-width:700px){.land-head{padding:0 18px}.land-center{margin-top:35px}.land-center h1{font-size:38px}.land-sub{font-size:16px}.land-features{grid-template-columns:repeat(2,1fr);gap:20px}.land-feature{border:0}.land-actions{flex-wrap:wrap}}

</style>
</head>
<body>

<div class="landing" id="landing">
  <header class="land-head">
    <div class="land-brand"><div class="land-logo">◎</div><div><strong>AURA AI</strong><small>School AI Learning System</small></div></div>
    <div class="land-tools"><button class="land-pill" onclick="toggleTheme()">🌙</button><button class="land-pill">🌐 English ▾</button></div>
  </header>
  <div class="land-center">
    <div class="land-badge">✦ Your AI Learning Companion</div>
    <h1>Welcome to AURA AI</h1>
    <div class="land-sub">Learn • Practice • Grow<br>Ask questions, solve doubts, study subjects and prepare for your exams with AURA.</div>
    <div class="land-chat">
      <div class="land-chat-title">◎ Ask AURA</div>
      <div class="land-chat-sub">Type your question or start a conversation...</div>
      <textarea class="land-input" id="landingQuestion" placeholder="e.g. Physics ka question poochho..."></textarea>
      <div class="land-chat-bottom"><div class="land-modes"><span class="land-mode">◉ DeepThink</span><span class="land-mode">🌐 Search</span></div><button class="land-send" onclick="landingAsk()">↑</button></div>
    </div>
    <div class="land-actions"><button class="land-btn land-login" onclick="openAuth('login')">↪ Login</button><button class="land-btn land-create" onclick="openAuth('create')">＋ Create Account</button></div>
  </div>
  <div class="land-features">
    <div class="land-feature">📚<b>6 Subjects</b><small>Physics, Chemistry, Biology, Maths, Hindi, English</small></div>
    <div class="land-feature">📝<b>Tests</b><small>MCQ + Subjective</small></div>
    <div class="land-feature">⭐<b>Important Questions</b><small>Board Exam Focused</small></div>
    <div class="land-feature">📊<b>Progress</b><small>Track Your Growth</small></div>
    <div class="land-feature">👨‍🏫<b>Teacher Mode</b><small>Learn with AI</small></div>
  </div>
</div>

<div class="auth-back" id="authBack">
  <div class="auth-box">
    <button class="auth-close" onclick="closeAuth()">×</button>
    <h2 id="authTitle">Login to AURA AI</h2>
    <p id="authSubtitle">Apne AURA account se continue karo.</p>
    <input class="auth-input" id="authUser" placeholder="Username / Email" autocomplete="username">
    <input class="auth-input" id="authPass" type="password" placeholder="Password" autocomplete="current-password">
    <div class="auth-error" id="authError"></div>
    <button class="auth-submit" onclick="submitAuth()" id="authSubmit">Login</button>
    <div class="auth-note">School demo mode: account is stored locally on this computer.</div>
  </div>
</div>

<div class="app" id="dashboard">
<aside class="sidebar">
  <div class="brand"><div class="brand-icon">◎</div><div><div class="brand-name">AURA AI</div><div class="brand-sub">School AI Learning System</div></div></div>
  <div class="section">Main</div>
  <div class="sidebar-scroll">
  <button class="nav active" onclick="scrollTopPage()">🏠 <span>Home</span></button>
  <button class="nav" onclick="focusQuestion()">💬 <span>Ask AURA</span></button>
  <div class="history-wrap" id="historyWrap">
    <div class="history-title"><span>Chat History</span><button class="history-clear" onclick="clearAllHistory(event)">Clear all</button></div>
    <div id="historyList"></div>
  </div>
  <div class="section">Subjects</div>
  <button class="nav subject" onclick="subjectAsk('Physics')">⚛️ <span>Physics</span></button>
  <button class="nav subject" onclick="subjectAsk('Chemistry')">🧪 <span>Chemistry</span></button>
  <button class="nav subject" onclick="subjectAsk('Biology')">🧬 <span>Biology</span></button>
  <button class="nav subject" onclick="subjectAsk('Maths')">📐 <span>Maths</span></button>
  <button class="nav subject" onclick="subjectAsk('Hindi')">📖 <span>Hindi</span></button>
  <button class="nav subject" onclick="subjectAsk('English')">🔤 <span>English</span></button>
  <div class="section">Tools</div>
  <button class="nav" onclick="focusQuestion()">📝 <span>Tests</span></button>
  <button class="nav" onclick="askPreset('Important questions for Class 12 board exam')">⭐ <span>Important Questions</span></button>
  <button class="nav" onclick="askPreset('Show my progress')">📊 <span>Progress</span></button>
  <button class="nav" onclick="askPreset('Tell me about exam preparation')">📅 <span>Exam</span></button>
  <button class="nav" onclick="askPreset('Teacher mode')">👨‍🏫 <span>Teacher Mode</span></button>
  <button class="nav" onclick="toggleTheme()">⚙️ <span>Settings / Theme</span></button>
  </div>
  <div class="sidebar-bottom">◎ AURA • DeepSeek AI + Local Knowledge</div>
</aside>

<main class="main">
<header class="topbar"><div class="top-title">◎ AURA AI <span style="font-weight:400;color:var(--muted)">• Gemini AI</span></div><div class="top-actions"><button class="icon-btn" onclick="newChat()">＋ New Chat</button><button class="icon-btn" onclick="toggleTheme()">🌙</button><button class="logout-btn" onclick="logoutAURA()">↪ Logout</button></div></header>

<section class="content" id="content">
<div class="hero">
  <div class="welcome">◎ नमस्ते, मैं आपकी क्या मदद कर सकता हूँ?</div>

  <div class="chat-card">
    <div class="messages" id="messages">
      <div class="msg aura"><div class="bubble">Namaste! 👋 Main AURA AI hoon.<br><br>Class 11/12 ke questions poochho. Hindi ya English mein likh sakte ho, ya 🎙️ mic se bolo.</div></div>
    </div>
    <div class="composer">
      <div class="input-row">
        <input class="question" id="question" placeholder="Gemini को संदेश भेजें" onkeydown="if(event.key==='Enter') askAura()">
        <button class="action mic" id="micBtn" onclick="toggleVoice()">🎙️</button>
        <button class="action" onclick="askAura()">➤ Ask</button>
      </div>
      <div class="tools"><button class="tool" onclick="copyLast()">📋 Copy</button><button class="tool" onclick="newChat()">🗑️ New Chat</button><button class="tool" onclick="repeatLast()">🔊 Listen</button><button class="tool" onclick="regenerateLast()">↻ Regenerate</button></div>
      <button class="stop-generating" id="stopGenerating" onclick="stopGenerating()">■ Stop generating</button>
      <div class="voice-panel" id="voicePanel"><div class="orb">🎙️</div><div id="voiceText" class="voice-text">Boliye, AURA sun raha hai...</div><div class="voice-gender"><span>Voice:</span><button id="femaleVoiceBtn" class="active" onclick="setVoiceGender('female')">♀ Female</button><button id="neutralVoiceBtn" onclick="setVoiceGender('neutral')">◉ Natural</button></div><button class="stop" onclick="stopVoice()">Stop Voice</button></div>
    </div>
  </div>


</div>
</section>
</main>
</div>

<script>

let authMode="login";
function openAuth(mode){
  authMode=mode; document.getElementById("authBack").classList.add("show");
  document.getElementById("authTitle").textContent=mode==="login"?"Login to AURA AI":"Create your AURA Account";
  document.getElementById("authSubtitle").textContent=mode==="login"?"Apne AURA account se continue karo.":"Demo account banao aur AURA dashboard open karo.";
  document.getElementById("authSubmit").textContent=mode==="login"?"Login":"Create Account";
  document.getElementById("authError").textContent=""; document.getElementById("authUser").focus();
}
function closeAuth(){document.getElementById("authBack").classList.remove("show");}
function submitAuth(){
  const u=document.getElementById("authUser").value.trim(), p=document.getElementById("authPass").value;
  const err=document.getElementById("authError");
  if(!u||!p){err.textContent="Username aur password dono bharo.";return;}
  if(authMode==="create"){
    localStorage.setItem("auraUser",u); localStorage.setItem("auraPass",p); localStorage.setItem("auraLoggedIn","1");
    closeAuth(); showDashboard(); return;
  }
  const su=localStorage.getItem("auraUser"), sp=localStorage.getItem("auraPass");
  if(!su){err.textContent="Pehle Create Account karo.";return;}
  if(u!==su||p!==sp){err.textContent="Username ya password galat hai.";return;}
  localStorage.setItem("auraLoggedIn","1"); closeAuth(); showDashboard();
}
function showDashboard(){document.getElementById("landing").classList.add("hidden");document.getElementById("dashboard").style.display="flex";}
function logoutAURA(){localStorage.removeItem("auraLoggedIn");document.getElementById("landing").classList.remove("hidden");window.scrollTo(0,0);}
function landingAsk(){
  const q=document.getElementById("landingQuestion").value.trim();
  if(q){document.getElementById("question").value=q;openAuth("login");}
}
if(localStorage.getItem("auraLoggedIn")==="1")showDashboard();
else document.getElementById("dashboard").style.display="none";

let recognition=null, listening=false, lastAnswer="", currentChatId=null, abortController=null, voiceGender="female";

function makeId(){return 'chat_'+Date.now()+'_'+Math.random().toString(36).slice(2,7)}
function getChats(){try{return JSON.parse(localStorage.getItem('auraChats')||'[]')}catch(e){return []}}
function saveChats(chats){localStorage.setItem('auraChats',JSON.stringify(chats));renderHistory()}
function currentMessages(){return [...document.querySelectorAll('#messages .msg')].map(m=>{const b=m.querySelector('.bubble');return {type:m.classList.contains('user')?'user':'aura',text:(b?.dataset.raw||b?.innerText||'').trim()}}).filter(x=>x.text&&!x.text.includes('AURA soch raha hai...'))}
function ensureChat(){if(currentChatId)return currentChatId;currentChatId=makeId();return currentChatId}
function persistCurrentChat(){
  const msgs=currentMessages(); if(!msgs.length)return;
  const chats=getChats(); const firstUser=msgs.find(m=>m.type==='user');
  const title=(firstUser?firstUser.text:'New Chat').slice(0,48);
  let chat=chats.find(c=>c.id===currentChatId);
  if(!chat){chat={id:currentChatId,title,created:Date.now(),messages:[]};chats.unshift(chat)}
  chat.title=title;chat.messages=msgs;chat.updated=Date.now();
  chats.sort((a,b)=>(b.updated||b.created)-(a.updated||a.created));
  saveChats(chats.slice(0,40));
}
function renderHistory(){
  const list=document.getElementById('historyList'); if(!list)return; list.innerHTML='';
  const chats=getChats();
  if(!chats.length){list.innerHTML='<div style="font-size:11px;color:var(--muted);padding:7px 8px">No chats yet</div>';return;}
  chats.forEach(c=>{
    const row=document.createElement('div');row.className='history-item';
    const open=document.createElement('button');open.className='history-open';open.title=c.title;open.textContent='💬 '+c.title;open.onclick=()=>openChat(c.id);
    const del=document.createElement('button');del.className='history-delete';del.title='Delete chat';del.textContent='🗑';del.onclick=(e)=>{e.stopPropagation();deleteChat(c.id)};
    row.append(open,del);list.appendChild(row);
  });
}
function openChat(id){
  const c=getChats().find(x=>x.id===id); if(!c)return;
  currentChatId=id; lastAnswer=''; const box=document.getElementById('messages'); box.innerHTML=''; box.style.display='block';
  c.messages.forEach(m=>addMessage(m.text,m.type,false));
  const ans=[...c.messages].reverse().find(m=>m.type==='aura'); if(ans)lastAnswer=ans.text;
  box.scrollTop=box.scrollHeight;
}
function deleteChat(id){
  const c=getChats().find(x=>x.id===id); if(!c)return;
  if(!confirm('Delete this chat?'))return;
  saveChats(getChats().filter(x=>x.id!==id));
  if(currentChatId===id)newChat(false);
}
function clearAllHistory(e){e?.stopPropagation();if(!getChats().length)return;if(!confirm('Delete all chat history?'))return;localStorage.removeItem('auraChats');currentChatId=null;newChat(false);renderHistory()}

function addMessage(text,type='aura',animate=true){
  const box=document.getElementById('messages');
  const row=document.createElement('div'); row.className='msg '+type+(animate?' msg-in':'');
  const bubble=document.createElement('div'); bubble.className='bubble'; bubble.textContent=text;
  row.appendChild(bubble); box.appendChild(row); box.scrollTop=box.scrollHeight; return {row,bubble};
}
function addAnswerActions(row,text){
  row.querySelector('.bubble').dataset.raw=text;
  const actions=document.createElement('div');actions.className='msg-actions';
  const cp=document.createElement('button');cp.textContent='📋 Copy';cp.onclick=()=>navigator.clipboard?.writeText(text);
  const ls=document.createElement('button');ls.textContent='🔊 Listen';ls.onclick=()=>speakText(text);
  const rg=document.createElement('button');rg.textContent='↻ Regenerate';rg.onclick=()=>regenerateQuestion(row);
  actions.append(cp,ls,rg);row.querySelector('.bubble').appendChild(actions);
}
function focusQuestion(){document.getElementById('question').focus()}
function scrollTopPage(){document.getElementById('content').scrollTo({top:0,behavior:'smooth'})}
function subjectAsk(s){document.getElementById('question').value=s+' ka important topic samjhao';focusQuestion()}
function askPreset(q){document.getElementById('question').value=q;askAura()}
function setStatus(t){const el=document.getElementById('status');if(el)el.textContent=t}

async function askAura(){
  const input=document.getElementById('question'), question=input.value.trim(); if(!question)return;
  ensureChat(); document.getElementById('messages').style.display='block';
  addMessage(question,'user'); input.value='';
  const think=addMessage('', 'aura'); think.bubble.innerHTML='<div class="typing" aria-label="AURA is thinking"><i></i><i></i><i></i><span style="margin-left:5px">AURA सोच रहा है...</span></div>';
  setStatus('● Thinking...'); document.getElementById('stopGenerating').classList.add('show');
  abortController=new AbortController();
  try{
    const response=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question}),signal:abortController.signal});
    const data=await response.json(); lastAnswer=data.answer||'No answer received.';
    think.bubble.innerHTML=''; think.bubble.classList.add('answer-in');
    typeAnswer(think.bubble,lastAnswer,()=>{addAnswerActions(think.row,lastAnswer);persistCurrentChat();});
    setStatus('● Ready');
  }catch(e){
    if(e.name==='AbortError'){think.row.remove();setStatus('● Stopped');}
    else {think.bubble.textContent='AURA server se connection nahi ho pa raha.';setStatus('● Server error');persistCurrentChat();}
  }finally{document.getElementById('stopGenerating').classList.remove('show');abortController=null}
}
function typeAnswer(el,text,done){
  let i=0; const step=()=>{i=Math.min(i+Math.max(2,Math.ceil(text.length/180)),text.length);el.textContent=text.slice(0,i);document.getElementById('messages').scrollTop=document.getElementById('messages').scrollHeight;if(i<text.length)setTimeout(step,8);else done?.()};step();
}
function stopGenerating(){if(abortController)abortController.abort()}
function regenerateQuestion(row){
  const msgs=[...document.querySelectorAll('#messages .msg.user')]; const idx=[...document.querySelectorAll('#messages .msg')].indexOf(row); const prev=msgs.filter(m=>[...document.querySelectorAll('#messages .msg')].indexOf(m)<idx).pop(); if(!prev)return;
  document.getElementById('question').value=prev.querySelector('.bubble')?.innerText||''; askAura();
}
function regenerateLast(){const users=[...document.querySelectorAll('#messages .msg.user')];if(!users.length)return;document.getElementById('question').value=users[users.length-1].querySelector('.bubble').innerText;askAura()}

function initSpeech(){
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){alert('Is browser mein voice recognition available nahi hai. Microsoft Edge ya Chrome try karo.');return null;}
  const r=new SR(); r.lang='hi-IN'; r.interimResults=false; r.continuous=false;
  r.onstart=()=>{listening=true;document.getElementById('micBtn').classList.add('listening');document.getElementById('voicePanel').classList.add('show','listening');document.getElementById('voiceText').textContent='Sun raha hoon... 🎙️'};
  r.onresult=e=>{document.getElementById('question').value=e.results[0][0].transcript;document.getElementById('voiceText').textContent='Question mil gaya ✓';setTimeout(()=>askAura(),350)};
  r.onerror=()=>stopVoice(); r.onend=()=>{if(listening)stopVoice()}; return r;
}
function toggleVoice(){if(listening){stopVoice();return}recognition=recognition||initSpeech();if(!recognition)return;try{recognition.start()}catch(e){}}
function stopVoice(){listening=false;if(recognition)try{recognition.stop()}catch(e){}document.getElementById('micBtn').classList.remove('listening');document.getElementById('voicePanel').classList.remove('listening');document.getElementById('voiceText').textContent='Voice Mode ready'}
function setVoiceGender(g){voiceGender=g;document.getElementById('femaleVoiceBtn').classList.toggle('active',g==='female');document.getElementById('neutralVoiceBtn').classList.toggle('active',g==='neutral');localStorage.setItem('auraVoiceGender',g)}
function chooseVoice(text){
  const voices=speechSynthesis.getVoices(); if(!voices.length)return null;
  const hindi=/[\u0900-\u097F]/.test(text); const lang=hindi?'hi':'en';
  let pool=voices.filter(v=>(v.lang||'').toLowerCase().startsWith(lang)); if(!pool.length)pool=voices;
  if(voiceGender==='female'){
    const femaleNames=['female','heera','kalpana','swara','neerja','aditi','zira','jenny','samantha','susan','hazel','sonia','veena','google हिन्दी','google hindi'];
    const f=pool.find(v=>femaleNames.some(n=>(v.name||'').toLowerCase().includes(n))); if(f)return f;
  }
  return pool[0]||voices[0];
}
function speakText(text){
  if(!('speechSynthesis' in window)){alert('Browser voice output available nahi hai.');return}
  speechSynthesis.cancel(); const u=new SpeechSynthesisUtterance(text);u.lang=/[\u0900-\u097F]/.test(text)?'hi-IN':'en-IN';u.rate=.95;u.pitch=1.05;const v=chooseVoice(text);if(v)u.voice=v;speechSynthesis.speak(u);
}
function repeatLast(){if(!lastAnswer){alert('Pehle AURA se koi answer lo.');return}speakText(lastAnswer)}
function copyLast(){if(lastAnswer)navigator.clipboard?.writeText(lastAnswer)}
function newChat(save=true){if(save)persistCurrentChat();currentChatId=null;lastAnswer='';document.getElementById('messages').innerHTML='<div class="msg aura msg-in"><div class="bubble">Namaste! 👋 Main AURA AI hoon.<br><br>Class 11/12 ke questions poochho. Hindi ya English mein likh sakte ho, ya 🎙️ mic se bolo.</div></div>';document.getElementById('messages').style.display='none';document.getElementById('question').value='';setStatus('● Ready');renderHistory()}
function toggleTheme(){document.body.classList.toggle('dark');localStorage.setItem('auraDark',document.body.classList.contains('dark'))}
if(localStorage.getItem('auraDark')==='true')document.body.classList.add('dark');
if(localStorage.getItem('auraVoiceGender'))setVoiceGender(localStorage.getItem('auraVoiceGender'));
if('speechSynthesis' in window)speechSynthesis.onvoiceschanged=()=>{};
renderHistory();
</script>
</body>
</html>
"""


        self.send_response(200)

        self.send_header(
            "Content-Type",
            "text/html; charset=utf-8"
        )

        self.end_headers()

        self.wfile.write(
            page.encode("utf-8")
        )


    def do_POST(self):

        global test_question, test_score, test_active

        if self.path == "/api-status":
            response = json.dumps({
                "configured": bool(DEEPSEEK_API_KEY),
                "provider": "Gemini",
                "model": GEMINI_MODEL
            }, ensure_ascii=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(response.encode("utf-8"))
            return

        if self.path != "/ask":

            self.send_response(404)
            self.end_headers()
            return


        try:

            length = int(
                self.headers.get(
                    "Content-Length",
                    0
                )
            )

            data = self.rfile.read(length)

            request_data = json.loads(
                data.decode("utf-8")
            )

            question = request_data.get(
                "question",
                ""
            )

            q = question.lower()
            # ==============================
            # TEST ANSWER CHECKING
            # ==============================

            if test_active and q in ["a", "b", "c", "d"]:

                if test_question == 1:

                    if q == "b":

                        test_score += 1

                        answer = """✅ Correct!

बहुत बढ़िया! 🎯

तुम्हारा answer: B) Coulomb
सही answer: B) Coulomb

Score: 1/1

------------------------------

Question 2:

दो समान electric charges के बीच क्या होता है?

A) Attraction
B) Repulsion
C) No force
D) कोई force नहीं

अपना answer केवल A, B, C या D में लिखो."""

                        test_question = 2

                    else:

                        answer = """❌ Incorrect

सही answer: B) Repulsion

Score: 0/1

------------------------------

Question 2:

दो समान electric charges के बीच क्या होता है?

A) Attraction
B) Repulsion
C) No force
D) कोई force नहीं

अपना answer केवल A, B, C या D में लिखो."""

                        test_question = 2


                elif test_question == 2:

                    if q == "b":

                        test_score += 1

                        answer = """✅ Correct! 🎯

दो समान charges एक-दूसरे को repel करते हैं।

Score: 2/2

------------------------------

Question 3:

Electric field की SI unit क्या है?

A) N/C
B) C/N
C) Joule
D) Watt

अपना answer केवल A, B, C या D में लिखो."""

                    else:

                        answer = """❌ Incorrect

सही answer: B) Repulsion

Score: """ + str(test_score) + """/2

------------------------------

Question 3:

Electric field की SI unit क्या है?

A) N/C
B) C/N
C) Joule
D) Watt

अपना answer केवल A, B, C या D में लिखो."""

                    test_question = 3


                elif test_question == 3:

                    if q == "a":

                        test_score += 1

                        answer = """✅ Correct! 🎯

Electric field की SI unit N/C होती है।

Score: """ + str(test_score) + """/3

🎉 Test का छोटा demo complete!

AURA में अगला step:
10-question full test + final score."""

                    else:

                        answer = """❌ Incorrect

सही answer: A) N/C

Final Score: """ + str(test_score) + """/3

🎯 Test complete!

AURA में अगला step:
10-question full test + final score."""

                    test_active = False

                response = json.dumps(
                    {
                        "answer": answer
                    },
                    ensure_ascii=False
                )

                self.send_response(200)

                self.send_header(
                    "Content-Type",
                    "application/json; charset=utf-8"
                )

                self.end_headers()

                self.wfile.write(
                    response.encode("utf-8")
                )

                return

            # ==============================
            # GREETING
            # ==============================

            if (
                "hello" in q
                or "hi aura" in q
                or q == "hi"
            ):

                answer = """Hello! 👋

Main AURA AI hoon.

Main Class 12 MP Board students ke liye
Offline Learning Assistant hoon.

Physics, Chemistry aur Maths ke
questions mujhse pooch sakte ho."""


            # ==============================
            # PHYSICS CHAPTER 1
            # ELECTRIC CHARGES AND FIELDS
            # ==============================
            # ==============================
            # PHYSICS CHAPTER 1 MCQ MODE
            # ==============================
            # ==============================
            # PHYSICS CHAPTER 1 TEST MODE
            # ==============================

            elif (
                "physics chapter 1 test" in q
                or "chapter 1 test" in q
                or "physics test" in q
            ):

                test_question = 1
                test_score = 0
                test_active = True

                answer = """🎯 AURA PHYSICS TEST

Chapter 1: Electric Charges and Fields

Question 1:

Electric charge की SI unit क्या है?

A) Newton
B) Coulomb
C) Volt
D) Ampere

अपना answer केवल A, B, C या D में लिखो."""
            elif (
                "mcq" in q
                or "mcqs" in q
                or "objective" in q
                or "बहुविकल्पीय" in q
            ):

                answer = """📝 Class 12 Physics
Chapter 1: Electric Charges and Fields

MCQ 1:

Electric charge की SI unit क्या है?

A) Newton
B) Coulomb
C) Volt
D) Ampere

✅ Answer: B) Coulomb

------------------------------

MCQ 2:

दो समान charges के बीच क्या होता है?

A) Attraction
B) Repulsion
C) No force
D) केवल gravitational force

✅ Answer: B) Repulsion

------------------------------

MCQ 3:

Coulomb's Law में force किसके inversely proportional है?

A) r
B) r²
C) 1/r
D) 1/r²

✅ Answer: D) 1/r²

------------------------------

MCQ 4:

Electric field की SI unit क्या है?

A) N/C
B) C/N
C) Joule
D) Watt

✅ Answer: A) N/C

------------------------------

MCQ 5:

Electric dipole में charges होते हैं:

A) दो समान positive
B) दो समान negative
C) equal और opposite
D) कोई भी दो charges

✅ Answer: C) equal और opposite

------------------------------

📌 अगर तुम चाहो तो अगला command:
"Physics Chapter 1 test"

लिखकर AURA का test mode शुरू कर सकते हो।"""
            elif (
                "electric charge" in q
                or "विद्युत आवेश" in q
                or "charge kya" in q
                or "charge क्या" in q
            ):

                answer = """⚡ Electric Charge

Electric charge पदार्थ का एक fundamental property है,
जिसके कारण electric force उत्पन्न होता है।

Charge दो प्रकार के होते हैं:

1. Positive charge (+)
2. Negative charge (-)

SI unit = Coulomb (C)

दो समान charges एक-दूसरे को repel करते हैं।
दो opposite charges एक-दूसरे को attract करते हैं."""


            elif (
                "properties of charge" in q
                or "charge ki properties" in q
                or "आवेश के गुण" in q
            ):

                answer = """⚡ Properties of Electric Charge

Electric charge के मुख्य गुण:

1. Additivity of charge
   Total charge = सभी charges का algebraic sum

2. Conservation of charge
   Charge न तो बनाया जा सकता है और न नष्ट किया जा सकता है।

3. Quantisation of charge

   q = ne

जहाँ:
q = charge
n = integer
e = electronic charge

e = 1.6 × 10⁻¹⁹ C"""


            elif (
                "coulomb" in q
                or "कूलॉम" in q
            ):

                answer = """⚡ Coulomb's Law

दो point charges के बीच electric force:

F = k q₁q₂ / r²

जहाँ:

F = Electric force
q₁ और q₂ = charges
r = दोनों charges के बीच distance
k = 1 / 4πε₀

Vacuum में:

k ≈ 9 × 10⁹ N m²/C²

Force distance के square के inversely proportional होता है."""


            elif (
                "electric field intensity" in q
                or "electric field" in q
                or "विद्युत क्षेत्र" in q
            ):

                answer = """⚡ Electric Field

किसी charge के आसपास का वह region जहाँ
दूसरे charge पर electric force लगता है,
electric field कहलाता है।

Electric field intensity:

E = F / q₀

जहाँ:

E = Electric field intensity
F = force
q₀ = test charge

SI unit = N/C

Point charge के कारण:

E = kQ / r²"""


            elif (
                "electric field lines" in q
                or "field lines" in q
                or "विद्युत क्षेत्र रेखा" in q
            ):

                answer = """⚡ Electric Field Lines

Electric field lines imaginary lines होती हैं
जो electric field की direction बताती हैं।

Important points:

• Positive charge से lines बाहर निकलती हैं।
• Negative charge की ओर lines जाती हैं।
• दो electric field lines कभी intersect नहीं करतीं।
• जहाँ lines ज्यादा close हों, वहाँ field stronger होता है।"""


            elif (
                "electric dipole" in q
                or "विद्युत द्विध्रुव" in q
            ):

                answer = """⚡ Electric Dipole

दो equal और opposite charges,
जो थोड़ी दूरी पर रखे हों,
electric dipole कहलाते हैं।

Charges:

+q और -q

Electric dipole moment:

p = q × 2a

जहाँ 2a = दोनों charges के बीच distance

Direction:
Negative charge से positive charge की ओर."""


            elif (
                "dipole moment" in q
                or "dipole ka moment" in q
                or "द्विध्रुव आघूर्ण" in q
            ):

                answer = """⚡ Electric Dipole Moment

Electric dipole moment:

p = q × d

जहाँ:

p = dipole moment
q = charge
d = charges के बीच distance

SI unit = C m

Direction: negative charge से positive charge की ओर."""


            elif (
                "gauss law" in q
                or "gauss's law" in q
                or "गाउस का नियम" in q
            ):

                answer = """⚡ Gauss's Law

Gauss's Law के अनुसार किसी closed surface से
कुल electric flux:

Φ = Q / ε₀

जहाँ:

Φ = Electric flux
Q = enclosed charge
ε₀ = permittivity of free space

यह law symmetric charge distributions में
electric field निकालने में बहुत useful है."""


            elif (
                "electric flux" in q
                or "विद्युत फ्लक्स" in q
            ):

                answer = """⚡ Electric Flux

Electric field के perpendicular surface से
passing field का measure electric flux कहलाता है।

Formula:

Φ = E A cosθ

जहाँ:

E = Electric field
A = Area
θ = E और area vector के बीच angle

SI unit = N m²/C"""


            elif (
                "chapter 1 formula" in q
                or "chapter 1 formulas" in q
                or "electric charges formula" in q
            ):

                answer = """📘 Class 12 Physics Chapter 1
Electric Charges and Fields

Important Formulas:

1. Coulomb's Law
F = k q₁q₂ / r²

2. Electric Field
E = F/q

3. Point Charge
E = kQ/r²

4. Electric Flux
Φ = EA cosθ

5. Gauss Law
Φ = Q/ε₀

6. Dipole Moment
p = qd

इन formulas को numerical questions के लिए
जरूर याद रखो."""


            elif (
                "ohm" in q
            ):

                answer = """Ohm's Law:

V = IR

V = Voltage
I = Current
R = Resistance

यानी:

Voltage = Current × Resistance"""


            elif (
                "photosynthesis" in q
            ):

                answer = """Photosynthesis:

Photosynthesis एक process है जिसमें green plants
sunlight की help से अपना food बनाते हैं।

Carbon dioxide और water का उपयोग होता है
और oxygen release होती है."""


            elif (
                "newton" in q and "first law" in q
            ):

                answer = """Newton's First Law:

किसी वस्तु पर external unbalanced force नहीं लगता,
तो वस्तु अपनी state नहीं बदलती।

Rest में वस्तु rest में रहती है।

Motion में वस्तु same velocity से
straight line में चलती रहती है।

इसे Law of Inertia भी कहते हैं."""


            else:

                # Local knowledge did not match, so use the Gemini AI brain.
                answer = gemini_answer(question)


            response = json.dumps(
                {
                    "answer": answer
                },
                ensure_ascii=False
            )

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )

            self.end_headers()

            self.wfile.write(
                response.encode("utf-8")
            )


        except Exception as error:

            self.send_response(500)

            self.send_header(
                "Content-Type",
                "application/json; charset=utf-8"
            )

            self.end_headers()

            response = json.dumps(
                {
                    "answer": "AURA Error: " + str(error)
                },
                ensure_ascii=False
            )

            self.wfile.write(
                response.encode("utf-8")
            )


server = HTTPServer(
    ("localhost", 8000),
    AuraServer
)


print("==============================")
print("        AURA AI SERVER")
print("==============================")
print()
print("AURA is running with Gemini AI backend!")
print()
print("Open:")
print("http://localhost:8000")
print()
print("Gemini API:", "Configured" if GEMINI_API_KEY else "NOT configured")
print()
print("Press CTRL + C to stop")
print("==============================")


server.serve_forever()