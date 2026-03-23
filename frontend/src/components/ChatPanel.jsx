import { LoaderCircle, SendHorizontal, Sparkles } from "lucide-react";
import { useEffect, useRef } from "react";

function renderMessage(content) {
  return content.split("\n").map((line, index) => {
    const baseClass = "block";
    let specialClass = "text-slate-200";
    if (line.startsWith("Direct Answer:")) specialClass = "font-medium text-white";
    if (line.startsWith("Supporting Data:")) specialClass = "text-slate-100";
    if (line.startsWith("Analysis:")) specialClass = "text-cyan-100";
    if (line.startsWith("Insight:")) specialClass = "text-emerald-100";
    if (line.startsWith("Recommended Action:")) specialClass = "text-violet-100";
    if (line.startsWith("[LEAD]")) specialClass = "font-medium text-amber-200";
    if (line.startsWith("[ALERT]")) specialClass = "font-medium text-rose-300";
    return (
      <span key={`${line}-${index}`} className={`${baseClass} ${specialClass}`}>
        {line}
      </span>
    );
  });
}

export function ChatPanel({
  activeCase,
  chatHistory,
  query,
  onQueryChange,
  onSend,
  loading,
  suggestions,
  onSuggestionClick,
  placeholder
}) {
  const containerRef = useRef(null);

  useEffect(() => {
    const node = containerRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [chatHistory, loading]);

  return (
    <section className="flex h-full min-h-0 flex-col overflow-hidden rounded-[30px] border border-white/10 bg-slate-900/85">
      <div className="border-b border-white/10 px-5 py-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-slate-400">Investigation Chat</p>
            <h2 className="mt-1 font-display text-2xl text-white">
              {activeCase ? activeCase.case_name : "Choose or create a case"}
            </h2>
          </div>
          {loading ? <LoaderCircle className="animate-spin text-amber-300" size={18} /> : null}
        </div>
      </div>

      <div ref={containerRef} className="min-h-0 flex-1 space-y-4 overflow-y-auto px-5 py-5">
        {chatHistory.length === 0 ? (
          <div className="rounded-3xl border border-dashed border-white/10 bg-white/5 p-6 text-sm text-slate-400">
            Start with queries like "Who appears everywhere?" or "Show suspicious late-night activity".
          </div>
        ) : null}

        {chatHistory.map((message, index) => {
          const isUser = message.role === "user";
          return (
            <div key={`${message.role}-${index}`} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[88%] rounded-3xl px-4 py-3 text-sm leading-6 ${
                  isUser
                    ? "bg-amber-400 text-slate-950"
                    : "border border-white/10 bg-white/5 text-slate-100"
                }`}
              >
                {renderMessage(message.content)}
              </div>
            </div>
          );
        })}

        {loading ? (
          <div className="flex justify-start">
            <div className="rounded-3xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-300">
              <div className="flex items-center gap-2">
                <Sparkles size={14} className="text-amber-300" />
                <span>Classifying columns, correlating datasets, and generating leads</span>
                <span className="inline-flex gap-1">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-cyan-300 [animation-delay:-0.3s]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-cyan-300 [animation-delay:-0.15s]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-cyan-300" />
                </span>
              </div>
            </div>
          </div>
        ) : null}
      </div>

      <div className="border-t border-white/10 p-5">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            onSend(query);
          }}
          className="flex items-center gap-3"
        >
          <input
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder={placeholder}
            disabled={!activeCase || loading}
            className="flex-1 rounded-2xl border border-white/10 bg-slate-950 px-4 py-4 text-sm text-white outline-none transition focus:border-amber-400 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!activeCase || loading || !query.trim()}
            className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-cyan-400 text-slate-950 transition hover:bg-cyan-300 disabled:opacity-40"
          >
            <SendHorizontal size={18} />
          </button>
        </form>
        <div className="mt-3 overflow-x-auto pb-1">
          <div className="flex w-max min-w-full gap-2">
            {(suggestions || []).map((item) => (
              <button
                key={item}
                onClick={() => onSuggestionClick ? onSuggestionClick(item) : onSend(item)}
                disabled={!activeCase || loading}
                className="whitespace-nowrap rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs text-slate-300 transition hover:border-amber-400/30 hover:text-white disabled:opacity-40"
              >
                {item}
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
