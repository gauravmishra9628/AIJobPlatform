import { useEffect, useMemo, useRef, useState } from "react";
import { Mic, MicOff, Send, Sparkles } from "lucide-react";
import jsPDF from "jspdf";
import { refineRecruiterQuery, submitRecruiterQuery } from "../api";

function escapeCsv(value) {
  const raw = String(value ?? "");
  if (raw.includes(",") || raw.includes("\n") || raw.includes("\"")) {
    return `"${raw.replace(/\"/g, '""')}"`;
  }
  return raw;
}

function toWebSocketUrl(queryId) {
  const configured = import.meta.env.VITE_RECRUITER_WS_URL;
  if (configured) {
    return configured.includes("{queryId}")
      ? configured.replace("{queryId}", String(queryId))
      : configured;
  }

  if (typeof window === "undefined") {
    return "";
  }

  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://${window.location.host}/ws/recruiter/query/${queryId}/`;
}

function CandidateCard({ candidate }) {
  const scoreValue = candidate.score ?? candidate.relevance_score ?? 0;
  const score = Number(scoreValue || 0).toFixed(1);

  return (
    <article className="panel" style={{ marginBottom: "0.75rem" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: "0.8rem" }}>
        <div>
          <h3 style={{ marginBottom: "0.2rem" }}>{candidate.applicant || "Candidate"}</h3>
          <p style={{ margin: 0, color: "#4d5c56", fontSize: "0.92rem" }}>
            Candidate ID: {candidate.candidate_id ?? "-"}
          </p>
        </div>
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.32rem",
            padding: "0.35rem 0.58rem",
            borderRadius: "999px",
            border: "1px solid #d6d2c7",
            background: "#fffdf8",
            color: "#113d34",
            fontSize: "0.78rem",
            fontWeight: 800,
          }}
        >
          <Sparkles size={14} />
          Score {score}
        </span>
      </div>
      {candidate.reasoning ? (
        <p style={{ marginTop: "0.55rem", marginBottom: 0, color: "#44524c" }}>{candidate.reasoning}</p>
      ) : null}
    </article>
  );
}

