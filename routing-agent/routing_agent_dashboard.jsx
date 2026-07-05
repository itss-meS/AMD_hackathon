import { useState, useEffect, useRef } from "react";

const SAMPLE_TASKS = [
  "What is the capital of France?",
  "Write a Python function to check if a number is prime.",
  "Explain the difference between TCP and UDP.",
  "What is 17 multiplied by 43?",
  "Summarize what machine learning is in one sentence.",
  "List 5 renewable energy sources.",
  "Why does the sky appear blue?",
  "Convert 100 Fahrenheit to Celsius.",
  "What are pros and cons of microservices?",
  "Write a SQL query to find duplicate emails in a users table.",
];

function classifyTask(task) {
  const t = task.toLowerCase();
  if (/def |class |import |function|code|debug|python|sql|algorithm|implement/.test(t)) return "code";
  if (/\d+[\+\-\*\/]\d+|calculate|solve|equation|convert|multiplied|fahrenheit/.test(t)) return "math";
  if (/why|explain|reason|compare|analyze|evaluate|difference between/.test(t)) return "reasoning";
  if (/write a|story|poem|essay|creative|summarize/.test(t)) return "creative";
  if (/^(what is|who is|when|where|which|list|name|define)/.test(t.trim())) return "simple_qa";
  return "extraction";
}

function getDifficulty(task) {
  const t = task.toLowerCase();
  let d = 0;
  if (/code|function|algorithm|implement/.test(t)) d += 3;
  if (/calculate|equation|formula/.test(t)) d += 2;
  if (/explain|analyze|compare/.test(t)) d += 2;
  if (/step by step|comprehensive|multiple/.test(t)) d += 1;
  if (task.split(" ").length > 15) d += 1;
  if (/^(what is|list|name|when|where)/.test(t.trim())) d -= 2;
  return Math.max(0, Math.min(10, d));
}

function routeTask(task, threshold = 0.85) {
  const type = classifyTask(task);
  const difficulty = getDifficulty(task);
  const localAcc = { simple_qa: 0.93, extraction: 0.88, math: 0.62, code: 0.58, reasoning: 0.68, creative: 0.75 };
  const mediumAcc = { simple_qa: 0.97, extraction: 0.94, math: 0.84, code: 0.82, reasoning: 0.87, creative: 0.88 };
  const la = localAcc[type] || 0.70;
  const ma = mediumAcc[type] || 0.88;
  if (difficulty >= 7) return { route: "remote_large", taskType: type, difficulty, localAcc: la, mediumAcc: ma };
  if (la >= threshold) return { route: "local", taskType: type, difficulty, localAcc: la, mediumAcc: ma };
  if (ma >= threshold) return { route: "remote_medium", taskType: type, difficulty, localAcc: la, mediumAcc: ma };
  return { route: "remote_large", taskType: type, difficulty, localAcc: la, mediumAcc: ma };
}

function estimateTokens(text) { return Math.max(1, Math.round(text.split(" ").length / 0.75)); }

const ROUTE_COLOR = {
  local: "#1D9E75",
  remote_medium: "#378ADD",
  remote_large: "#D85A30",
};
const ROUTE_LABEL = { local: "Local (LM Studio)", remote_medium: "Fireworks Medium", remote_large: "Fireworks Large" };
const ROUTE_COST = { local: 0, remote_medium: 0.0002, remote_large: 0.0009 };

function Badge({ route }) {
  const colors = { local: "#E1F5EE", remote_medium: "#E6F1FB", remote_large: "#FAECE7" };
  const textColors = { local: "#0F6E56", remote_medium: "#185FA5", remote_large: "#993C1D" };
  return (
    <span style={{ background: colors[route], color: textColors[route], fontSize: 11, fontWeight: 500, padding: "2px 8px", borderRadius: 6, whiteSpace: "nowrap" }}>
      {route === "local" ? "🖥 Local" : route === "remote_medium" ? "☁ Medium" : "☁ Large"}
    </span>
  );
}

function StatCard({ label, value, sub }) {
  return (
    <div style={{ background: "var(--color-background-secondary)", borderRadius: 8, padding: "12px 16px" }}>
      <div style={{ fontSize: 12, color: "var(--color-text-secondary)", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 500, color: "var(--color-text-primary)" }}>{value}</div>
      {sub && <div style={{ fontSize: 11, color: "var(--color-text-secondary)", marginTop: 2 }}>{sub}</div>}
    </div>
  );
}

