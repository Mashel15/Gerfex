import { useEffect, useRef, useState } from "react";
import { registerPlugin } from "@capacitor/core";

const GerfexNative = registerPlugin("Gerfex");

async function askGerfexNative(prompt, modelState = {}) {
  const nativePromise = GerfexNative?.thinkMain
    ? GerfexNative.thinkMain({ message: prompt, model_state: modelState })
    : GerfexNative.think({ message: prompt, model_state: modelState });

  const nativeRes = await Promise.race([
    nativePromise,
    new Promise((resolve) =>
      setTimeout(() => resolve({
        ok: false,
        error: "GMA_NATIVE_UI_TIMEOUT",
        result: JSON.stringify({
          ok: false,
          reply: "انتهت مهلة انتظار GMA Native قبل رجوع الرد للواجهة.",
          stage: "ui_timeout"
        })
      }), 120000)
    )
  ]);

  if (!nativeRes || nativeRes.ok === false) {
    let fallbackReply = "خطأ Gerfex Native: " + (nativeRes?.error || "لا يوجد تفاصيل");
    try {
      const parsedError = JSON.parse(nativeRes?.result || "{}");
      fallbackReply = parsedError.reply || parsedError.error || fallbackReply;
    } catch {}
    return {
      ok: false,
      reply: fallbackReply,
      speaker: "Gerfex",
      replies: [{ speaker: "Gerfex", content: fallbackReply }],
      raw: nativeRes
    };
  }

  let parsed = {};
  try {
    parsed = JSON.parse(nativeRes.result || "{}");
  } catch (e) {
    parsed = {
      ok: false,
      reply: "فشل تحليل نتيجة Gerfex Native: " + (e?.message || e),
      raw_result: nativeRes.result || ""
    };
  }

  const replyText = parsed.reply || parsed.error || parsed.raw_result || "لا يوجد رد من Gerfex.";

  return {
    ok: parsed.ok !== false,
    reply: replyText,
    speaker: parsed.speaker || "Gerfex",
    replies: [{ speaker: parsed.speaker || "Gerfex", content: replyText }],
    raw: parsed
  };
}


async function getNativePerceptionStatus() {
  const nativeRes = await GerfexNative.accessibilityStatus();
  const text = nativeRes?.screen_text || "";
  const preview = text.split("\n").filter(Boolean).slice(0, 8).join("\n");

  return {
    ok: !!nativeRes?.ok,
    ready: !!nativeRes?.ready,
    length: text.length,
    savedPath: nativeRes?.screen_text_saved_path || "",
    preview
  };
}

const sections = [
  ["models", "🤖", "النماذج"],
  ["sessions", "💬", "الجلسات"],
  ["learning", "🧠", "التعليم"],
  ["dev", "⚙️", "التطوير"]
];

const defaultModels = [
  { id: 1, name: "GMA", type: "Local", model: "gma-core", connected: false, mute: false, hold: false },
  { id: 2, name: "ChatGPT", type: "API", model: "gpt", connected: false, mute: false, hold: false },
  { id: 3, name: "DeepSeek", type: "API/Local", model: "deepseek", connected: false, mute: false, hold: false }
];

function buildExternalModelsRegistry(models) {
  const external = (models || []).filter((m) => m.name !== "GMA");

  return {
    version: "EXTERNAL_MODELS_REGISTRY_V1",
    mode: "advisor_only",
    active: external
      .filter((m) => !!m.connected && !m.hold)
      .map((m) => m.name),
    providers: external.map((m) => ({
      id: m.id,
      name: m.name,
      type: "openai_compatible",
      ui_type: m.type || "",
      model: m.model || "",
      base_url: m.baseUrl || "",
      api_key: m.apiKey || "",
      path: m.path || "",
      connected: !!m.connected,
      mute: !!m.mute,
      hold: !!m.hold
    }))
  };
}

