import { useState } from "react";
import { autoApplyJobs } from "../api";

export default function AutoApplyPanel({ onApplied }) {
  const [threshold, setThreshold] = useState(80);
  const [limit, setLimit] = useState(10);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(false);

  const handleAutoApply = async () => {
    setLoading(true);
    setStatus("");
    try {
      const data = await autoApplyJobs({ threshold, limit });
      setStatus(data.detail || `Applied to ${data.applied_jobs?.length || 0} jobs.`);
      if (onApplied) onApplied(data);
    } catch (err) {
      setStatus(err?.message || "Auto apply failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel">
      <div className="sectionHeader inline">
        <div>
          <p className="eyebrow">One-click apply</p>
          <h2>Auto Apply AI</h2>
        </div>
      </div>
      <div className="twoCol">
        <label className="field">
          <span>Match threshold</span>
          <input type="number" min="50" max="100" value={threshold} onChange={(event) => setThreshold(Number(event.target.value))} />
        </label>
        <label className="field">
          <span>Max applications</span>
          <input type="number" min="1" max="25" value={limit} onChange={(event) => setLimit(Number(event.target.value))} />
        </label>
      </div>
      <button type="button" disabled={loading} onClick={handleAutoApply}>
        {loading ? "Applying..." : "Auto Apply"}
      </button>
      {status ? <p className="status compactStatus">{status}</p> : null}
    </section>
  );
}
