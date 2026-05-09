import "./styles.css";

const jobs = [
  {
    title: "AI Product Analyst",
    company: "NexaWorks",
    location: "Remote",
    salary: "$92k - $118k",
    match: 94,
    type: "Full-time",
    skills: ["Prompting", "SQL", "Dashboards"],
  },
  {
    title: "Machine Learning Engineer",
    company: "SignalForge",
    location: "Bengaluru",
    salary: "$120k - $150k",
    match: 89,
    type: "Hybrid",
    skills: ["Python", "PyTorch", "MLOps"],
  },
  {
    title: "AI Resume Reviewer",
    company: "CareerPilot",
    location: "New York",
    salary: "$76k - $96k",
    match: 86,
    type: "Contract",
    skills: ["NLP", "Hiring", "Feedback"],
  },
];

const statItems = [
  ["1,284", "Active jobs"],
  ["82%", "Avg. match score"],
  ["19 min", "Fastest shortlist"],
];

document.querySelector("#app").innerHTML = `
  <main class="min-h-screen bg-[#f6f7f4]">
    <nav class="border-b border-[#dfe4dc] bg-white/90">
      <div class="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
        <a class="text-xl font-semibold tracking-tight text-[#17211c]" href="#">
          AIJobPlatform
        </a>
        <div class="hidden items-center gap-2 md:flex">
          <a class="px-3 py-2 text-sm font-medium text-[#526157]" href="#">Jobs</a>
          <a class="px-3 py-2 text-sm font-medium text-[#526157]" href="#">Candidates</a>
          <a class="px-3 py-2 text-sm font-medium text-[#526157]" href="#">Insights</a>
        </div>
        <button class="rounded-md bg-[#1b5e4b] px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-[#164a3d]">
          Post Job
        </button>
      </div>
    </nav>

    <section class="border-b border-[#dfe4dc] bg-[#e9efe8]">
      <div class="mx-auto grid max-w-7xl gap-8 px-5 py-10 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
        <div>
          <p class="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-[#1b5e4b]">
            AI powered hiring
          </p>
          <h1 class="max-w-3xl text-4xl font-bold tracking-tight text-[#17211c] md:text-6xl">
            Match candidates to the right AI jobs faster.
          </h1>
          <p class="mt-5 max-w-2xl text-lg leading-8 text-[#526157]">
            Search, score, and shortlist roles with a focused dashboard built for job seekers and recruiters.
          </p>
          <form class="mt-7 grid gap-3 rounded-lg border border-[#cad5ca] bg-white p-3 shadow-sm md:grid-cols-[1fr_1fr_auto]">
            <input class="min-h-12 rounded-md border border-[#d7ded5] px-4 text-[#17211c] outline-none focus:border-[#1b5e4b]" placeholder="Role or skill" />
            <input class="min-h-12 rounded-md border border-[#d7ded5] px-4 text-[#17211c] outline-none focus:border-[#1b5e4b]" placeholder="Location" />
            <button class="min-h-12 rounded-md bg-[#d96f32] px-6 font-semibold text-white hover:bg-[#bd5d27]" type="button">
              Search Jobs
            </button>
          </form>
        </div>

        <div class="rounded-lg border border-[#cad5ca] bg-white p-5 shadow-sm">
          <div class="mb-5 flex items-center justify-between">
            <div>
              <p class="text-sm font-medium text-[#526157]">Candidate profile</p>
              <h2 class="text-2xl font-bold text-[#17211c]">Resume Match</h2>
            </div>
            <span class="rounded-full bg-[#e4f3ec] px-3 py-1 text-sm font-bold text-[#1b5e4b]">94%</span>
          </div>
          <div class="space-y-4">
            <div>
              <div class="mb-2 flex justify-between text-sm font-medium text-[#526157]">
                <span>Skill fit</span><span>Excellent</span>
              </div>
              <div class="h-3 overflow-hidden rounded-full bg-[#e8ece6]">
                <div class="h-full w-[92%] bg-[#1b5e4b]"></div>
              </div>
            </div>
            <div>
              <div class="mb-2 flex justify-between text-sm font-medium text-[#526157]">
                <span>Experience level</span><span>Strong</span>
              </div>
              <div class="h-3 overflow-hidden rounded-full bg-[#e8ece6]">
                <div class="h-full w-[84%] bg-[#d96f32]"></div>
              </div>
            </div>
          </div>
          <div class="mt-6 grid grid-cols-3 gap-3">
            ${statItems
              .map(
                ([value, label]) => `
                  <div class="rounded-md border border-[#edf0eb] bg-[#fafbf8] p-3">
                    <p class="text-xl font-bold text-[#17211c]">${value}</p>
                    <p class="mt-1 text-xs font-medium text-[#526157]">${label}</p>
                  </div>
                `,
              )
              .join("")}
          </div>
        </div>
      </div>
    </section>

    <section class="mx-auto max-w-7xl px-5 py-9">
      <div class="mb-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 class="text-2xl font-bold tracking-tight text-[#17211c]">Recommended jobs</h2>
          <p class="mt-1 text-sm text-[#526157]">Ranked by profile fit, skill overlap, and hiring activity.</p>
        </div>
        <select class="h-11 rounded-md border border-[#cad5ca] bg-white px-3 text-sm font-medium text-[#17211c]">
          <option>Best match</option>
          <option>Newest</option>
          <option>Salary high to low</option>
        </select>
      </div>

      <div class="grid gap-4 lg:grid-cols-3">
        ${jobs
          .map(
            (job) => `
              <article class="job-card rounded-lg border border-[#dfe4dc] bg-white p-5 shadow-sm">
                <div class="flex items-start justify-between gap-4">
                  <div>
                    <h3 class="text-lg font-bold text-[#17211c]">${job.title}</h3>
                    <p class="mt-1 text-sm font-medium text-[#526157]">${job.company} · ${job.location}</p>
                  </div>
                  <span class="rounded-full bg-[#e4f3ec] px-3 py-1 text-sm font-bold text-[#1b5e4b]">${job.match}%</span>
                </div>
                <div class="mt-5 flex flex-wrap gap-2">
                  ${job.skills
                    .map(
                      (skill) => `
                        <span class="rounded-md border border-[#dfe4dc] bg-[#fafbf8] px-2.5 py-1 text-xs font-semibold text-[#526157]">${skill}</span>
                      `,
                    )
                    .join("")}
                </div>
                <div class="mt-6 flex items-center justify-between border-t border-[#edf0eb] pt-4">
                  <div>
                    <p class="text-sm font-bold text-[#17211c]">${job.salary}</p>
                    <p class="mt-1 text-xs font-medium text-[#526157]">${job.type}</p>
                  </div>
                  <button class="rounded-md border border-[#1b5e4b] px-3 py-2 text-sm font-semibold text-[#1b5e4b] hover:bg-[#e4f3ec]">
                    View
                  </button>
                </div>
              </article>
            `,
          )
          .join("")}
      </div>
    </section>
  </main>
`;