async function syncExternalModelsToNative(models) {
  try {
    if (!GerfexNative?.saveExternalModels) return false;
    const registry = buildExternalModelsRegistry(models);
    const res = await GerfexNative.saveExternalModels({ registry: JSON.stringify(registry) });
    return !!res?.ok;
  } catch (err) {
    console.log("syncExternalModelsToNative failed", err);
    return false;
  }
}


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
  const [typingFocus, setTypingFocus] = useState(false);
  const [listening, setListening] = useState(false);
  const [voiceInput, setVoiceInput] = useState(false);

  const [messages, setMessages] = useState(() =>
    load("g_messages", load("g_main_session", [{ speaker: "Gerfex", content: "النظام جاهز." }]))
  );
  const [currentSession, setCurrentSession] = useState(() => load("g_current_session", "main"));

  const [models, setModels] = useState(() => load("g_models_internal_v1", defaultModels));
  const [modelTestStatus, setModelTestStatus] = useState({});
  const [sessions, setSessions] = useState(() => load("g_sessions", []));
  const [savedSessions, setSavedSessions] = useState(() => load("g_saved_sessions", []));
  const [projects, setProjects] = useState(() => load("g_projects", []));
  const [learning, setLearning] = useState(() =>
    load("g_learning", { queue: [], done: [] })
  );
  const [nativeLearning, setNativeLearning] = useState(null);
  const [nativeLearningStatus, setNativeLearningStatus] = useState("");
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
  useEffect(() => {
    localStorage.setItem("g_models_internal_v1", JSON.stringify(models));
    syncExternalModelsToNative(models);
  }, [models]);
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

  async function startVoice() {
    try {
      setListening(true);

      if (!GerfexNative?.startSpeech) {
        setListening(false);
        return addReply("الصوت غير مربوط Native داخل التطبيق.");
      }

      const res = await GerfexNative.startSpeech();
      const t = (res?.text || "").trim();

      if (t) {
        setInput(t);
        setVoiceInput(true);
      } else {
        addReply("لم ألتقط صوت واضح.");
      }
    } catch (e) {
      addReply("خطأ في الصوت: " + (e?.message || e || "unknown"));
    } finally {
      setListening(false);
    }
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

    if (learningSession) {
      const userMsg = { speaker: "Mashel", content: text };
      const baseMessages = [...(learningSession?.messages || []), userMsg];

      setLearningSession((x) => ({ ...x, messages: baseMessages }));
      persistLearningSessionMessages(learningSession, baseMessages);
      setInput("");
      setVoiceInput(false);

      try {
        const gmaState = {
          name: "GMA",
          connected: true,
          mute: false,
          hold: false,
          learning_session: true,
          models: models
        };

        const data = GerfexNative?.thinkLearning
          ? await GerfexNative.thinkLearning({ message: text, learning_state: gmaState })
          : await askGerfexNative("[LEARNING_SESSION]\\n" + text, gmaState);

        const parsedLearning = data?.result ? JSON.parse(data.result || "{}") : data;
        const replyText = parsedLearning?.reply || parsedLearning?.raw?.reply || parsedLearning?.raw?.error || "لم أستطع توليد رد تعلّم الآن.";
        const replyMsg = { speaker: "GMA", content: replyText };

        const finalMessages = [...baseMessages, replyMsg];
        setLearningSession((x) => ({ ...x, messages: finalMessages }));
        persistLearningSessionMessages(learningSession, finalMessages);
      } catch (err) {
        const errorMsg = { speaker: "Gerfex", content: "فشل اتصال صفحة التعلم بـ GMA: " + (err?.message || err) };
        const finalMessages = [...baseMessages, errorMsg];
        setLearningSession((x) => ({ ...x, messages: finalMessages }));
        persistLearningSessionMessages(learningSession, finalMessages);
      }

      setTimeout(() => bottom.current?.scrollIntoView({ behavior: "smooth" }), 50);
      return;
    }

    const shouldSpeak = voiceInput;

    const gmaModel = models.find((m) => m.name === "GMA") || {};
    const modelState = {
      name: "GMA",
      connected: !!gmaModel.connected && !gmaModel.hold && !gmaModel.mute,
      mute: !!gmaModel.mute,
      hold: !!gmaModel.hold,
      models: models
    };

    if (text === "حالة الإدراك" || text === "حالة الادراك") {
      setMessages((m) => [...m, { speaker: "Mashel", content: text }]);
      setInput("");
      setVoiceInput(false);

      try {
        const st = await getNativePerceptionStatus();
        addReply(
          `Native Perception\nready: ${st.ready}\ntext_length: ${st.length}\nsaved_path: ${st.savedPath || "none"}\n---\n${st.preview || "لا يوجد نص شاشة بعد."}`
        );
      } catch (err) {
        addReply("فشل فحص الإدراك: " + (err?.message || err));
      }
      return;
    }

    setMessages((m) => [...m, { speaker: "Mashel", content: text }]);
    setInput("");
    setVoiceInput(false);

    try {
      const data = await askGerfexNative(text, modelState);
      const replies = Array.isArray(data.replies) ? data.replies : [];

      replies.forEach((r, idx) => {
        addReply(r.content || "لا يوجد رد.", r.speaker || "Gerfex", shouldSpeak && idx === 0);
      });
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

    if (model.name === "GMA") {
      const answer = prompt("GMA هو العقل الأساسي. اكتب DELETE QUEEN للتأكيد:");
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


  async function testModelConnection(m) {
    if (!m || !m.name) return;

    setModelTestStatus((x) => ({
      ...x,
      [m.id]: { status: "testing", text: "⏳ جاري اختبار الاتصال..." }
    }));

    try {
      await syncExternalModelsToNative(models);

      if (!GerfexNative?.testExternalModel) {
        setModelTestStatus((x) => ({
          ...x,
          [m.id]: { status: "error", text: "🔴 دالة اختبار الاتصال غير موجودة في Native." }
        }));
        return;
      }

      const res = await GerfexNative.testExternalModel({ name: m.name });
      const data = JSON.parse(res.result || "{}");
      const ok = !!data.ok;

      const javaDebug = {
        registry_exists: res.registry_exists,
        registry_length: res.registry_length,
        registry_path: res.registry_path,
        result: data
      };

      const debugText = JSON.stringify({
        native_response: res,
        parsed_result: data
      }, null, 2);

      const rawReply = data.reply || data.raw?.reply || data.raw?.error || data.error || debugText;
      const reason = rawReply ? " — " + String(rawReply).slice(0, 2500) : "";

      setModelTestStatus((x) => ({
        ...x,
        [m.id]: {
          status: ok ? "ok" : "error",
          text: (ok ? "🟢 متصل فعلياً" : "🔴 فشل الاتصال") + reason
        }
      }));
    } catch (err) {
      setModelTestStatus((x) => ({
        ...x,
        [m.id]: { status: "error", text: "🔴 خطأ الاختبار: " + (err?.message || err) }
      }));
    }
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
                <div style={st.detailsBox} onClick={(e) => e.stopPropagation()}>
                  <input style={st.input} placeholder="اسم النموذج" value={m.name || ""} onChange={(e) => updateModel(m.id, { name: e.target.value })} />
                  <select style={st.input} value={m.type || "API"} onChange={(e) => updateModel(m.id, { type: e.target.value })}>
                    <option>API</option>
                    <option>Local</option>
                    <option>URL</option>
                  </select>
                  <input style={st.input} placeholder="Model Name" value={m.model || ""} onChange={(e) => updateModel(m.id, { model: e.target.value })} />
                  <input style={st.input} placeholder="Base URL" value={m.baseUrl || ""} onChange={(e) => updateModel(m.id, { baseUrl: e.target.value })} />
                  <input style={st.input} placeholder="API Key اختياري" value={m.apiKey || ""} onChange={(e) => updateModel(m.id, { apiKey: e.target.value })} />
                  <input style={st.input} placeholder="Path / Local Server اختياري" value={m.path || ""} onChange={(e) => updateModel(m.id, { path: e.target.value })} />
                  <button style={st.save} onClick={async () => {
                    const ok = await syncExternalModelsToNative(models);
                    alert(ok ? "تم حفظ بيانات النماذج" : "فشل حفظ بيانات النماذج");
                    if (ok) setExpandedModel(null);
                  }}>
                    حفظ البيانات
                  </button>
                  {m.name !== "GMA" && (
                    <>
                      <button style={st.save} onClick={() => testModelConnection(m)}>
                        اختبار الاتصال
                      </button>
                      <small style={{ color: "#cbd5e1" }}>
                        الحالة: {(modelTestStatus[m.id] && modelTestStatus[m.id].text) || "لم يتم اختبار الاتصال"}
                      </small>
                    </>
                  )}
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

  async function refreshNativeLearning() {
    try {
      setNativeLearningStatus("جاري تحديث تعلم Gerfex الداخلي...");
      if (!GerfexNative?.learningStatus) {
        setNativeLearningStatus("دالة learningStatus غير موجودة في Native.");
        return;
      }

      const res = await GerfexNative.learningStatus();
      const data = JSON.parse(res.result || "{}");
      setNativeLearning(data);
      setNativeLearningStatus(data.ok ? "تم تحديث حالة التعلم الداخلي." : ("فشل التحديث: " + (data.error || "unknown")));
    } catch (err) {
      setNativeLearningStatus("خطأ في تحديث التعلم الداخلي: " + (err?.message || err));
    }
  }

  async function approveNativeLesson() {
    try {
      setNativeLearningStatus("جاري اعتماد آخر درس...");
      const res = await GerfexNative.approveLatestLesson();
      const data = JSON.parse(res.result || "{}");
      setNativeLearningStatus(data.ok ? "تم اعتماد آخر درس." : ("لم يتم الاعتماد: " + (data.reason || data.error || "unknown")));
      await refreshNativeLearning();
    } catch (err) {
      setNativeLearningStatus("خطأ اعتماد الدرس: " + (err?.message || err));
    }
  }

  async function approveNativeImprovement() {
    try {
      setNativeLearningStatus("جاري اعتماد آخر تطوير...");
      const res = await GerfexNative.approveLatestImprovement();
      const data = JSON.parse(res.result || "{}");
      setNativeLearningStatus(data.ok ? "تم اعتماد آخر تطوير." : ("لم يتم الاعتماد: " + (data.reason || data.error || "unknown")));
      await refreshNativeLearning();
    } catch (err) {
      setNativeLearningStatus("خطأ اعتماد التطوير: " + (err?.message || err));
    }
  }

  function NativeLearningList({ title, items }) {
    const data = Array.isArray(items) ? items : [];
    return (
      <>
        <h4 style={st.h}>{title} ({data.length})</h4>
        {data.length === 0 && <p style={st.note}>فارغ.</p>}
        {data.map((x) => (
          <div style={st.card} key={x.id || x.text}>
            <b>{x.kind || "item"}</b>
            <small style={{ color: "#cbd5e1" }}>{x.status || ""}</small>
            <p style={{ margin: "6px 0 0", whiteSpace: "pre-wrap" }}>{x.text || JSON.stringify(x)}</p>
          </div>
        ))}
      </>
    );
  }

  function renderLearning() {
    const totalPages = Math.max(1, Math.ceil(messages.length / 12));

    return (
      <>
        <h4 style={st.h}>🧠 تعلم Gerfex الداخلي</h4>

        <div style={st.two}>
          <button style={st.save} onClick={refreshNativeLearning}>تحديث حالة التعلم</button>
          <button style={st.save} onClick={approveNativeLesson}>اعتماد آخر درس</button>
        </div>

        <button style={{ ...st.item, background: "#0f172a", marginTop: 8 }} onClick={approveNativeImprovement}>
          اعتماد آخر تطوير
        </button>

        {nativeLearningStatus && <p style={st.note}>{nativeLearningStatus}</p>}

        {nativeLearning && (
          <>
            <NativeLearningList title="⏳ الدروس المعلقة" items={nativeLearning.pending_lessons} />
            <NativeLearningList title="⏳ التطويرات المعلقة" items={nativeLearning.pending_improvements} />
            <NativeLearningList title="✅ المعرفة المعتمدة" items={nativeLearning.approved_knowledge} />
            <NativeLearningList title="✅ التطويرات المعتمدة" items={nativeLearning.approved_improvements} />
          </>
        )}

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

  async function showExecutionTrace() {
    try {
      const nativeRes = await GerfexNative.readExecutionTrace();
      const lines = (nativeRes?.content || "").split("\n").filter(Boolean).slice(-10);

      const pretty = lines.map((line, i) => {
        try {
          const o = JSON.parse(line);
          const stages = Array.isArray(o.stages) ? o.stages : [];
          const route = [...stages].reverse().find(x => x.stage === "brain_router")?.route || "-";
          const decision = [...stages].reverse().find(x => x.stage === "provider_response") || {};
          const execution = [...stages].reverse().find(x =>
            x.stage === "execution_observed" ||
            x.stage === "execution_manager_end" ||
            x.stage === "execution_manager_stop"
          ) || {};

          const ok = (execution.execution_ok ?? execution.ok) ? "نجح" : "فشل";

          return `${i + 1}) ${o.goal || "-"}\nالمسار: ${route}\nالقرار: ${decision.intent || "-"} / ${decision.target || "-"}\nالتنفيذ: ${ok}\nالسبب: ${decision.reason || execution.reason || "-"}`;
        } catch {
          return `${i + 1}) ${line}`;
        }
      }).join("\n\n");

      setDevStatus(pretty || "لا يوجد تتبع بعد.");
    } catch (err) {
      setDevStatus("فشل عرض التتبع: " + (err?.message || err));
    }
  }

  async function showExecutionPath() {
    try {
      const nativeRes = await GerfexNative.readExecutionPath();
      const lines = (nativeRes?.content || "").split("\n").filter(Boolean).slice(-10);

      const pretty = lines.map((line, i) => {
        try {
          const o = JSON.parse(line);
          const path = Array.isArray(o.path) ? o.path : [];

          return `${i + 1}) ${o.goal || "-"}\nالمسار: ${o.route || "-"}\nالقرار: ${(o.decision?.intent || "-")} / ${(o.decision?.target || "-")}\nالتنفيذ: ${o.execution?.ok ? "نجح" : "فشل"}\n\nخط السير:\n- ${path.join("\n- ")}`;
        } catch {
          return `${i + 1}) ${line}`;
        }
      }).join("\n\n");

      setDevStatus(pretty || "لا يوجد خط سير بعد.");
    } catch (err) {
      setDevStatus("فشل عرض خط السير: " + (err?.message || err));
    }
  }

  function renderDev() {
    return (
      <section style={st.panel}>
        <h3>🧾 تتبع تنفيذ Gerfex</h3>
        <p style={st.note}>يعرض آخر 10 أوامر فقط من ملف التتبع الداخلي.</p>

        <button style={st.item} onClick={showExecutionTrace}>
          🧾 عرض آخر 10 أوامر
        </button>

        <button style={st.item} onClick={showExecutionPath}>
          🛣️ عرض خط السير
        </button>

        {devStatus && (
          <pre style={{
            whiteSpace: "pre-wrap",
            background: "#020617",
            color: "#e5e7eb",
            border: "1px solid #1f2937",
            borderRadius: 14,
            padding: 12,
            maxHeight: 420,
            overflow: "auto",
            direction: "rtl"
          }}>
            {devStatus}
          </pre>
        )}
      </section>
    );
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
            onFocus={() => setTypingFocus(true)}
            onBlur={() => setTypingFocus(false)}
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
  footer: { flexShrink: 0, padding: "2px 2px calc(2px + env(safe-area-inset-bottom))", background: "#0b0f14" },
  composer: { width: "100%", maxWidth: "100%", margin: 0, display: "flex", alignItems: "center", gap: 8, background: "#202123", border: "1px solid #374151", borderRadius: 18, padding: "4px 8px" },
  round: { width: 38, height: 38, borderRadius: 19, border: "none", background: "#2b2c2f", color: "white", fontSize: 18, flexShrink: 0 },
  textarea: { flex: 1, resize: "none", overflowY: "auto", maxHeight: 150, minHeight: 38, border: "none", outline: "none", background: "transparent", color: "white", fontSize: 16, lineHeight: "24px", padding: "7px 2px", fontFamily: "inherit" },
  send: { width: 38, height: 38, borderRadius: 19, border: "none", background: "#f8fafc", color: "#111827", fontSize: 20, fontWeight: 800, flexShrink: 0 }
};
