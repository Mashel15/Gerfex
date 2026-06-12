import { useEffect, useRef, useState } from "react";
import { registerPlugin } from "@capacitor/core";

const GerfexNative = registerPlugin("Gerfex");

async function askGerfexNative(prompt, modelState = {}) {
  const nativeRes = await GerfexNative.think({ message: prompt, model_state: modelState });
  const parsed = JSON.parse(nativeRes.result || "{}");
  return {
    ok: parsed.ok,
    reply: parsed.reply || "لا يوجد رد.",
    speaker: "Gerfex",
    raw: parsed.raw
  };
}

const sections = [
  ["models", "🤖", "النماذج"],
  ["sessions", "💬", "الجلسات"],
  ["learning", "🧠", "التعليم"],
  ["dev", "⚙️", "التطوير"]
];

const defaultModels = [
  { id: 1, name: "Queen", type: "Local", model: "queen-core", connected: false, mute: false, hold: false },
  { id: 2, name: "ChatGPT", type: "API", model: "gpt", connected: false, mute: false, hold: false },
  { id: 3, name: "DeepSeek", type: "API/Local", model: "deepseek", connected: false, mute: false, hold: false }
];

function load(key, fallback) {
  try {
    return JSON.parse(localStorage.getItem(key)) || fallback;
  } catch {
    return fallback;
  }
}

