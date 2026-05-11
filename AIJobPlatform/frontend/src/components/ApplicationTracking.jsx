import { useEffect, useState } from "react";
import { getApplicationHistory, updateApplicationStage } from "../api";

export default function ApplicationTracking({ applicationId, isRecruiter = false }) {
  const [history, setHistory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [newStage, setNewStage] = useState("");
  const [notes, setNotes] = useState("");

  const stages = ["applied", "reviewing", "shortlisted", "rejected"];

  const fetchHistory = async () => {
    try {
      const data = await getApplicationHistory(applicationId);
      setHistory(data);
      setNewStage(data.current_status || "");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [applicationId]);

  const handleStageUpdate = async (e) => {
    e.preventDefault();
    if (newStage === history.current_status) {
      setError("Select a different stage");
      return;
    }

    try {
      await updateApplicationStage(applicationId, newStage, notes);
      setNotes("");
      await fetchHistory();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) return <p>Loading application status...</p>;
  if (error) return <p className="error">{error}</p>;
  if (!history) return <p>No application data available.</p>;

  return (
    <div className="application-tracking card">
      <h2>Application Status Tracking</h2>

      <div className="stage-timeline">
        <h3>Current Status: <span className="status-badge">{history.current_status}</span></h3>
        
        {isRecruiter && (
          <form onSubmit={handleStageUpdate} className="stage-update-form">
            <div className="form-group">
              <label>Update Status:</label>
              <select 
                value={newStage} 
                onChange={(e) => setNewStage(e.target.value)}
                required
              >
                <option value="">Select new stage...</option>
                {stages.map(stage => (
                  <option key={stage} value={stage}>{stage}</option>
                ))}
              </select>
            </div>
            
            <div className="form-group">
              <label>Notes (optional):</label>
              <textarea 
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Add notes about this stage change..."
              />
            </div>
            
            <button type="submit">Update Status</button>
          </form>
        )}
      </div>

      {history.history && history.history.length > 0 && (
        <div className="history-section">
          <h3>Stage History</h3>
          <div className="timeline">
            {history.history.map((entry, idx) => (
              <div key={idx} className="timeline-entry">
                <div className="timeline-marker"></div>
                <div className="timeline-content">
                  <h4>
                    {entry.from_stage ? `${entry.from_stage} → ${entry.to_stage}` : entry.to_stage}
                  </h4>
                  <p className="changed-by">Changed by: {entry.changed_by}</p>
                  {entry.notes && <p className="notes">{entry.notes}</p>}
                  <p className="timestamp">{new Date(entry.created_at).toLocaleString()}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
