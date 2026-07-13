import { useState } from "react";
import { registerPlugin } from "@capacitor/core";

const GerfexNative = registerPlugin("Gerfex");

function lastJsonLines(content, count = 10) {
  return String(content || "")
    .split("\n")
    .filter(Boolean)
    .slice(-count);
}

function formatCommands(content) {
  const lines = lastJsonLines(content, 10);

  return lines.map((line, index) => {
    try {
      const item = JSON.parse(line);
      const stages = Array.isArray(item.stages) ? item.stages : [];

      const route =
        [...stages].reverse().find(
          (stage) => stage.stage === "brain_router"
        )?.route || "-";

      const decision =
        [...stages].reverse().find(
          (stage) => stage.stage === "provider_response"
        ) || {};

      const execution =
        [...stages].reverse().find((stage) =>
          [
            "execution_observed",
            "execution_manager_end",
            "execution_manager_stop",
            "plugin_execute_end"
          ].includes(stage.stage)
        ) || {};

      const executionValue =
        execution.execution_ok ?? execution.ok;

      const result =
        executionValue === true
          ? "نجح"
          : executionValue === false
            ? "فشل"
            : "-";

      return [
        `${index + 1}) ${item.goal || "-"}`,
        `المسار: ${route}`,
        `القرار: ${decision.intent || "-"} / ${decision.target || "-"}`,
        `التنفيذ: ${result}`,
        `السبب: ${decision.reason || execution.reason || "-"}`
      ].join("\n");
    } catch {
      return `${index + 1}) ${line}`;
    }
  }).join("\n\n");
}

function formatPaths(content) {
  const lines = lastJsonLines(content, 10);

  return lines.map((line, index) => {
    try {
      const item = JSON.parse(line);
      const path = Array.isArray(item.path) ? item.path : [];

      return [
        `${index + 1}) ${item.goal || "-"}`,
        `المسار: ${item.route || "-"}`,
        `القرار: ${item.decision?.intent || "-"} / ${item.decision?.target || "-"}`,
        `التنفيذ: ${item.execution?.ok ? "نجح" : "فشل"}`,
        "",
        "خط السير:",
        path.length > 0
          ? `- ${path.join("\n- ")}`
          : "- لا توجد مراحل مسجلة."
      ].join("\n");
    } catch {
      return `${index + 1}) ${line}`;
    }
  }).join("\n\n");
}

function parseJavaDiagnostic(line) {
  const match = String(line || "").match(
    /^(\d+)\s+trace_id=(\S+)\s+layer=(\S+)\s+stage=(\S+)\s+detail=(.*)$/
  );

  if (!match) return null;

  return {
    timestamp: Number(match[1]) || 0,
    trace_id: match[2],
    layer: match[3],
    stage: match[4],
    status: match[4].includes("exception") ? "error" : "ok",
    detail: match[5] || ""
  };
}

function formatDiagnostics(gdfContent, javaContent) {
  const cases = new Map();

  String(gdfContent || "")
    .split("\n")
    .filter(Boolean)
    .forEach((line) => {
      try {
        const event = JSON.parse(line);
        const traceId = String(event.trace_id || "").trim();

        if (!traceId) return;

        cases.set(traceId, {
          timestamp: event.timestamp || event.time || "",
          trace_id: traceId,
          layer: event.layer || "-",
          stage: event.stage || "-",
          status: event.status || "-",
          detail:
            event.error_code ||
            event.details?.reason ||
            event.details?.action ||
            event.details?.mode ||
            ""
        });
      } catch {
        // تجاهل الأسطر غير الصالحة فقط.
      }
    });

  String(javaContent || "")
    .split("\n")
    .filter(Boolean)
    .forEach((line) => {
      const event = parseJavaDiagnostic(line);
      if (!event || !event.trace_id) return;

      const previous = cases.get(event.trace_id) || {};

      cases.set(event.trace_id, {
        ...previous,
        ...event,
        detail: event.detail || previous.detail || ""
      });
    });

  const items = Array.from(cases.values())
    .slice(-10)
    .reverse();

  if (items.length === 0) {
    return "لا توجد حالات تشخيص مسجلة بعد.";
  }

  return items.map((item, index) => {
    const status =
      item.status === "error"
        ? "خطأ"
        : item.status === "timeout"
          ? "توقف"
          : item.status === "ok"
            ? "ناجح"
            : item.status || "-";

    return [
      `${index + 1}) trace_id: ${item.trace_id || "-"}`,
      `الطبقة: ${item.layer || "-"}`,
      `المرحلة: ${item.stage || "-"}`,
      `الحالة: ${status}`,
      `التفصيل: ${item.detail || "-"}`
    ].join("\n");
  }).join("\n\n");
}

export default function TrackingPage() {
  const [content, setContent] = useState("");

  async function showCommands() {
    try {
      const result = await GerfexNative.readExecutionTrace();
      setContent(
        formatCommands(result?.content) ||
        "لا توجد أوامر مسجلة بعد."
      );
    } catch (error) {
      setContent(
        "فشل عرض الأوامر: " +
        (error?.message || error)
      );
    }
  }

  async function showPath() {
    try {
      const result = await GerfexNative.readExecutionPath();
      setContent(
        formatPaths(result?.content) ||
        "لا توجد مسارات مسجلة بعد."
      );
    } catch (error) {
      setContent(
        "فشل عرض المسار: " +
        (error?.message || error)
      );
    }
  }

  async function showDiagnostics() {
    try {
      const result = await GerfexNative.readDiagnostics();

      setContent(
        formatDiagnostics(
          result?.gdf_events,
          result?.java_diagnostics
        )
      );
    } catch (error) {
      setContent(
        "فشل عرض التشخيص: " +
        (error?.message || error)
      );
    }
  }

  return (
    <section style={styles.panel}>
      <p style={styles.note}>
        يعرض آخر 10 حالات من نظام التتبع الداخلي.
      </p>

      <button style={styles.item} onClick={showCommands}>
        📜 الأوامر
      </button>

      <button style={styles.item} onClick={showPath}>
        🛣️ المسار
      </button>

      <button style={styles.item} onClick={showDiagnostics}>
        🩺 التشخيص
      </button>

      {content && (
        <pre style={styles.output}>
          {content}
        </pre>
      )}
    </section>
  );
}

const styles = {
  panel: {
    display: "grid",
    gap: 4
  },
  note: {
    color: "#94a3b8",
    padding: 8,
    fontSize: 13,
    margin: 0
  },
  item: {
    width: "100%",
    background: "transparent",
    color: "white",
    border: "none",
    borderRadius: 10,
    padding: 12,
    textAlign: "right",
    fontSize: 15
  },
  output: {
    whiteSpace: "pre-wrap",
    background: "#020617",
    color: "#e5e7eb",
    border: "1px solid #1f2937",
    borderRadius: 14,
    padding: 12,
    maxHeight: 420,
    overflow: "auto",
    direction: "rtl"
  }
};