export default function App() {
  const [menu, setMenu] = useState(false);
  const [quick, setQuick] = useState(false);
  const [section, setSection] = useState("sessions");
  const [devDoor, setDevDoor] = useState(null);
  const [devRoot, setDevRoot] = useState("system");
  const [devPath, setDevPath] = useState("");
  const [devItems, setDevItems] = useState([]);
  const [devFilePath, setDevFilePath] = useState("");
  const [devContent, setDevContent] = useState("");
  const [devStatus, setDevStatus] = useState("");
  const [input, setInput] = useState("");
  const [listening, setListening] = useState(false);
  const [voiceInput, setVoiceInput] = useState(false);

  const [messages, setMessages] = useState(() =>
    load("g_messages", load("g_main_session", [{ speaker: "Gerfex", content: "النظام جاهز." }]))
  );
  const [currentSession, setCurrentSession] = useState(() => load("g_current_session", "main"));

  const [models, setModels] = useState(() => load("g_models", defaultModels));
  const [sessions, setSessions] = useState(() => load("g_sessions", []));
  const [savedSessions, setSavedSessions] = useState(() => load("g_saved_sessions", []));
  const [projects, setProjects] = useState(() => load("g_projects", []));
  const [learning, setLearning] = useState(() =>
    load("g_learning", { queue: [], done: [] })
  );
  const [learningSession, setLearningSession] = useState(null);

  const [showAddModel, setShowAddModel] = useState(false);
  const [expandedModel, setExpandedModel] = useState(null);
  const [form, setForm] = useState({
    name: "",
    type: "API",
    model: "",
    baseUrl: "",
    apiKey: "",
    path: ""
  });

  const [learnPages, setLearnPages] = useState(10);
  const [ideaPages, setIdeaPages] = useState(2);

  const bottom = useRef(null);
  const textRef = useRef(null);
  const fileRef = useRef(null);

  useEffect(() => localStorage.setItem("g_messages", JSON.stringify(messages)), [messages]);
  useEffect(() => {
    if (currentSession === "main") {
      localStorage.setItem("g_main_session", JSON.stringify(messages));
    }
  }, [messages, currentSession]);
  useEffect(() => localStorage.setItem("g_current_session", JSON.stringify(currentSession)), [currentSession]);
  useEffect(() => localStorage.setItem("g_models", JSON.stringify(models)), [models]);
  useEffect(() => localStorage.setItem("g_sessions", JSON.stringify(sessions)), [sessions]);
  useEffect(() => localStorage.setItem("g_saved_sessions", JSON.stringify(savedSessions)), [savedSessions]);
  useEffect(() => localStorage.setItem("g_projects", JSON.stringify(projects)), [projects]);
  useEffect(() => {
    if (learning.ideas) {
      const clean = { ...learning };
      delete clean.ideas;
      setLearning(clean);
    }
  }, []);

  useEffect(() => localStorage.setItem("g_learning", JSON.stringify(learning)), [learning]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (!textRef.current) return;
    textRef.current.style.height = "auto";
    textRef.current.style.height = Math.min(textRef.current.scrollHeight, 150) + "px";
  }, [input]);

  function speak(text) {
    try {
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = "ar-SA";
      window.speechSynthesis.speak(u);
    } catch {}
  }

  function addReply(content, speaker = "Gerfex", withVoice = false) {
    setMessages((m) => [...m, { speaker, content }]);
    if (withVoice) speak(content);
  }

  function startVoice() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return addReply("المتصفح لا يدعم الصوت.");

    const r = new SR();
    r.lang = "ar-SA";
    r.continuous = false;
    r.interimResults = false;

    r.onstart = () => setListening(true);
    r.onend = () => setListening(false);
    r.onerror = (e) => {
      setListening(false);
      addReply("خطأ في الصوت: " + (e.error || "unknown"));
    };
    r.onresult = (e) => {
      const t = e.results?.[0]?.[0]?.transcript || "";
      if (t.trim()) {
        setInput(t);
        setVoiceInput(true);
      }
    };

    r.start();
  }

  function handleAttach(e) {
    const file = e.target.files && e.target.files[0];
    if (!file) return;

    setMessages((m) => [
      ...m,
      {
        speaker: "Mashel",
        content: "📎 مرفق: " + file.name + " (" + Math.max(1, Math.round(file.size / 1024)) + " KB)"
      }
    ]);

    e.target.value = "";
  }

  function persistLearningSessionMessages(item, msgs) {
    if (!item) return;
    const src = item.source || "queue";

    setLearning((l) => ({
      ...l,
      [src]: (l[src] || []).map((x) =>
        x.id === item.id ? { ...x, messages: msgs } : x
      )
    }));
  }

  async function send() {
    const text = input.trim();
    if (!text) return;

    const shouldSpeak = voiceInput;

    const queenModel = models.find((m) => m.name === "Queen") || {};
    const modelState = {
      name: "Queen",
      connected: !!queenModel.connected,
      mute: !!queenModel.mute,
      hold: !!queenModel.hold
    };

    if (!modelState.connected) {
      // Gerfex Core remains available even if Queen provider toggle is off.
      // Queen is only a replaceable provider inside GerfexIntegratedV1.
    }

    if (modelState.hold) {
      return;
    }

    if (learningSession) {
      if (text === "اعتمد" || text === "اعتماد" || text === "اعتمد الجلسة") {
        const mashelMessages = (learningSession.messages || [])
          .filter((m) => (m.speaker || "") === "Mashel")
          .map((m) => (m.content || "").trim())
          .filter(Boolean);

        const learnText = mashelMessages[mashelMessages.length - 1] || "";

        try {
          const data = await askGerfexNative(`[LEARNING_SESSION]\n${learnText}\nاعتمد الجلسة`, { ...modelState, learning_session: true });
          setInput("");
          setVoiceInput(false);
          const approvalMsg = { speaker: data.speaker || "Queen", content: data.reply || "تم اعتماد جلسة التعلم." };
          const approvedMessages = [...(learningSession.messages || []), approvalMsg];
          setLearningSession((x) => ({ ...x, messages: approvedMessages }));
          persistLearningSessionMessages(learningSession, approvedMessages);
        } catch {
          alert("فشل اعتماد جلسة التعلم.");
        }
        return;
      }

      if (text === "لا تعتمد" || text === "لا تعتمد الجلسة") {
        setInput("");
        setVoiceInput(false);
        const noApprovalMsg = { speaker: "Gerfex", content: "لم يتم اعتماد الجلسة. بقيت محفوظة كما هي." };
        const noApprovalMessages = [...(learningSession.messages || []), noApprovalMsg];
        setLearningSession((x) => ({ ...x, messages: noApprovalMessages }));
        persistLearningSessionMessages(learningSession, noApprovalMessages);
        return;
      }

      const userMsg = { speaker: "Mashel", content: text };
      const nextMessages = [...(learningSession.messages || []), userMsg];
      setLearningSession((x) => ({ ...x, messages: nextMessages }));
      persistLearningSessionMessages(learningSession, nextMessages);
      setInput("");
      setVoiceInput(false);

      try {
        const data = await askGerfexNative(text, { ...modelState, learning_session: true });

        if (!modelState.mute) {
          const withReply = [...nextMessages, { speaker: data.speaker || "Queen", content: data.reply || "لا يوجد رد." }];
          setLearningSession((x) => ({ ...x, messages: withReply }));
          persistLearningSessionMessages(learningSession, withReply);
        }
      } catch {
        setLearningSession((x) => ({ ...x, messages: [...nextMessages, { speaker: "Gerfex", content: "خطأ في Gerfex الداخلي" }] }));
      }
      return;
    }

    setMessages((m) => [...m, { speaker: "Mashel", content: text }]);
    setInput("");
    setVoiceInput(false);

    try {
      const data = await askGerfexNative(text, modelState);

      if (!modelState.mute) {
        addReply(data.reply || "لا يوجد رد.", data.speaker || "Gerfex", shouldSpeak);
      }
    } catch (err) {
      addReply(`خطأ في Gerfex الداخلي: ${err?.message || err}`);
    }
  }

  function saveSession() {
    setSessions((s) => [
      {
        id: Date.now(),
        title: "جلسة " + new Date().toLocaleString(),
        date: new Date().toLocaleString(),
        messages: [...messages]
      },
      ...s
    ]);
  }

  function newSession() {
    setSessions((s) => [
      {
        id: Date.now(),
        title: "جلسة " + new Date().toLocaleString(),
        date: new Date().toLocaleString(),
        messages: [...messages]
      },
      ...s
    ]);
    setCurrentSession("new");
    setMessages([{ speaker: "Gerfex", content: "جلسة جديدة." }]);
  }

  function clearSession() {
    setMessages([{ speaker: "Gerfex", content: "تم مسح الجلسة الحالية." }]);
  }

  function openMainSession() {
    setLearningSession(null);
    if (currentSession !== "main") {
      setSessions((list) => [
        {
          id: Date.now(),
          title: "جلسة " + new Date().toLocaleString(),
          date: new Date().toLocaleString(),
          messages: [...messages]
        },
        ...list
      ]);
    }

    setCurrentSession("main");
    setMessages(load("g_main_session", [{ speaker: "Gerfex", content: "النظام جاهز." }]));
    setMenu(false);
  }


  function addModel() {
    if (!form.name.trim()) return;
    const id = Math.max(0, ...models.map((m) => m.id)) + 1;
    setModels((m) => [...m, { id, ...form, connected: false, mute: false, hold: false }]);
    setForm({ name: "", type: "API", model: "", baseUrl: "", apiKey: "", path: "" });
    setShowAddModel(false);
  }

  function updateModel(id, patch) {
    setModels((m) => m.map((x) => (x.id === id ? { ...x, ...patch } : x)));
  }

  function moveModel(id, dir) {
    setModels((list) => {
      const index = list.findIndex((x) => x.id === id);
      if (index < 0) return list;

      const next = dir === "up" ? index - 1 : index + 1;
      if (next < 0 || next >= list.length) return list;

      const copy = [...list];
      const temp = copy[index];
      copy[index] = copy[next];
      copy[next] = temp;
      return copy;
    });
  }

  function editModel(id) {
    const model = models.find((x) => x.id === id);
    if (!model) return;

    const name = prompt("اسم النموذج:", model.name || "");
    if (name === null) return;

    const type = prompt("نوع النموذج:", model.type || "");
    if (type === null) return;

    const modelName = prompt("Model Name:", model.model || "");
    if (modelName === null) return;

    const baseUrl = prompt("Base URL:", model.baseUrl || "");
    if (baseUrl === null) return;

    const apiKey = prompt("API Key اختياري:", model.apiKey || "");
    if (apiKey === null) return;

    const path = prompt("Path / Local Server اختياري:", model.path || "");
    if (path === null) return;

    setModels((list) => list.map((x) =>
      x.id === id
        ? {
            ...x,
            name: name.trim() || x.name,
            type: type.trim(),
            model: modelName.trim(),
            baseUrl: baseUrl.trim(),
            apiKey: apiKey.trim(),
            path: path.trim()
          }
        : x
    ));
  }

  function deleteModel(id) {
    const model = models.find((x) => x.id === id);
    if (!model) return;

    if (model.name === "Queen") {
      const answer = prompt("Queen هو العقل الأساسي. اكتب DELETE QUEEN للتأكيد:");
      if (answer !== "DELETE QUEEN") return;
    } else {
      const ok = confirm("هل تريد حذف النموذج: " + model.name + "؟");
      if (!ok) return;
    }

    setModels((list) => list.filter((x) => x.id !== id));
  }


  function makeLearn(kind, amount) {
    kind = "session";
    const all = String(amount) === "all";
    const unit = kind === "idea" ? "سطر" : "صفحة";
    const count = all ? messages.length : (kind === "idea" ? Number(amount) : Number(amount) * 12);

    const item = {
      id: Date.now(),
      title: kind === "idea" ? "فكرة من الجلسة الحالية" : "جلسة تعلم من الجلسة الحالية",
      date: new Date().toLocaleString(),
      pages: all ? "كل الجلسة" : amount + " " + unit,
      messages: messages.slice(-count)
    };

    setLearning((l) => ({ ...l, queue: [item, ...(l.queue || [])] }));
    addReply("تمت إضافة الجلسة إلى جلسات التعلم.");
  }

  function moveLearn(from, to, id) {
    setLearning((l) => {
      const item = l[from].find((x) => x.id === id);
      if (!item) return l;
      return {
        ...l,
        [from]: l[from].filter((x) => x.id !== id),
        [to]: [item, ...l[to]]
      };
    });
  }

  function deleteLearn(from, id) {
    setLearning((l) => ({ ...l, [from]: l[from].filter((x) => x.id !== id) }));
  }

  function renameSession(id, target) {
    const title = prompt("اكتب اسم الجلسة الجديد:");
    if (!title || !title.trim()) return;

    if (target === "sessions") {
      setSessions((list) => list.map((x) => x.id === id ? { ...x, title: title.trim() } : x));
    }

    if (target === "saved") {
      setSavedSessions((list) => list.map((x) => x.id === id ? { ...x, title: title.trim() } : x));
    }

    if (target === "projects") {
      setProjects((list) => list.map((x) => x.id === id ? { ...x, title: title.trim() } : x));
    }
  }

  function moveSessionToSaved(item) {
    setSavedSessions((list) => [{ ...item, movedAt: new Date().toLocaleString() }, ...list]);
    setSessions((list) => list.filter((x) => x.id !== item.id));
  }

  function moveSessionToProjects(item) {
    setProjects((list) => [{ ...item, movedAt: new Date().toLocaleString() }, ...list]);
    setSessions((list) => list.filter((x) => x.id !== item.id));
  }

  function moveSessionBetween(item, from, to) {
    const removeFrom = (list) => list.filter((x) => x.id !== item.id);
    const moved = { ...item, movedAt: new Date().toLocaleString() };

    if (from === "sessions") setSessions(removeFrom);
    if (from === "saved") setSavedSessions(removeFrom);
    if (from === "projects") setProjects(removeFrom);

    if (to === "sessions") setSessions((list) => [moved, ...list]);
    if (to === "saved") setSavedSessions((list) => [moved, ...list]);
    if (to === "projects") setProjects((list) => [moved, ...list]);
  }

  function renderSessionCard(item, source) {
    return (
      <div style={st.card} key={item.id}>
        <b>{item.title}</b>
        <small>{item.date || ""}</small>
        <div style={{ ...st.cardBtns, gridTemplateColumns: "repeat(6, 1fr)" }}>
          <button onClick={() => { setCurrentSession("saved"); setMessages(item.messages || []); setMenu(false); }}>فتح</button>
          <button onClick={() => renameSession(item.id, source)}>تسمية</button>
          {source !== "sessions" && <button onClick={() => moveSessionBetween(item, source, "sessions")}>جلسات</button>}
          {source !== "saved" && <button onClick={() => moveSessionBetween(item, source, "saved")}>محفوظات</button>}
          {source !== "projects" && <button onClick={() => moveSessionBetween(item, source, "projects")}>مشاريع</button>}
          <button onClick={() => {
            if (source === "sessions") setSessions((list) => list.filter((x) => x.id !== item.id));
            if (source === "saved") setSavedSessions((list) => list.filter((x) => x.id !== item.id));
            if (source === "projects") setProjects((list) => list.filter((x) => x.id !== item.id));
          }}>حذف</button>
        </div>
      </div>
    );
  }

  function renderSessions() {
    return (
      <>
        <button style={st.item} onClick={clearSession}>🗑 مسح الجلسة الحالية</button>
        <button style={st.item} onClick={openMainSession}>🏠 الجلسة الرئيسية</button>
        <button style={st.item} onClick={newSession}>➕ جلسة جديدة</button>
        <button style={st.item} onClick={saveSession}>💾 حفظ الجلسة الحالية</button>

        <h4 style={st.h}>📋 قائمة الجلسات</h4>
        {sessions.length === 0 && <p style={st.note}>لا توجد جلسات محفوظة.</p>}
        {sessions.map((item) => renderSessionCard(item, "sessions"))}

        <h4 style={st.h}>🗂 المحفوظات</h4>
        {savedSessions.length === 0 && <p style={st.note}>لا توجد جلسات في المحفوظات.</p>}
        {savedSessions.map((item) => renderSessionCard(item, "saved"))}

        <h4 style={st.h}>📁 المشاريع</h4>
        {projects.length === 0 && <p style={st.note}>لا توجد مشاريع.</p>}
        {projects.map((item) => renderSessionCard(item, "projects"))}
      </>
    );
  }

  function renderModels() {
    return (
      <>
        <button style={st.item} onClick={() => setShowAddModel(!showAddModel)}>➕ إضافة نموذج</button>

        {showAddModel && (
          <div style={st.form}>
            <input style={st.input} placeholder="اسم النموذج" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <select style={st.input} value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })}>
              <option>API</option>
              <option>Local</option>
              <option>URL</option>
            </select>
            <input style={st.input} placeholder="Model Name" value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} />
            <input style={st.input} placeholder="Base URL" value={form.baseUrl} onChange={(e) => setForm({ ...form, baseUrl: e.target.value })} />
            <input style={st.input} placeholder="API Key اختياري" value={form.apiKey} onChange={(e) => setForm({ ...form, apiKey: e.target.value })} />
            <input style={st.input} placeholder="Path / Local Server اختياري" value={form.path} onChange={(e) => setForm({ ...form, path: e.target.value })} />
            <button style={st.save} onClick={addModel}>حفظ</button>
          </div>
        )}

        <h4 style={st.h}>كل النماذج</h4>

        {models.map((m) => (
          <div style={st.modelRow} key={m.id}>
            <div onClick={() => setExpandedModel(expandedModel === m.id ? null : m.id)} style={{ cursor: "pointer" }}>
              <b>{m.id}. {m.name}</b>
              <small style={{ display: "block", color: "#94a3b8" }}>{m.type} / {m.model}</small>
              <small style={{ display: "block", color: "#94a3b8" }}>
                {m.connected ? "ON" : "OFF"} — اضغط لفتح التفاصيل
              </small>

              {expandedModel === m.id && (
                <div style={st.detailsBox}>
                  <small>الاسم: {m.name || "-"}</small>
                  <small>النوع: {m.type || "-"}</small>
                  <small>الموديل: {m.model || "-"}</small>
                  <small>Base URL: {m.baseUrl || "-"}</small>
                  <small>API Key: {m.apiKey ? "موجود" : "-"}</small>
                  <small>Path: {m.path || "-"}</small>
                  <button style={st.save} onClick={(e) => { e.stopPropagation(); editModel(m.id); }}>
                    تعديل التفاصيل
                  </button>
                </div>
              )}
            </div>

            <div style={st.modelActions}>
              <button style={st.status} onClick={() => updateModel(m.id, { connected: !m.connected })}>
                {m.connected ? "🟢" : "⛔"}
              </button>
              <button style={st.status} onClick={() => moveModel(m.id, "up")}>فوق</button>
              <button style={st.status} onClick={() => moveModel(m.id, "down")}>تحت</button>
              <button style={st.danger} onClick={() => deleteModel(m.id)}>🗑</button>
            </div>
          </div>
        ))}
      </>
    );
  }

  function renameLearnItem(name, id) {
    const title = prompt("اكتب الاسم الجديد:");
    if (!title || !title.trim()) return;

    setLearning((l) => ({
      ...l,
      [name]: l[name].map((x) =>
        x.id === id ? { ...x, title: title.trim() } : x
      )
    }));
  }

  function LearningList({ title, name }) {
    const data = learning[name] || [];
    return (
      <>
        <h4 style={st.h}>{title}</h4>
        {data.length === 0 && <p style={st.note}>فارغ.</p>}
        {data.map((x) => (
          <div style={st.card} key={x.id}>
            <b>{x.title}</b>
            <small style={{ color: "#94a3b8" }}>
              {name === "queue" ? "النوع: جلسة تعلم" : "النوع: مكتملة"}
            </small>
            <small style={{ color: "#94a3b8" }}>{x.date} - {x.pages}</small>

            <div style={{ ...st.cardBtns, gridTemplateColumns: "repeat(5, 1fr)" }}>
              <button onClick={() => { setLearningSession({ ...x, source: name, messages: [...(x.messages || [])] }); setMenu(false); }}>فتح</button>
              <button onClick={() => renameLearnItem(name, x.id)}>تسمية</button>
              {name !== "queue" && <button onClick={() => moveLearn(name, "queue", x.id)}>للتعلم</button>}
              {name !== "done" && <button onClick={() => moveLearn(name, "done", x.id)}>مكتملة</button>}
              <button onClick={() => deleteLearn(name, x.id)}>حذف</button>
            </div>
          </div>
        ))}
      </>
    );
  }

  function renderLearning() {
    const totalPages = Math.max(1, Math.ceil(messages.length / 12));

    return (
      <>
        <h4 style={st.h}>📚 إضافة جلسة للتعلم</h4>
        <div style={st.two}>
          <div style={st.inputWrap}>
            <input
              style={st.inputWithUnit}
              type="number"
              min="1"
              value={learnPages}
              onChange={(e) => setLearnPages(e.target.value)}
            />
            <span style={st.unitLabel}>صفحة</span>
          </div>
          <button style={st.save} onClick={() => makeLearn("session", learnPages || 1)}>إضافة</button>
        </div>
        <button
          style={{ ...st.item, background: "#0f172a", marginTop: 8 }}
          onClick={() => setLearnPages(String(totalPages))}
        >
          اختيار كل الصفحات
        </button>

        {/* قسم الأفكار ملغي نهائياً */}
        <LearningList title="📚 محفوظة للتعلم" name="queue" />
        <LearningList title="✅ جلسات مكتملة" name="done" />
      </>
    );
  }

  async function loadDevList(root = devRoot, path = "") {
    setDevRoot(root);
    setDevPath(path);
    setDevFilePath("");
    setDevContent("");
    setDevStatus("جاري قراءة الملفات...");
    try {
      const res = await fetch(`${API_BASE}/dev/list?root=${encodeURIComponent(root)}&path=${encodeURIComponent(path)}`);
      const data = await res.json();
      setDevItems(data.items || []);
      setDevStatus(data.ok ? "" : (data.error || "فشل قراءة الملفات"));
    } catch {
      setDevStatus("فشل الاتصال ببوابة الملفات");
    }
  }

  async function openDevFile(path) {
    setDevFilePath(path);
    setDevStatus("جاري فتح الملف...");
    try {
      const res = await fetch(`${API_BASE}/dev/read?root=${encodeURIComponent(devRoot)}&path=${encodeURIComponent(path)}`);
      const data = await res.json();
      setDevContent(data.content || "");
      setDevDoor("code");
      setDevStatus(data.ok ? "" : (data.error || "فشل فتح الملف"));
    } catch {
      setDevStatus("فشل الاتصال بمحرر الكود");
    }
  }

  async function saveDevFile() {
    if (!devFilePath) {
      setDevStatus("اختر ملفاً أولاً من مستكشف الملفات.");
      return;
    }
    setDevStatus("جاري الحفظ...");
    try {
      const res = await fetch(`${API_BASE}/dev/write`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ root: devRoot, path: devFilePath, content: devContent })
      });
      const data = await res.json();
      setDevStatus(data.ok ? "تم حفظ الملف." : (data.error || "فشل الحفظ"));
    } catch {
      setDevStatus("فشل الاتصال أثناء الحفظ");
    }
  }

  function parentDevPath(path) {
    if (!path) return "";
    const parts = path.split("/").filter(Boolean);
    parts.pop();
    return parts.join("/");
  }

  function renderCodeDoor() {
    return (
      <section style={st.panel}>
        <button style={st.card} onClick={() => setDevDoor(null)}>← رجوع إلى التطوير</button>
        <h3>💻 محرر الكود</h3>
        <p style={st.note}>{devFilePath ? `الملف: ${devRoot}/${devFilePath}` : "افتح ملفاً من مستكشف الملفات أو الصق كوداً هنا."}</p>
        <textarea
          value={devContent}
          onChange={(e) => setDevContent(e.target.value)}
          style={{ width: "100%", minHeight: 320, borderRadius: 14, padding: 12, background: "#020617", color: "#e5e7eb", border: "1px solid #1f2937", fontFamily: "monospace", direction: "ltr" }}
          placeholder="الكود هنا..."
        />
        <button style={st.card} onClick={saveDevFile}>💾 حفظ الملف</button>
        {devStatus && <p style={st.note}>{devStatus}</p>}
      </section>
    );
  }

  function renderFileDoor() {
    return (
      <section style={st.panel}>
        <button style={st.card} onClick={() => setDevDoor(null)}>← رجوع إلى التطوير</button>
        <h3>📁 مستكشف الملفات</h3>
        <p style={st.note}>🏠 Gerfex System / {devPath || ""}</p>

        <button style={st.card} onClick={() => loadDevList("system", "")}>🏠 Gerfex System</button>
        <button style={st.card} onClick={() => loadDevList("ui", "")}>🤖 GerfexReactUI</button>
        {devPath && <button style={st.card} onClick={() => loadDevList(devRoot, parentDevPath(devPath))}>⬆️ رجوع مجلد</button>}

        <div style={st.list}>
          {devItems.map((x) => (
            <button
              key={x.path}
              style={st.card}
              onClick={() => x.type === "dir" ? loadDevList(devRoot, x.path) : openDevFile(x.path)}
            >
              {x.type === "dir" ? "📁" : "📄"} {x.name}
            </button>
          ))}
        </div>

        {devStatus && <p style={st.note}>{devStatus}</p>}
      </section>
    );
  }

  function renderDev() {
    if (devDoor === "code") return renderCodeDoor();
    if (devDoor === "files") return renderFileDoor();

    return ["💻 محرر الكود", "📁 مستكشف الملفات"].map((x) => (
      <button
        key={x}
        style={st.item}
        onClick={() => {
          if (x.includes("محرر الكود")) setDevDoor("code");
          if (x.includes("مستكشف الملفات")) {
            setDevDoor("files");
            loadDevList("system", "");
          }
        }}
      >
        {x}
      </button>
    ));
  }

  function body() {
    if (section === "sessions") return renderSessions();
    if (section === "models") return renderModels();
    if (section === "learning") return renderLearning();
    return renderDev();
  }

  const activeModels = models.filter((m) => m.connected);

  return (
    <div style={st.app}>
      <header style={st.header}>
        <button style={st.icon} onClick={() => setMenu(!menu)}>☰</button>
        <div style={{ textAlign: "center" }}>
          <div style={st.title}>Gerfex</div>
          <div style={st.ok}>● prototype v1</div>
        </div>
        <button style={st.icon} onClick={() => setQuick(!quick)}>🤖</button>
      </header>

      {menu && (
        <aside style={st.drawer}>
          <div style={st.tabs}>
            {sections.map(([k, i, t]) => (
              <button key={k} style={{ ...st.tab, background: section === k ? "#1e293b" : "transparent" }} onClick={() => setSection(k)}>
                {i} {t}
              </button>
            ))}
          </div>
          <div style={st.drawerBody}>{body()}</div>
        </aside>
      )}

      {quick && (
        <aside style={st.quick}>
          <b>🤖 النماذج النشطة</b>
          {activeModels.length === 0 && <p style={st.note}>لا يوجد نموذج متصل.</p>}
          {activeModels.map((m) => (
            <div style={{ ...st.quickRow, gridTemplateColumns: "1fr 42px 42px" }} key={m.id}>
              <span>
                {m.name}
                <small style={{ display: "block", color: "#94a3b8" }}>
                  {m.mute ? "صامت" : "مسموح بالمراقبة"} / {m.hold ? "معلّق" : "نشط"}
                </small>
              </span>
              <button
                style={{ ...st.symbol, background: m.mute ? "#7f1d1d" : "#1f2937" }}
                onClick={() => updateModel(m.id, { mute: !m.mute })}
              >
                {m.mute ? "🔕" : "🔇"}
              </button>
              <button
                style={{ ...st.symbol, background: m.hold ? "#854d0e" : "#1f2937" }}
                onClick={() => updateModel(m.id, { hold: !m.hold })}
              >
                {m.hold ? "⏸" : "✋"}
              </button>
            </div>
          ))}
        </aside>
      )}

      <main style={st.messages}>
        {(learningSession ? learningSession.messages : messages).map((m, i) => (
          <div style={st.msg} key={i}>
            <b>{m.speaker}</b>
            <div style={st.text}>{m.content}</div>
          </div>
        ))}
        <div ref={bottom} />
      </main>

      <footer style={st.footer}>
        <div style={st.composer}>
          <input
            ref={fileRef}
            type="file"
            style={{ display: "none" }}
            onChange={handleAttach}
          />
          <button style={st.round} type="button" onClick={() => fileRef.current && fileRef.current.click()}>📎</button>
          <button style={{ ...st.round, background: listening ? "#dc2626" : "#202123" }} onClick={startVoice}>
            {listening ? "●" : "🎤"}
          </button>
          <textarea
            ref={textRef}
            rows={1}
            value={input}
            placeholder="اكتب رسالة..."
            style={st.textarea}
            onChange={(e) => { setInput(e.target.value); setVoiceInput(false); }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
          />
          <button style={st.send} onClick={send}>↑</button>
        </div>
      </footer>
    </div>
  );
}

