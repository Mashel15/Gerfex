import { useEffect, useRef, useState } from "react";
import { registerPlugin } from "@capacitor/core";
import TrackingPage from "./components/TrackingPage";

const GerfexNative = registerPlugin("Gerfex");

function classifyGerfexRoute(prompt = "") {
  const text = String(prompt || "").trim().toLowerCase();

  const pythonCorePatterns = [
    "افتح", "شغل", "سكر", "اقفل", "اضغط", "اسحب", "اكتب",
    "ابحث", "بحث", "افحص", "اقرأ الشاشة", "حالة الإدراك", "حالة الادراك",
    "احفظ", "تذكر", "علّم", "علم", "اعتمد", "لا تعتمد",
    "نفذ", "نفّذ", "مهمة", "ثم", "ارجع", "التنفيذ", "الذاكرة", "تعلم"
  ];

  if (pythonCorePatterns.some((x) => text.includes(x))) {
    return "python_core";
  }

  return "gma_native";
}

async function askGerfexNative(prompt, modelState = {}, routeHint = null) {
  // الشاشة الرئيسية تبدأ دائمًا من Gerfex، وليس من GMA مباشرة.
  const nativeRes = await GerfexNative.think({ message: prompt, model_state: modelState });

  if (!nativeRes || nativeRes.ok === false) {
    return {
      ok: false,
      reply: "خطأ Gerfex Native: " + (nativeRes?.error || "لا يوجد تفاصيل"),
      speaker: "Gerfex",
      replies: [{ speaker: "Gerfex", content: "خطأ Gerfex Native: " + (nativeRes?.error || "لا يوجد تفاصيل") }],
      raw: nativeRes
    };
  }

  const parsed = JSON.parse(nativeRes.result || "{}");
  const external = parsed.external_models || {};
  const advisors = Array.isArray(external.advisors) ? external.advisors : [];

  const providerState = {};
  (modelState.models || []).forEach((m) => {
    providerState[m.name] = {
      mute: !!m.mute,
      hold: !!m.hold,
      connected: !!m.connected
    };
  });

  const visibleExternalReplies = advisors
    .filter((a) => {
      const st = providerState[a.provider] || {};
      return !st.hold && !st.mute;
    })
    .map((a) => ({
      speaker: a.provider || "External AI",
      content: a.reply || a.error || "لا يوجد رد."
    }));

  const replies = [];

  if (modelState.connected && !modelState.hold && !modelState.mute) {
    replies.push({
      speaker: parsed.speaker || "Gerfex",
      content: parsed.reply || parsed.error || "لا يوجد رد."
    });
  }

  replies.push(...visibleExternalReplies);

  if (!modelState.connected || modelState.hold) {
    if (visibleExternalReplies.length === 0 && (parsed.reply || parsed.error)) {
      replies.push({
        speaker: "Gerfex",
        content: parsed.reply || parsed.error || "لا يوجد رد."
      });
    }
  }

  return {
    ok: parsed.ok,
    reply: replies[0]?.content || parsed.reply || parsed.error || "لا يوجد رد.",
    speaker: replies[0]?.speaker || parsed.speaker || "Gerfex",
    replies,
    trace_id: parsed.trace_id || null,
    raw: parsed.raw || parsed
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
  ["models", "📦", "النماذج"],
  ["sessions", "💬", "الجلسات"],
  ["learning", "💡", "الأفكار"],
  ["dev", "⚙️", "التتبع"]
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
  const [input, setInput] = useState("");
  const [typingFocus, setTypingFocus] = useState(false);
  const [viewportHeight, setViewportHeight] = useState(() =>
    Math.round(window.visualViewport?.height || window.innerHeight)
  );
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

  useEffect(() => {
    const viewport = window.visualViewport;

    const updateViewport = () => {
      const nextHeight = Math.round(
        viewport?.height || window.innerHeight
      );

      setViewportHeight(nextHeight);

      window.requestAnimationFrame(() => {
        bottom.current?.scrollIntoView({
          block: "end"
        });
      });
    };

    updateViewport();

    viewport?.addEventListener("resize", updateViewport);
    viewport?.addEventListener("scroll", updateViewport);
    window.addEventListener("resize", updateViewport);

    return () => {
      viewport?.removeEventListener("resize", updateViewport);
      viewport?.removeEventListener("scroll", updateViewport);
      window.removeEventListener("resize", updateViewport);
    };
  }, []);

  useEffect(() => {
    if (!typingFocus) return;

    const timer = window.setTimeout(() => {
      bottom.current?.scrollIntoView({
        behavior: "smooth",
        block: "end"
      });
    }, 120);

    return () => window.clearTimeout(timer);
  }, [typingFocus, learningSession]);

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

        if (!GerfexNative?.gmaNativeChat) {
        throw new Error("gmaNativeChat غير متوفر لصفحة الأفكار");
      }

      const nativeGma = await GerfexNative.gmaNativeChat({
        message: "[IDEAS_SESSION]\\n" + text,
        predictLength: 128
      });

      const data = {
        ok: !!nativeGma?.ok,
        reply: nativeGma?.reply || nativeGma?.error || "لم أستطع توليد رد الآن.",
        speaker: "GMA",
        raw: nativeGma
      };
        const replyText = data.reply || data.raw?.reply || data.raw?.error || "لم أستطع توليد رد الآن.";
        const replyMsg = { speaker: "GMA", content: replyText };

        const finalMessages = [...baseMessages, replyMsg];
        setLearningSession((x) => ({ ...x, messages: finalMessages }));
        persistLearningSessionMessages(learningSession, finalMessages);
      } catch (err) {
        const errorMsg = { speaker: "Gerfex", content: "فشل اتصال صفحة الأفكار بـ GMA: " + (err?.message || err) };
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

    const routeHint = classifyGerfexRoute(text);

    try {
      const data = await askGerfexNative(text, modelState, routeHint);
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


  function addMainSessionToIdeas(amount) {
    const pages = Math.max(1, Number(amount) || 1);
    const messageCount = pages * 12;
    const copiedMessages = messages.slice(-messageCount);

    const item = {
      id: Date.now(),
      title: "فكرة من الجلسة الرئيسية",
      date: new Date().toLocaleString(),
      pages: pages + " صفحة",
      messages: copiedMessages
    };

    setLearning((current) => ({
      ...current,
      queue: [item, ...(current.queue || [])]
    }));
  }

  function createIdeaSession() {
    const item = {
      id: Date.now(),
      title: "جلسة أفكار جديدة",
      date: new Date().toLocaleString(),
      pages: "جلسة جديدة",
      messages: [
        {
          speaker: "GMA",
          content: "جلسة أفكار جديدة. اكتب الموضوع الذي تريد مناقشته."
        }
      ]
    };

    setLearning((current) => ({
      ...current,
      queue: [item, ...(current.queue || [])]
    }));

    setLearningSession({
      ...item,
      source: "queue",
      messages: [...item.messages]
    });

    setMenu(false);
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

  function IdeasList() {
    const data = learning.queue || [];

    return (
      <>
        <h4 style={st.h}>💡 جلسات الأفكار</h4>

        {data.length === 0 && (
          <p style={st.note}>لا توجد جلسات أفكار بعد.</p>
        )}

        {data.map((item) => (
          <div style={st.card} key={item.id}>
            <b>{item.title}</b>

            <small style={{ color: "#94a3b8" }}>
              {item.date} - {item.pages}
            </small>

            <div style={{
              ...st.cardBtns,
              gridTemplateColumns: "repeat(3, 1fr)"
            }}>
              <button
                onClick={() => {
                  setLearningSession({
                    ...item,
                    source: "queue",
                    messages: [...(item.messages || [])]
                  });
                  setMenu(false);
                }}
              >
                فتح
              </button>

              <button onClick={() => renameLearnItem("queue", item.id)}>
                تسمية
              </button>

              <button onClick={() => deleteLearn("queue", item.id)}>
                حذف
              </button>
            </div>
          </div>
        ))}
      </>
    );
  }

  function renderLearning() {
    return (
      <>
        <h4 style={st.h}>💡 إضافة جلسة من الصفحة الرئيسية</h4>

        <div style={st.two}>
          <div style={st.inputWrap}>
            <input
              style={st.inputWithUnit}
              type="number"
              min="1"
              value={learnPages}
              onChange={(event) => setLearnPages(event.target.value)}
            />
            <span style={st.unitLabel}>صفحة</span>
          </div>

          <button
            style={st.save}
            onClick={() => addMainSessionToIdeas(learnPages)}
          >
            إضافة
          </button>
        </div>

        <button
          style={{
            ...st.item,
            background: "#0f172a",
            marginTop: 8
          }}
          onClick={createIdeaSession}
        >
          ➕ إنشاء جلسة جديدة
        </button>

        <IdeasList />
      </>
    );
  }

  function body() {
    if (section === "sessions") return renderSessions();
    if (section === "models") return renderModels();
    if (section === "learning") return renderLearning();
    return <TrackingPage />;
  }

  const activeModels = models.filter((m) => m.connected);

  return (
    <div
      style={{
        ...st.app,
        height: viewportHeight + "px"
      }}
    >
      <header style={st.header}>
        <button style={st.icon} onClick={() => setMenu(!menu)}>☰</button>
        <div style={{ textAlign: "center" }}>
          <div style={st.title}>Gerfex</div>
</div>
        <button
          style={{
            ...st.icon,
            width: 34,
            height: 34,
            borderRadius: 10,
            fontSize: 17
          }}
          onClick={() => setQuick(!quick)}
        >
          📦
        </button>
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
          <b>📦 النماذج النشطة</b>
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

      <main
        style={{
          ...st.messages,
          userSelect: menu ? "none" : "text",
          WebkitUserSelect: menu ? "none" : "text"
        }}
      >
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
  app: { height: "100dvh", width: "100%", maxWidth: "100vw", background: "#0b0f14", color: "#f8fafc", display: "flex", flexDirection: "column", fontFamily: "system-ui, sans-serif", overflow: "hidden", overflowX: "hidden", userSelect: "none", WebkitUserSelect: "none" },
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
  textarea: { flex: 1, resize: "none", overflowY: "auto", maxHeight: 150, minHeight: 38, border: "none", outline: "none", background: "transparent", color: "white", fontSize: 16, lineHeight: "24px", padding: "7px 2px", fontFamily: "inherit", userSelect: "text", WebkitUserSelect: "text" },
  send: { width: 38, height: 38, borderRadius: 19, border: "none", background: "#f8fafc", color: "#111827", fontSize: 20, fontWeight: 800, flexShrink: 0 }
};
