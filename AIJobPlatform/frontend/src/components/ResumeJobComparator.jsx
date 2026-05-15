import React, { useMemo, useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  AlertCircle,
  BarChart3,
  Brain,
  FileText,
  IndianRupee,
  Loader2,
  Sparkles,
  UploadCloud,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import {
  compareResumeToJob,
  getComparatorSkillGap,
  listJobs,
  predictComparatorSalary,
  uploadComparatorResume,
} from "../api";

const scoreColor = (score = 0) => {
  if (score >= 80) return "#059669";
  if (score >= 60) return "#d97706";
  return "#dc2626";
};

const formatInr = (value) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value || 0);

export default function ResumeJobComparator() {
  const fileRef = useRef(null);
  const [resume, setResume] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [jobs, setJobs] = useState([]);
  const [jobId, setJobId] = useState("");
  const [comparison, setComparison] = useState(null);
  const [skillGap, setSkillGap] = useState(null);
  const [salary, setSalary] = useState(null);
  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);

  React.useEffect(() => {
    let alive = true;
    listJobs()
      .then((items) => {
        if (alive) setJobs(Array.isArray(items) ? items : items?.jobs || []);
      })
      .catch(() => {
        if (alive) setJobs([]);
      });
    return () => {
      alive = false;
    };
  }, []);

  const selectedJob = useMemo(
    () => jobs.find((job) => String(job.id) === String(jobId)),
    [jobs, jobId]
  );

  const handleFile = async (file) => {
    if (!file) return;
    setError("");
    setLoading("upload");
    setComparison(null);
    setSkillGap(null);
    setSalary(null);

    try {
      const uploaded = await uploadComparatorResume(file);
      setResume(uploaded);
      setPreviewUrl(file.type === "application/pdf" ? URL.createObjectURL(file) : "");
    } catch (err) {
      setError(err.message || "Resume upload failed.");
    } finally {
      setLoading("");
    }
  };

  const runAnalysis = async () => {
    if (!resume?.id || !jobId) {
      setError("Select a resume and job first.");
      return;
    }

    setError("");
    setLoading("analysis");
    try {
      const [matchResult, gapResult, salaryResult] = await Promise.all([
        compareResumeToJob(resume.id, Number(jobId)),
        getComparatorSkillGap({ resume_id: resume.id, job_id: Number(jobId) }),
        predictComparatorSalary({ resume_id: resume.id, job_id: Number(jobId) }),
      ]);
      setComparison(matchResult);
      setSkillGap(gapResult);
      setSalary(salaryResult);
    } catch (err) {
      setError(err.message || "Comparison failed.");
    } finally {
      setLoading("");
    }
  };

  const skillChart = useMemo(() => {
    if (!comparison) return [];
    return [
      { name: "Matched", value: comparison.matched_skills?.length || 0 },
      { name: "Missing", value: comparison.missing_skills?.length || 0 },
    ];
  }, [comparison]);

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-950">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <div className="flex flex-col gap-3 border-b border-zinc-200 pb-5 md:flex-row md:items-end md:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-normal text-zinc-950">
              Resume Job Comparator
            </h1>
            <p className="mt-1 text-sm text-zinc-600">
              Match score, ATS quality, salary estimate, and skill roadmap in one workflow.
            </p>
          </div>
          <button
            type="button"
            onClick={runAnalysis}
            disabled={!resume || !jobId || Boolean(loading)}
            className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-zinc-950 px-4 text-sm font-medium text-white shadow-sm transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:bg-zinc-400"
          >
            {loading === "analysis" ? <Loader2 className="h-4 w-4 animate-spin" /> : <Brain className="h-4 w-4" />}
            Analyze Fit
          </button>
        </div>

        {error ? (
          <div className="flex items-center gap-2 rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            <AlertCircle className="h-4 w-4" />
            {error}
          </div>
        ) : null}

        <div className="grid gap-6 lg:grid-cols-[380px_1fr]">
          <section className="flex flex-col gap-4">
            <div
              role="button"
              tabIndex={0}
              onClick={() => fileRef.current?.click()}
              onDragOver={(event) => {
                event.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(event) => {
                event.preventDefault();
                setDragging(false);
                handleFile(event.dataTransfer.files?.[0]);
              }}
              className={`flex min-h-44 cursor-pointer flex-col items-center justify-center rounded-md border border-dashed px-5 py-6 text-center transition ${
                dragging ? "border-emerald-500 bg-emerald-50" : "border-zinc-300 bg-white hover:border-zinc-500"
              }`}
            >
              <input
                ref={fileRef}
                type="file"
                className="hidden"
                accept=".pdf,.doc,.docx,.txt"
                onChange={(event) => handleFile(event.target.files?.[0])}
              />
              {loading === "upload" ? (
                <Loader2 className="h-8 w-8 animate-spin text-zinc-600" />
              ) : (
                <UploadCloud className="h-8 w-8 text-zinc-700" />
              )}
              <div className="mt-3 text-sm font-medium text-zinc-950">
                {resume?.original_name || "Drop resume or choose file"}
              </div>
              <div className="mt-1 text-xs text-zinc-500">PDF, DOCX, DOC, or TXT up to 5 MB</div>
            </div>

            <label className="flex flex-col gap-2">
              <span className="text-sm font-medium text-zinc-800">Target job</span>
              <select
                value={jobId}
                onChange={(event) => setJobId(event.target.value)}
                className="h-10 rounded-md border border-zinc-300 bg-white px-3 text-sm outline-none transition focus:border-zinc-900"
              >
                <option value="">Select job</option>
                {jobs.map((job) => (
                  <option key={job.id} value={job.id}>
                    {job.title} at {job.company}
                  </option>
                ))}
              </select>
            </label>

            {selectedJob ? (
              <div className="rounded-md border border-zinc-200 bg-white p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-zinc-950">
                  <FileText className="h-4 w-4" />
                  {selectedJob.title}
                </div>
                <p className="mt-2 line-clamp-5 text-sm leading-6 text-zinc-600">
                  {selectedJob.description}
                </p>
              </div>
            ) : null}

            <div className="overflow-hidden rounded-md border border-zinc-200 bg-white">
              <div className="border-b border-zinc-200 px-4 py-3 text-sm font-semibold text-zinc-950">
                PDF Preview
              </div>
              {previewUrl ? (
                <iframe title="Resume preview" src={previewUrl} className="h-96 w-full bg-white" />
              ) : (
                <div className="flex h-56 items-center justify-center px-4 text-center text-sm text-zinc-500">
                  Upload a PDF resume to preview it here.
                </div>
              )}
            </div>
          </section>

          <section className="grid gap-4 xl:grid-cols-3">
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-md border border-zinc-200 bg-white p-5 xl:col-span-1"
            >
              <div className="text-sm font-semibold text-zinc-600">Match score</div>
              <div className="mt-5 flex items-center justify-center">
                <div
                  className="grid h-40 w-40 place-items-center rounded-full"
                  style={{
                    background: `conic-gradient(${scoreColor(comparison?.match_percentage)} ${
                      comparison?.match_percentage || 0
                    }%, #e4e4e7 0)`,
                  }}
                >
                  <div className="grid h-28 w-28 place-items-center rounded-full bg-white">
                    <div className="text-center">
                      <div className="text-3xl font-semibold" style={{ color: scoreColor(comparison?.match_percentage) }}>
                        {Math.round(comparison?.match_percentage || 0)}%
                      </div>
                      <div className="text-xs text-zinc-500">overall</div>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-md border border-zinc-200 bg-white p-5 xl:col-span-1"
            >
              <div className="flex items-center justify-between">
                <div className="text-sm font-semibold text-zinc-600">ATS score</div>
                <BarChart3 className="h-4 w-4 text-zinc-500" />
              </div>
              <div className="mt-5 h-32">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={comparison?.heatmap || []}>
                    <CartesianGrid vertical={false} stroke="#e4e4e7" />
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                    <YAxis domain={[0, 100]} hide />
                    <Tooltip />
                    <Bar dataKey="score" radius={[4, 4, 0, 0]} fill="#2563eb" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 text-2xl font-semibold text-zinc-950">{comparison?.ats_score || resume?.ats_score || 0}/100</div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="rounded-md border border-zinc-200 bg-white p-5 xl:col-span-1"
            >
              <div className="flex items-center justify-between">
                <div className="text-sm font-semibold text-zinc-600">Salary prediction</div>
                <IndianRupee className="h-4 w-4 text-zinc-500" />
              </div>
              <div className="mt-6 text-3xl font-semibold text-zinc-950">
                {formatInr(salary?.salary_prediction || comparison?.salary_prediction)}
              </div>
              <div className="mt-2 text-sm text-zinc-500">
                {salary?.role || selectedJob?.title || "Target role"} · {salary?.confidence || "medium"} confidence
              </div>
            </motion.div>

            <div className="rounded-md border border-zinc-200 bg-white p-5 xl:col-span-1">
              <div className="text-sm font-semibold text-zinc-600">Skill gap</div>
              <div className="mt-4 h-56">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={skillChart} dataKey="value" nameKey="name" innerRadius={52} outerRadius={82}>
                      <Cell fill="#059669" />
                      <Cell fill="#dc2626" />
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="flex flex-wrap gap-2">
                {(skillGap?.missing_skills || comparison?.missing_skills || []).slice(0, 8).map((skill) => (
                  <span key={skill} className="rounded-md bg-red-50 px-2 py-1 text-xs font-medium text-red-700">
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            <div className="rounded-md border border-zinc-200 bg-white p-5 xl:col-span-2">
              <div className="mb-4 flex items-center gap-2 text-sm font-semibold text-zinc-600">
                <Sparkles className="h-4 w-4" />
                AI recommendations
              </div>
              <div className="grid gap-3 md:grid-cols-2">
                {(comparison?.improvement_suggestions || resume?.ai_suggestions || []).slice(0, 6).map((item, index) => (
                  <div key={`${item.title}-${index}`} className="rounded-md border border-zinc-200 p-3">
                    <div className="text-sm font-semibold text-zinc-950">{item.title || item.skill || "Improve resume"}</div>
                    <p className="mt-1 text-sm leading-6 text-zinc-600">{item.message || item.example || item.tips}</p>
                    {item.impact ? (
                      <div className="mt-2 text-xs font-medium text-emerald-700">Estimated impact +{item.impact}%</div>
                    ) : null}
                  </div>
                ))}
                {!comparison?.improvement_suggestions?.length && !resume?.ai_suggestions?.length ? (
                  <div className="rounded-md border border-zinc-200 p-3 text-sm text-zinc-500">
                    Recommendations appear after analysis.
                  </div>
                ) : null}
              </div>

              {comparison?.career_recommendations?.length ? (
                <div className="mt-5 border-t border-zinc-200 pt-4">
                  <div className="text-sm font-semibold text-zinc-600">Career path prediction</div>
                  {comparison.career_recommendations.map((item) => (
                    <div key={item.role} className="mt-2 rounded-md bg-zinc-50 p-3 text-sm text-zinc-700">
                      <span className="font-semibold text-zinc-950">{item.role}</span> in {item.timeline}. {item.next_step}
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