function MiniBar({ value, max, color }) {
  return (
    <div style={{ height: 6, background: "var(--color-background-secondary)", borderRadius: 3, overflow: "hidden", flex: 1 }}>
      <div style={{ height: "100%", width: `${Math.round((value / max) * 100)}%`, background: color, borderRadius: 3, transition: "width 0.4s" }} />
    </div>
  );
}

export default function App() {
  const [tasks, setTasks] = useState(SAMPLE_TASKS.map((t, i) => {
    const r = routeTask(t);
    const tokens = estimateTokens(t) + Math.floor(Math.random() * 60) + 30;
    const cost = +(tokens / 1000 * ROUTE_COST[r.route]).toFixed(6);
    return { id: i + 1, task: t, ...r, tokens, cost, status: "done" };
  }));
  const [threshold, setThreshold] = useState(0.85);
  const [customTask, setCustomTask] = useState("");
  const [activeTab, setActiveTab] = useState("tasks");
  const [animatedIdx, setAnimatedIdx] = useState(null);

  const routeCounts = tasks.reduce((a, t) => { a[t.route] = (a[t.route] || 0) + 1; return a; }, {});
  const totalTokens = tasks.reduce((s, t) => s + t.tokens, 0);
  const totalCost = tasks.reduce((s, t) => s + t.cost, 0);
  const localPct = Math.round(((routeCounts.local || 0) / tasks.length) * 100);

  function recalcRoutes(newThreshold) {
    setThreshold(newThreshold);
    setTasks(prev => prev.map(t => {
      const r = routeTask(t.task, newThreshold);
      const cost = +(t.tokens / 1000 * ROUTE_COST[r.route]).toFixed(6);
      return { ...t, ...r, cost };
    }));
  }

  function addTask() {
    if (!customTask.trim()) return;
    const r = routeTask(customTask, threshold);
    const tokens = estimateTokens(customTask) + Math.floor(Math.random() * 40) + 20;
    const cost = +(tokens / 1000 * ROUTE_COST[r.route]).toFixed(6);
    const newTask = { id: tasks.length + 1, task: customTask, ...r, tokens, cost, status: "done" };
    setAnimatedIdx(tasks.length);
    setTasks(prev => [...prev, newTask]);
    setCustomTask("");
    setTimeout(() => setAnimatedIdx(null), 800);
  }

  const typeBreakdown = tasks.reduce((a, t) => { a[t.taskType] = (a[t.taskType] || 0) + 1; return a; }, {});
  const maxType = Math.max(...Object.values(typeBreakdown));

  const TYPE_COLORS = { simple_qa: "#1D9E75", extraction: "#378ADD", math: "#D85A30", code: "#534AB7", reasoning: "#BA7517", creative: "#D4537E" };

  return (
    <div style={{ fontFamily: "var(--font-sans)", color: "var(--color-text-primary)", maxWidth: 700, margin: "0 auto", padding: "1.5rem 0" }}>
      <h2 style={{ fontSize: 18, fontWeight: 500, margin: "0 0 4px" }}>Hybrid routing agent</h2>
      <p style={{ fontSize: 13, color: "var(--color-text-secondary)", margin: "0 0 20px" }}>
        Routes tasks between LM Studio (local, free) and Fireworks AI (remote) to minimize cost while staying above accuracy threshold.
      </p>

      {/* Stats */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginBottom: 20 }}>
        <StatCard label="Total tasks" value={tasks.length} />
        <StatCard label="Total tokens" value={totalTokens.toLocaleString()} sub={`avg ${Math.round(totalTokens / tasks.length)}/task`} />
        <StatCard label="Total cost" value={`$${totalCost.toFixed(4)}`} sub="Fireworks only" />
        <StatCard label="Local rate" value={`${localPct}%`} sub="free inference" />
      </div>

      {/* Threshold slider */}
      <div style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: 10, padding: "14px 16px", marginBottom: 16 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 10 }}>
          <span style={{ fontSize: 13, fontWeight: 500 }}>Accuracy threshold</span>
          <span style={{ fontSize: 13, fontWeight: 500, color: "#378ADD" }}>{(threshold * 100).toFixed(0)}%</span>
        </div>
        <input type="range" min="60" max="99" value={Math.round(threshold * 100)} step="1"
          onChange={e => recalcRoutes(parseInt(e.target.value) / 100)} style={{ width: "100%" }} />
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "var(--color-text-secondary)", marginTop: 4 }}>
          <span>60% — more local</span>
          <span>99% — more remote</span>
        </div>
      </div>

      {/* Route distribution */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10, marginBottom: 16 }}>
        {["local", "remote_medium", "remote_large"].map(r => (
          <div key={r} style={{ background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)", borderRadius: 10, padding: "12px 14px" }}>
            <div style={{ fontSize: 11, color: "var(--color-text-secondary)", marginBottom: 6 }}>{ROUTE_LABEL[r]}</div>
            <div style={{ fontSize: 20, fontWeight: 500, color: ROUTE_COLOR[r], marginBottom: 4 }}>{routeCounts[r] || 0}</div>
            <MiniBar value={routeCounts[r] || 0} max={tasks.length} color={ROUTE_COLOR[r]} />
            <div style={{ fontSize: 11, color: "var(--color-text-secondary)", marginTop: 4 }}>
              {r === "local" ? "free" : `$${ROUTE_COST[r]}/1K tokens`}
            </div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 4, marginBottom: 12, borderBottom: "0.5px solid var(--color-border-tertiary)", paddingBottom: 0 }}>
        {["tasks", "types"].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} style={{
            background: "none", border: "none", borderBottom: activeTab === tab ? "2px solid var(--color-text-primary)" : "2px solid transparent",
            padding: "6px 12px", fontSize: 13, cursor: "pointer", fontWeight: activeTab === tab ? 500 : 400,
            color: activeTab === tab ? "var(--color-text-primary)" : "var(--color-text-secondary)", marginBottom: -1
          }}>
            {tab === "tasks" ? `All tasks (${tasks.length})` : "Task types"}
          </button>
        ))}
      </div>

      {activeTab === "tasks" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {tasks.map((t, i) => (
            <div key={t.id} style={{
              background: "var(--color-background-primary)", border: "0.5px solid var(--color-border-tertiary)",
              borderRadius: 8, padding: "10px 14px", display: "flex", alignItems: "center", gap: 10,
              opacity: animatedIdx === i ? 0.4 : 1, transition: "opacity 0.4s"
            }}>
              <span style={{ fontSize: 11, color: "var(--color-text-secondary)", minWidth: 20, textAlign: "right" }}>#{t.id}</span>
              <span style={{ flex: 1, fontSize: 13, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{t.task}</span>
              <Badge route={t.route} />
              <span style={{ fontSize: 11, color: "var(--color-text-secondary)", minWidth: 55, textAlign: "right" }}>{t.tokens} tok</span>
              <span style={{ fontSize: 11, color: t.cost === 0 ? "#1D9E75" : "var(--color-text-secondary)", minWidth: 52, textAlign: "right" }}>
                {t.cost === 0 ? "free" : `$${t.cost.toFixed(5)}`}
              </span>
            </div>
          ))}
        </div>
      )}

      {activeTab === "types" && (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {Object.entries(typeBreakdown).sort((a, b) => b[1] - a[1]).map(([type, count]) => (
            <div key={type} style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span style={{ fontSize: 12, minWidth: 90, color: "var(--color-text-secondary)" }}>{type.replace("_", " ")}</span>
              <MiniBar value={count} max={maxType} color={TYPE_COLORS[type] || "#888"} />
              <span style={{ fontSize: 12, fontWeight: 500, minWidth: 16, color: "var(--color-text-primary)" }}>{count}</span>
            </div>
          ))}
          <div style={{ marginTop: 12, padding: "10px 14px", background: "var(--color-background-secondary)", borderRadius: 8, fontSize: 12, color: "var(--color-text-secondary)" }}>
            Code and math tasks route to remote — local model handles simple Q&A and extraction for free.
          </div>
        </div>
      )}

      {/* Add task */}
      <div style={{ marginTop: 16, display: "flex", gap: 8 }}>
        <input value={customTask} onChange={e => setCustomTask(e.target.value)}
          onKeyDown={e => e.key === "Enter" && addTask()}
          placeholder="Add a task to see how it routes..."
          style={{ flex: 1, fontSize: 13, padding: "8px 12px", borderRadius: 8, border: "0.5px solid var(--color-border-secondary)", background: "var(--color-background-primary)", color: "var(--color-text-primary)" }} />
        <button onClick={addTask} style={{ padding: "8px 16px", fontSize: 13, borderRadius: 8, cursor: "pointer" }}>
          Route ↗
        </button>
      </div>

      <div style={{ marginTop: 16, padding: "10px 14px", background: "var(--color-background-secondary)", borderRadius: 8, fontSize: 12, color: "var(--color-text-secondary)" }}>
        <strong style={{ color: "var(--color-text-primary)", fontWeight: 500 }}>Setup:</strong> Start LM Studio → load a model → click "Start Server". Add your <code style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>FIREWORKS_API_KEY</code> to <code style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>.env</code>. Then run <code style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>python main.py</code>.
      </div>
    </div>
  );
}
