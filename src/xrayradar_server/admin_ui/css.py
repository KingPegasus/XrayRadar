"""CSS styles for admin UI."""

CSS = """body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial; margin: 0; background: #0b1220; color: #e5e7eb; }
header { padding: 16px 20px; border-bottom: 1px solid #1f2937; display: flex; justify-content: space-between; align-items: center; }
header .title { font-weight: 700; letter-spacing: 0.2px; }
header .meta { opacity: 0.9; font-size: 13px; }
.layout { display: grid; grid-template-columns: 240px 1fr; min-height: calc(100vh - 66px); }
aside { border-right: 1px solid #1f2937; background: rgba(15, 23, 42, 0.4); }
.sideInner { padding: 14px 12px; }
.navItem { display: flex; align-items: center; gap: 10px; padding: 10px 10px; border-radius: 10px; cursor: pointer; color: #cbd5e1; border: 1px solid transparent; }
.navItem:hover { background: rgba(148, 163, 184, 0.08); }
.navItem.active { background: rgba(37, 99, 235, 0.18); border-color: rgba(37, 99, 235, 0.35); color: #e5e7eb; }
.navDot { width: 9px; height: 9px; border-radius: 999px; background: #334155; }
.navItem.active .navDot { background: #2563eb; }
.content { padding: 16px 20px; }
.view { display: block; }
.hidden { display: none !important; }
.grid2 { display: grid; grid-template-columns: 420px 1fr; gap: 16px; }
@media (max-width: 1000px) {
  .layout { grid-template-columns: 1fr; }
  aside { border-right: 0; border-bottom: 1px solid #1f2937; }
  .sideInner { display: flex; gap: 10px; flex-wrap: wrap; }
  .grid2 { grid-template-columns: 1fr; }
}
section { background: #0f172a; border: 1px solid #1f2937; border-radius: 10px; padding: 14px; }
h1 { margin: 0 0 20px 0; font-size: 24px; font-weight: 700; color: #e5e7eb; }
h2 { margin: 0 0 10px 0; font-size: 14px; text-transform: uppercase; letter-spacing: 0.08em; color: #cbd5e1; }
label { display: block; margin: 10px 0 6px; font-size: 12px; color: #cbd5e1; }
input, select { width: 90%; padding: 10px; border-radius: 8px; border: 1px solid #334155; background: #0b1220; color: #e5e7eb; }
input::placeholder { color: #64748b; }
button { padding: 10px 12px; border-radius: 8px; border: 1px solid #334155; background: #111827; color: #e5e7eb; cursor: pointer; }
button.primary { background: #2563eb; border-color: #2563eb; }
button.danger { background: #b91c1c; border-color: #b91c1c; }
button.small { padding: 6px 10px; font-size: 12px; }
button:disabled { opacity: 0.5; cursor: not-allowed; }
.row { display: flex; gap: 10px; flex-wrap: wrap; }
.row > * { flex: 1; min-width: 180px; }
.muted { color: #94a3b8; font-size: 12px; }
.error { color: #fca5a5; font-size: 12px; white-space: pre-wrap; }
.ok { color: #86efac; font-size: 12px; white-space: pre-wrap; }
table { width: 100%; border-collapse: collapse; table-layout: fixed; }
th, td { border-bottom: 1px solid #1f2937; padding: 8px; font-size: 13px; text-align: left; vertical-align: top; word-wrap: break-word; overflow-wrap: break-word; }
th:nth-child(1), td:nth-child(1) { width: 50px; } /* ID */
th:nth-child(2), td:nth-child(2) { width: 25%; min-width: 100px; } /* Name */
th:nth-child(3), td:nth-child(3) { width: 35%; min-width: 150px; word-break: break-all; } /* Email - wrap */
th:nth-child(4), td:nth-child(4) { width: auto; white-space: normal; } /* Flags */
.pill { white-space: nowrap; display: inline-block; }
th { color: #cbd5e1; font-weight: 600; }
tr:hover td { background: rgba(148, 163, 184, 0.06); }
.pill { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 12px; border: 1px solid #334155; color: #cbd5e1; }
.pill.admin { border-color: #2563eb; color: #93c5fd; }
.pill.revoked { border-color: #b91c1c; color: #fca5a5; }
a { color: #93c5fd; }
.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; gap: 10px; }
.mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
.codeblock { white-space: pre; overflow: auto; margin: 0; padding: 12px; border-radius: 10px; border: 1px solid #1f2937; background: rgba(0, 0, 0, 0.22); color: #e5e7eb; font-size: 12px; line-height: 1.45; }

.modalOverlay { position: fixed; inset: 0; background: rgba(0, 0, 0, 0.64); display: grid; place-items: center; padding: 16px; z-index: 50; }
.modalCard { width: min(980px, 100%); max-height: min(86vh, 900px); overflow: hidden; display: grid; grid-template-rows: auto 1fr; }
.modalHeader { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; padding: 12px 14px; border-bottom: 1px solid #1f2937; background: rgba(15, 23, 42, 0.85); }
.modalBody { padding: 14px; overflow: auto; }
.modalTitle { font-weight: 800; letter-spacing: 0.2px; }
.modalClose { width: 34px; height: 34px; padding: 0; border-radius: 10px; display: grid; place-items: center; }

/* Dashboard styles */
.dashboard-stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 20px; margin-top: 24px; }
.dashboard-card { background: #1f2937; border: 1px solid #374151; border-radius: 12px; padding: 20px; transition: all 0.2s ease; }
.dashboard-card:hover { border-color: #4b5563; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3); transform: translateY(-2px); }
.dashboard-card-title { font-weight: 700; font-size: 13px; text-transform: uppercase; letter-spacing: 0.05em; color: #9ca3af; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #374151; }
.dashboard-stat-item { margin-bottom: 16px; }
.dashboard-stat-item:last-child { margin-bottom: 0; }
.dashboard-stat-label { font-size: 12px; color: #9ca3af; margin-bottom: 6px; font-weight: 500; }
.dashboard-stat-value { font-size: 28px; font-weight: 700; color: #f3f4f6; line-height: 1.2; }
.dashboard-stat-value.highlight-blue { color: #60a5fa; }
.dashboard-stat-value.highlight-green { color: #34d399; }
.dashboard-stat-value.highlight-yellow { color: #fbbf24; }
.dashboard-stat-value.highlight-red { color: #f87171; }
.dashboard-stat-value.highlight-purple { color: #a78bfa; }
@media (max-width: 768px) {
  .dashboard-stats { grid-template-columns: 1fr; gap: 16px; }
  .dashboard-card { padding: 16px; }
  .dashboard-stat-value { font-size: 24px; }
}"""