const st = {
  app: { height: "100dvh", background: "#0b0f14", color: "#f8fafc", display: "flex", flexDirection: "column", fontFamily: "system-ui, sans-serif", overflow: "hidden" },
  header: { height: 56, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 12px", borderBottom: "1px solid #1f2937", background: "#0b0f14", flexShrink: 0 },
  icon: { width: 42, height: 42, borderRadius: 12, border: "none", background: "#111827", color: "white", fontSize: 22 },
  title: { fontWeight: 800, fontSize: 18 },
  ok: { color: "#22c55e", fontSize: 11 },
  drawer: { position: "absolute", top: 60, left: 8, right: "auto", width: 335, maxWidth: "94vw", maxHeight: "82dvh", overflowY: "auto", background: "#111827", border: "1px solid #273449", borderRadius: 18, padding: 10, zIndex: 20 },
  tabs: { display: "grid", gridTemplateColumns: "1fr", gap: 8 },
  tab: { color: "white", border: "none", borderRadius: 12, padding: 12, fontSize: 14, textAlign: "left" },
  drawerBody: { marginTop: 10, borderTop: "1px solid #273449", paddingTop: 10 },
  item: { width: "100%", background: "transparent", color: "white", border: "none", borderRadius: 10, padding: 12, textAlign: "right", fontSize: 15 },
  h: { margin: "14px 4px 8px", color: "#cbd5e1" },
  note: { color: "#94a3b8", padding: 8, fontSize: 13 },
  row: { display: "grid", gridTemplateColumns: "1fr 42px", gap: 6, marginBottom: 6 },
  mainBtn: { background: "#0f172a", color: "white", border: "1px solid #263244", borderRadius: 12, padding: 10, textAlign: "right" },
  danger: { background: "#7f1d1d", color: "white", border: "none", borderRadius: 12 },
  form: { display: "grid", gap: 8, background: "#0f172a", borderRadius: 14, padding: 10 },
  input: { background: "#0b0f14", color: "white", border: "1px solid #374151", borderRadius: 12, padding: 10 },
  inputWrap: { display: "grid", gridTemplateColumns: "1fr 52px", alignItems: "center", background: "#0b0f14", border: "1px solid #374151", borderRadius: 12, overflow: "hidden" },
  inputWithUnit: { width: "100%", background: "transparent", color: "white", border: "none", outline: "none", padding: "10px 8px", fontSize: 16 },
  unitLabel: { color: "#94a3b8", fontSize: 14, whiteSpace: "nowrap", textAlign: "center", paddingInlineEnd: 8 },
  unitRow: { display: "grid", gridTemplateColumns: "44px 1fr", alignItems: "center", gap: 8 },
  save: { background: "#2563eb", color: "white", border: "none", borderRadius: 12, padding: "10px 6px", fontSize: 14 },
  modelRow: { display: "grid", gridTemplateColumns: "1fr 112px", gap: 8, background: "#0f172a", border: "1px solid #263244", borderRadius: 14, padding: 10, marginBottom: 8 },
  status: { background: "#1f2937", color: "white", border: "none", borderRadius: 12, fontSize: 13, minHeight: 34 },
  modelActions: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 5 },
  detailsBox: { marginTop: 10, display: "grid", gap: 6, background: "#111827", border: "1px solid #263244", borderRadius: 12, padding: 10, color: "#cbd5e1" },
  two: { display: "grid", gridTemplateColumns: "minmax(0, 1fr) 78px", gap: 8 },
  card: { background: "#0f172a", border: "1px solid #263244", borderRadius: 14, padding: 10, marginBottom: 8, display: "grid", gap: 6 },
  cardBtns: { display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 5 },
  quick: { position: "absolute", top: 60, right: 8, width: 270, maxWidth: "92vw", background: "#111827", border: "1px solid #273449", borderRadius: 18, padding: 12, zIndex: 30 },
  quickRow: { display: "grid", gridTemplateColumns: "1fr 28px 38px 38px", gap: 6, alignItems: "center", padding: "8px 0" },
  symbol: { background: "#1f2937", color: "white", border: "none", borderRadius: 10, height: 34 },
  messages: { flex: 1, overflowY: "auto", padding: "12px 16px 4px", scrollPaddingBottom: 8 },
  msg: { maxWidth: 780, margin: "0 auto 22px", lineHeight: 1.75 },
  text: { whiteSpace: "pre-wrap", fontSize: 16, marginTop: 5 },
  footer: { flexShrink: 0, padding: "8px 10px calc(8px + env(safe-area-inset-bottom))", background: "#0b0f14" },
  composer: { maxWidth: 780, margin: "0 auto", display: "flex", alignItems: "flex-end", gap: 8, background: "#202123", border: "1px solid #374151", borderRadius: 24, padding: 8 },
  round: { width: 38, height: 38, borderRadius: 19, border: "none", background: "#2b2c2f", color: "white", fontSize: 18, flexShrink: 0 },
  textarea: { flex: 1, resize: "none", overflowY: "auto", maxHeight: 150, minHeight: 38, border: "none", outline: "none", background: "transparent", color: "white", fontSize: 16, lineHeight: "24px", padding: "7px 2px", fontFamily: "inherit" },
  send: { width: 38, height: 38, borderRadius: 19, border: "none", background: "#f8fafc", color: "#111827", fontSize: 20, fontWeight: 800, flexShrink: 0 }
};
