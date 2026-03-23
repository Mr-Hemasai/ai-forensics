import { Database, Plus, Shield } from "lucide-react";

export function CaseSidebar({
  activeCase,
  cases,
  activeCaseId,
  showNewCaseForm,
  onToggleNewCase,
  newCaseName,
  onNewCaseNameChange,
  onCreateCase,
  observationItems,
  onSelectCase
}) {
  return (
    <aside className="flex h-full min-h-0 flex-col overflow-hidden rounded-[28px] border border-white/10 bg-slate-900/90 p-4 shadow-glow">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="inline-flex rounded-2xl bg-cyan-400/10 p-2 text-cyan-200">
            <Shield size={18} />
          </div>
          <p className="mt-3 text-[11px] uppercase tracking-[0.28em] text-slate-400">Investigation</p>
          <h1 className="mt-2 font-display text-2xl text-white">{ "AI Forensic Desk"}</h1>
          <p className="mt-2 text-sm text-slate-400">Case-based telecom and digital analysis workspace.</p>
        </div>
      </div>  <br></br>
        <button
          onClick={onToggleNewCase}
          className="inline-flex items-center gap-5 rounded-xl bg-amber-400 px-10 py-2 text-m font-medium text-slate-950 transition hover:bg-amber-300"
        >
          <Plus size={14} />
          New Case
        </button>
    

      {showNewCaseForm ? (
        <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-3">
          <input
            value={newCaseName}
            onChange={(event) => onNewCaseNameChange(event.target.value)}
            placeholder="Enter case name"
            className="w-full rounded-xl border border-white/10 bg-slate-950 px-4 py-3 text-sm text-white outline-none transition focus:border-amber-400"
          />
          <div className="mt-3 flex gap-2">
            <button
              onClick={onCreateCase}
              className="flex-1 rounded-xl bg-cyan-400 px-4 py-2.5 text-sm font-medium text-slate-950 transition hover:bg-cyan-300"
            >
              Save Case
            </button>
            <button
              onClick={onToggleNewCase}
              className="rounded-xl border border-white/10 px-4 py-2.5 text-sm text-slate-300 transition hover:bg-white/5"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : null}

      {observationItems?.length ? (
        <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-3">
          <p className="text-[11px] uppercase tracking-[0.24em] text-slate-400">Observation Box</p>
          <div className="mt-3 h-40 overflow-y-auto rounded-xl bg-slate-950/80 p-3">
            <div className="space-y-2 text-sm text-slate-200">
              {observationItems.map((item) => (
                <p key={item}>• {item}</p>
              ))}
            </div>
          </div>
        </div>
      ) : null}

      <div className="mt-5 flex items-center justify-between">
        <p className="text-[11px] uppercase tracking-[0.24em] text-slate-400">Cases</p>
        <Database size={16} className="text-slate-500" />
      </div>

      <div className="mt-3 min-h-0 flex-1 space-y-3 overflow-y-auto pr-1">
        {cases.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-white/10 bg-white/5 p-4 text-sm text-slate-400">
            No cases yet. Create one to begin.
          </div>
        ) : null}

        {cases.map((item) => {
          const active = item.case_id === activeCaseId;
          return (
            <button
              key={item.case_id}
              onClick={() => onSelectCase(item.case_id)}
              className={`w-full rounded-2xl border p-4 text-left transition ${
                active
                  ? "border-amber-400/60 bg-amber-400/10"
                  : "border-white/10 bg-white/5 hover:border-white/20 hover:bg-white/10"
              }`}
            >
              <p className="font-display text-base text-white">{item.case_name}</p>
              <p className="mt-1 text-xs text-slate-400">Case ID: {item.case_id}</p>
              <div className="mt-3 flex gap-2 text-xs text-slate-300">
                <span className="rounded-full bg-white/10 px-2 py-1">{item.dataset_count} datasets</span>
                <span className="rounded-full bg-white/10 px-2 py-1">{item.chat_count} chats</span>
              </div>
            </button>
          );
        })}
      </div>
    </aside>
  );
}