export default function RecruiterAssistant() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [error, setError] = useState("");
  const [queryId, setQueryId] = useState(null);
  const [streamStatus, setStreamStatus] = useState("idle");

  const recognitionRef = useRef(null);
  const socketRef = useRef(null);
  const pollingRef = useRef(null);

  const canUseSpeech = useMemo(
    () => typeof window !== "undefined" && ("SpeechRecognition" in window || "webkitSpeechRecognition" in window),
    []
  );

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!query.trim()) {
      setError("Enter a query to search candidates.");
      return;
    }

    setLoading(true);
    setError("");
    setStreamStatus("idle");

    try {
      const data = await submitRecruiterQuery(query.trim());
      setResults(Array.isArray(data?.results) ? data.results : []);
      setQueryId(data?.query_id || null);
    } catch (err) {
      setError(err.message || "Query failed. Please try again.");
      setQueryId(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!queryId) {
      return undefined;
    }

    let active = true;
    let pollAttempts = 0;

    const stopPolling = () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
    };

    const startPollingFallback = () => {
      if (pollingRef.current) {
        return;
      }
      setStreamStatus("polling");
      pollingRef.current = setInterval(async () => {
        if (!active) {
          stopPolling();
          return;
        }

        pollAttempts += 1;
        try {
          const payload = await refineRecruiterQuery(queryId, { limit: 30 });
          if (!active) {
            return;
          }
          if (Array.isArray(payload?.results) && payload.results.length) {
            setResults(payload.results);
          }
          if (pollAttempts >= 8) {
            setStreamStatus("complete");
            stopPolling();
          }
        } catch {
          setStreamStatus("error");
          stopPolling();
        }
      }, 2000);
    };

    const wsUrl = toWebSocketUrl(queryId);
    if (!wsUrl) {
      startPollingFallback();
      return () => {
        active = false;
        stopPolling();
      };
    }

    try {
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        if (active) {
          setStreamStatus("live");
        }
      };

      socket.onmessage = (event) => {
        if (!active) {
          return;
        }

        try {
          const payload = JSON.parse(event.data || "{}");
          if (payload?.type === "query_result" && payload?.result) {
            setResults((current) => {
              const candidateId = payload.result.candidate_id;
              if (candidateId && current.some((item) => item.candidate_id === candidateId)) {
                return current;
              }
              return [...current, payload.result];
            });
          }

          if (payload?.type === "query_complete") {
            setStreamStatus("complete");
            socket.close();
          }
        } catch {
          // Ignore malformed messages and keep the stream open.
        }
      };

      socket.onerror = () => {
        if (!active) {
          return;
        }
        startPollingFallback();
      };

      socket.onclose = () => {
        if (!active) {
          return;
        }
        if (streamStatus !== "complete") {
          startPollingFallback();
        }
      };
    } catch {
      startPollingFallback();
    }

    return () => {
      active = false;
      stopPolling();
      if (socketRef.current) {
        socketRef.current.close();
        socketRef.current = null;
      }
    };
  }, [queryId]);

  const exportCsv = () => {
    if (!results.length) {
      return;
    }

    const headers = ["candidate_id", "applicant", "score", "reasoning"];
    const rows = results.map((item) => [
      item.candidate_id,
      item.applicant,
      item.score ?? item.relevance_score,
      item.reasoning,
    ]);

    const csvText = [headers, ...rows]
      .map((row) => row.map(escapeCsv).join(","))
      .join("\n");

    const blob = new Blob([csvText], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `recruiter-query-${queryId || "results"}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const exportPdf = () => {
    if (!results.length) {
      return;
    }

    const doc = new jsPDF({ unit: "pt", format: "a4" });
    doc.setFontSize(14);
    doc.text("Recruiter Assistant Results", 40, 46);
    doc.setFontSize(10);
    doc.text(`Query: ${query}`, 40, 66);

    let y = 90;
    results.forEach((item, index) => {
      if (y > 760) {
        doc.addPage();
        y = 46;
      }

      const line = `${index + 1}. ${item.applicant || "Candidate"} | Score ${Number(item.score ?? item.relevance_score ?? 0).toFixed(1)}`;
      doc.text(line, 40, y);
      y += 14;

      const reasonText = String(item.reasoning || "No reasoning provided");
      const wrapped = doc.splitTextToSize(reasonText, 500);
      doc.text(wrapped, 54, y);
      y += wrapped.length * 12 + 10;
    });

    doc.save(`recruiter-query-${queryId || "results"}.pdf`);
  };

  const toggleVoice = () => {
    if (!canUseSpeech) {
      setError("Voice input is not supported in this browser.");
      return;
    }

    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      setIsListening(false);
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => {
      setIsListening(true);
      setError("");
    };

    recognition.onresult = (event) => {
      const transcript = event?.results?.[0]?.[0]?.transcript || "";
      if (transcript) {
        setQuery((prev) => `${prev} ${transcript}`.trim());
      }
    };

    recognition.onerror = () => {
      setError("Voice capture failed. Try again or type your query.");
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  return (
    <section className="panel" aria-label="Recruiter assistant" style={{ display: "grid", gap: "0.75rem" }}>
      <header style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: "0.8rem" }}>
        <div>
          <h2 style={{ fontSize: "1.2rem" }}>Recruiter Assistant</h2>
          <p style={{ margin: "0.25rem 0 0", color: "#4d5c56", fontSize: "0.92rem" }}>
            Ask in natural language to surface top candidate matches.
          </p>
        </div>
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "0.4rem",
            border: "1px solid #d6d2c7",
            borderRadius: "999px",
            padding: "0.35rem 0.65rem",
            fontSize: "0.8rem",
            color: "#113d34",
            fontWeight: 800,
            background: "#fffdf8",
          }}
        >
          <Sparkles size={14} />
          AI Enabled
        </span>
      </header>

      <div className="buttonRow" style={{ justifyContent: "flex-start" }}>
        <button className="ghostButton fitButton" type="button" onClick={exportCsv} disabled={!results.length}>
          Export CSV
        </button>
        <button className="ghostButton fitButton" type="button" onClick={exportPdf} disabled={!results.length}>
          Export PDF
        </button>
        {streamStatus === "live" ? <span className="chip strong">Live stream</span> : null}
        {streamStatus === "polling" ? <span className="chip">Syncing results...</span> : null}
      </div>

      <div className="chat-history" style={{ maxHeight: "22rem", overflowY: "auto", paddingRight: "0.2rem" }}>
        {results.length ? (
          results.map((result, index) => <CandidateCard key={`${result.candidate_id || "candidate"}-${index}`} candidate={result} />)
        ) : (
          <div
            style={{
              border: "1px dashed #d6d2c7",
              borderRadius: "8px",
              padding: "1rem",
              color: "#5f6b66",
              background: "#fffdf8",
            }}
          >
            No results yet. Try: Top ATS score applicants with React and Django.
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit} className="query-input" style={{ display: "grid", gridTemplateColumns: "1fr auto auto", gap: "0.5rem" }}>
        <input
          type="text"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Ask about candidates..."
          aria-label="Recruiter query"
        />
        <button
          type="button"
          onClick={toggleVoice}
          disabled={loading}
          aria-label={isListening ? "Stop voice input" : "Start voice input"}
          title={canUseSpeech ? "Use voice input" : "Voice not supported in this browser"}
          style={{ width: "46px", padding: "0" }}
        >
          {isListening ? <MicOff size={20} /> : <Mic size={20} />}
        </button>
        <button type="submit" disabled={loading || !query.trim()} aria-label="Submit recruiter query" style={{ width: "46px", padding: "0" }}>
          <Send size={20} />
        </button>
      </form>

      {loading ? <p style={{ margin: 0, color: "#4d5c56" }}>Finding best candidates...</p> : null}
      {error ? <p style={{ margin: 0, color: "#8f2d18" }}>{error}</p> : null}
    </section>
  );
}
