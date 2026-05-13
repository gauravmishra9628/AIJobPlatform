import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { getPublicProfile } from "../api";

export default function PublicProfilePage() {
  const { userId } = useParams();
  const [profileData, setProfileData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let mounted = true;
    async function loadProfile() {
      setLoading(true);
      setError("");
      try {
        const data = await getPublicProfile(userId);
        if (!mounted) return;
        setProfileData(data);
      } catch (err) {
        if (!mounted) return;
        setError(err?.message || "Failed to load profile");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    loadProfile();
    return () => {
      mounted = false;
    };
  }, [userId]);

  if (loading) {
    return <div className="panel">Loading public profile...</div>;
  }

  if (error) {
    return <div className="panel error">{error}</div>;
  }

  if (!profileData) {
    return <div className="panel">Profile not found.</div>;
  }

  const profile = profileData.profile || {};
  const user = profileData.user || {};
  const badges = profileData.badges || [];
  const portfolio = profileData.portfolio || [];

  return (
    <section className="panel">
      <div className="sectionHeader inline">
        <div>
          <p className="eyebrow">Public profile</p>
          <h2>{user.first_name || user.email}</h2>
        </div>
        <Link to="/profile" className="ghostButton">Edit profile</Link>
      </div>

      <div className="stat-cards small">
        <div className="stat-card">
          <h4>Profile strength</h4>
          <div className="stat-value">{profileData.profile_strength ?? 0}%</div>
        </div>
        <div className="stat-card">
          <h4>Badges</h4>
          <div className="stat-value">{badges.length}</div>
        </div>
        <div className="stat-card">
          <h4>Portfolio items</h4>
          <div className="stat-value">{portfolio.length}</div>
        </div>
      </div>

      <div className="insightList">
        <p>{profile.headline || "No headline yet."}</p>
        <p>{profile.bio || profile.about || "No bio yet."}</p>
        <p>{profile.location || "Location not set."}</p>
      </div>

      <div className="skillLine compact">
        {(profile.skills || []).length ? profile.skills.map((skill) => <span key={skill}>{skill}</span>) : <span>Add skills to unlock visibility</span>}
      </div>

      {portfolio.length > 0 && (
        <div className="roadmapListInline">
          {portfolio.slice(0, 4).map((item, index) => (
            <div className="roadmapStep" key={`${item.name || item.title || index}`}>
              <strong>{item.name || item.title || `Portfolio item ${index + 1}`}</strong>
              <span>{item.description || item.summary || "Portfolio entry"}</span>
              {item.link ? <a href={item.link} target="_blank" rel="noreferrer">Open link</a> : null}
            </div>
          ))}
        </div>
      )}

      {badges.length > 0 && (
        <div className="roadmapListInline">
          {badges.slice(0, 6).map((badge) => (
            <div className="roadmapStep" key={badge.id}>
              <strong>{badge.skill_name}</strong>
              <span>{badge.badge_tier} badge via {badge.source}</span>
              <span>{badge.score}%</span>
            </div>
          ))}
        </div>
      )}

      {profileData.resume_link ? (
        <a className="featurePill" href={profileData.resume_link} target="_blank" rel="noreferrer">
          Shareable resume link
        </a>
      ) : null}
    </section>
  );
}
