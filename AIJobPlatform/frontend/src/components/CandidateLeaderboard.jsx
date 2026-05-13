import { useEffect, useState } from "react";
import { getCandidateLeaderboard } from "../api";

export default function CandidateLeaderboard() {
  const [leaderboard, setLeaderboard] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    async function loadLeaderboard() {
      setLoading(true);
      setError("");
      try {
        const data = await getCandidateLeaderboard();
        if (!mounted) return;
        setLeaderboard(data.top_candidates || []);
      } catch (err) {
        if (!mounted) return;
        setError(err?.message || "Failed to load leaderboard");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    loadLeaderboard();
    return () => {
      mounted = false;
    };
  }, []);

  if (loading) return <div className="panel">Loading leaderboard...</div>;
  if (error) return <div className="panel error">{error}</div>;

  return (
    <section className="panel">
      <div className="sectionHeader inline">
        <div>
          <p className="eyebrow">Leaderboard</p>
          <h2>Top candidates</h2>
        </div>
      </div>
      <div className="candidateRankList">
        {leaderboard.length ? leaderboard.map((candidate, index) => (
          <article className="candidateRankCard" key={candidate.candidate_id}>
            <div>
              <strong>{index + 1}. {candidate.candidate_name}</strong>
              <p>{candidate.headline || "Candidate profile"}</p>
              <div className="skillLine compact">
                {(candidate.skills || []).slice(0, 5).map((skill) => <span key={`${candidate.candidate_id}-${skill}`}>{skill}</span>)}
              </div>
            </div>
            <div className="rankActions">
              <span className="chip strong">{candidate.leaderboard_score} pts</span>
              <span className="chip">{candidate.badge_count} badges</span>
            </div>
          </article>
        )) : <p className="muted">No candidates to rank yet.</p>}
      </div>
    </section>
  );
}
