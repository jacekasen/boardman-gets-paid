"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  ArrowDown,
  ArrowDownToLine,
  ArrowRight,
  ArrowUpRight,
  ChartNoAxesColumnIncreasing,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  Columns3,
  Layers,
  Search,
  X,
  BookOpen,
} from "lucide-react";
import {
  league,
  brackets,
  money,
  compact,
  initials,
  type Player,
} from "@/lib/data";

type View = "overview" | "players" | "teams" | "methodology";
const nav = [
  { id: "overview", label: "Overview", icon: Columns3 },
  { id: "players", label: "Surplus board", icon: ChartNoAxesColumnIncreasing },
  { id: "teams", label: "Team payrolls", icon: Layers },
] as const;
const active = league.players.filter((p) => !p.is_dead_money);

function Brand({ small = false }: { small?: boolean }) {
  return (
    <div className={`brand ${small ? "small" : ""}`}>
      <svg viewBox="0 0 40 40" aria-hidden="true">
        <circle cx="20" cy="20" r="17" />
        <path d="M3 20h34M20 3v34M8 8c15 2 22 9 24 24M32 8C17 10 10 17 8 32" />
      </svg>
      {!small && (
        <span>
          BOARD MAN
          <br />
          GETS PAID<span className="brand-period">.</span>
        </span>
      )}
    </div>
  );
}

export default function Dashboard() {
  const [view, setView] = useState<View>("overview");
  const [query, setQuery] = useState("");
  const [team, setTeam] = useState("all");
  const [tier, setTier] = useState("all");
  const [mode, setMode] = useState<"all" | "bargains" | "anchors" | "roi">("all");
  const [sort, setSort] = useState<{
    key: "net_surplus" | "salary" | "war" | "friction_tax" | "fair_value" | "roi_multiple";
    asc: boolean;
  }>({ key: "net_surplus", asc: false });
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState<Player | null>(null);

  const filtered = useMemo(() => {
    return active
      .filter((p) => {
        if (team !== "all" && p.team !== team) return false;
        if (tier !== "all" && p.contract_tier !== tier) return false;
        if (mode === "bargains" && p.net_surplus <= 0) return false;
        if (mode === "anchors" && p.net_surplus >= 0) return false;
        if (mode === "roi" && (!p.is_salary_known || p.roi_multiple === null)) return false;
        if (query) {
          const q = query.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
          const target = `${p.player_name} ${p.team} ${p.contract_tier}`
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase();
          if (!target.includes(q)) return false;
        }
        return true;
      })
      .sort((a, b) => {
        const valA = (a[sort.key] as number | null | undefined) ?? -999999999;
        const valB = (b[sort.key] as number | null | undefined) ?? -999999999;
        return (valA - valB) * (sort.asc ? 1 : -1);
      });
  }, [query, team, tier, mode, sort]);

  const pageSize = view === "overview" ? 6 : 15;
  const shown = filtered.slice(page * pageSize, (page + 1) * pageSize);
  function navigate(next: View) {
    setView(next);
    setPage(0);
  }
  function sortBy(key: typeof sort.key) {
    setSort({ key, asc: sort.key === key ? !sort.asc : false });
    setPage(0);
  }
  function exportCsv() {
    const cols = [
      "player_name",
      "team",
      "contract_tier",
      "salary",
      "war",
      "fair_value",
      "friction_tax",
      "net_surplus",
      "roi_multiple",
    ] as const;
    const csv = [
      cols.join(","),
      ...filtered.map((p) =>
        cols.map((k) => `"${String(p[k] ?? "").replaceAll('"', '""')}"`).join(","),
      ),
    ].join("\n");
    const url = URL.createObjectURL(
      new Blob([csv], { type: "text/csv;charset=utf-8;" }),
    );
    const a = document.createElement("a");
    a.href = url;
    a.download = "boardman-surplus-2025-26.csv";
    a.click();
    URL.revokeObjectURL(url);
  }
  const titles: Record<View, [string, string]> = {
    overview: [
      "The value beyond the contract.",
      "A clearer picture of player value. Built for the modern CBA.",
    ],
    players: [
      "Find the edge in every contract.",
      "Explore the league through the lens of net surplus value.",
    ],
    teams: [
      "Every dollar has a consequence.",
      "Track payroll commitments and the thresholds that change the game.",
    ],
    methodology: [
      "Good decisions start with clarity.",
      "An open model. Explicit assumptions. A more complete view of value.",
    ],
  };
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button
          className="brand-button"
          onClick={() => navigate("overview")}
          aria-label="Board Man home"
        >
          <Brand />
        </button>
        <div className="sidebar-season">
          <span className="status-dot" />
          2025–26 SEASON<span className="season-tag">NBA</span>
        </div>
        <div className="nav-caption">WORKSPACE</div>
        <nav aria-label="Main navigation">
          {nav.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${view === item.id ? "active" : ""}`}
              onClick={() => navigate(item.id)}
            >
              <item.icon size={18} />
              {item.label}
              {view === item.id && <span className="nav-dot" />}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="model-note">
            <span className="eyebrow">THE BOARD MAN MODEL</span>
            <p>
              Production is only
              <br />
              half the story.
            </p>
            <span>Price in the cost of constraints.</span>
            <button onClick={() => navigate("methodology")}>
              Explore the methodology <ArrowUpRight size={15} />
            </button>
          </div>
          <button
            className={`nav-item ${view === "methodology" ? "active" : ""}`}
            onClick={() => navigate("methodology")}
          >
            <BookOpen size={17} />
            Methodology
          </button>
          <div className="sidebar-footer">
            <span className="avatar">JK</span>
            <div>
              Built by Jace Kasen<span>Independent basketball research</span>
            </div>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            Workspace <ChevronRight size={13} />
            <span>
              {view === "methodology"
                ? "Methodology"
                : nav.find((n) => n.id === view)?.label}
            </span>
          </div>
          <div className="topbar-right">
            <span className="snapshot-label">
              <span className="status-dot" />
              2025–26 data snapshot
            </span>
            <button
              className="icon-button"
              aria-label="About the model"
              onClick={() => navigate("methodology")}
            >
              <CircleHelp size={18} />
            </button>
          </div>
        </header>
        <main>
          <div className="page-heading">
            <div>
              <div className="eyebrow">
                {view === "overview"
                  ? "THE FRONT OFFICE, RECONSIDERED"
                  : "BOARD MAN GETS PAID / " + view.toUpperCase()}
              </div>
              <h1>{titles[view][0]}</h1>
              <p>{titles[view][1]}</p>
            </div>
            {(view === "overview" || view === "players") && (
              <button
                className="button secondary export-button"
                onClick={exportCsv}
              >
                <ArrowDownToLine size={15} />
                Export board
              </button>
            )}
          </div>
          {view === "overview" && (
            <>
              <div className="metrics">
                <Metric
                  title="CONTRACTS ANALYZED"
                  value={String(active.length)}
                  note="Across all 30 NBA franchises"
                  icon="01"
                />
                <Metric
                  title="POSITIVE SURPLUS"
                  value={String(active.filter((p) => p.net_surplus > 0).length)}
                  note="Players producing above their cost"
                  icon="02"
                  positive
                />
                <Metric
                  title="ABOVE THE FIRST APRON"
                  value={String(
                    league.teams.filter((t) => t.bracket >= 2).length,
                  ).padStart(2, "0")}
                  note="Teams with restricted flexibility"
                  icon="03"
                />
                <Metric
                  title="OPEN-MARKET COST / WIN"
                  value={compact(league.costPerWin)}
                  note="Multi-season WAR calibration"
                  icon="04"
                />
              </div>
              <div className="overview-grid">
                <section className="panel chart-panel">
                  <div className="panel-heading">
                    <div>
                      <h2>The price of production</h2>
                      <p>Player salary vs. projected wins above replacement</p>
                    </div>
                    <span className="subtle-tag">LEAGUE VIEW</span>
                  </div>
                  <Scatter onSelect={setSelected} />
                  <div className="chart-legend">
                    <span>
                      <i className="legend-dot green" />
                      Positive surplus
                    </span>
                    <span>
                      <i className="legend-dot orange" />
                      Negative surplus
                    </span>
                    <span>
                      <i className="legend-line" />
                      Fair-value line
                    </span>
                  </div>
                </section>
                <section className="insight-panel">
                  <div className="eyebrow">
                    <span className="tiny-line" />
                    CONTRACT EFFICIENCY
                  </div>
                  <h2>
                    Maximum wins.
                    <br />
                    Minimum drag.
                  </h2>
                  <p>
                    Identifying surplus value anomalies: who outperforms their cap hit, and who anchors their franchise.
                  </p>
                  <div className="trade-mini">
                    <span>
                      <b>TOP BARGAIN</b>Victor Wembanyama
                    </span>
                    <ArrowRight size={17} />
                    <span>
                      <b>+$59.0M</b>Surplus
                    </span>
                  </div>
                  <div className="insight-value">
                    <span>LEAGUE SURPLUS LEADER</span>
                    <strong>
                      +$79.2<span>M</span>
                    </strong>
                    <small>Nikola Jokić (Denver Nuggets)</small>
                  </div>
                  <button
                    onClick={() => {
                      navigate("players");
                    }}
                  >
                    Explore surplus board <ArrowUpRight size={17} />
                  </button>
                </section>
              </div>
            </>
          )}
          {(view === "overview" || view === "players") && (
            <section className="panel board-panel">
              <div className="panel-heading">
                <div>
                  <h2>
                    League surplus board{" "}
                    <span className="count-tag">{active.length}</span>
                  </h2>
                  <p>The real return on a roster spot.</p>
                </div>
                {view === "overview" && (
                  <button
                    className="text-button"
                    onClick={() => navigate("players")}
                  >
                    View full board <ArrowRight size={15} />
                  </button>
                )}
              </div>
              <div className="table-toolbar">
                <label className="search-field">
                  <Search size={16} />
                  <input
                    aria-label="Search players"
                    placeholder="Search a player or team..."
                    value={query}
                    onChange={(e) => {
                      setQuery(e.target.value);
                      setPage(0);
                    }}
                  />
                  {query && (
                    <button
                      onClick={() => {
                        setQuery("");
                        setPage(0);
                      }}
                      aria-label="Clear search"
                    >
                      <X size={14} />
                    </button>
                  )}
                </label>
                <div className="table-filters">
                  <div className="mode-pills" role="radiogroup" aria-label="Arbitrage preset">
                    <button
                      className={`mode-pill ${mode === "all" ? "active" : ""}`}
                      onClick={() => {
                        setMode("all");
                        setSort({ key: "net_surplus", asc: false });
                        setPage(0);
                      }}
                    >
                      All
                    </button>
                    <button
                      className={`mode-pill ${mode === "bargains" ? "active" : ""}`}
                      onClick={() => {
                        setMode("bargains");
                        setSort({ key: "net_surplus", asc: false });
                        setPage(0);
                      }}
                    >
                      Top Bargains
                    </button>
                    <button
                      className={`mode-pill ${mode === "anchors" ? "active" : ""}`}
                      onClick={() => {
                        setMode("anchors");
                        setSort({ key: "net_surplus", asc: true });
                        setPage(0);
                      }}
                    >
                      Top Anchors
                    </button>
                    <button
                      className={`mode-pill ${mode === "roi" ? "active" : ""}`}
                      onClick={() => {
                        setMode("roi");
                        setSort({ key: "roi_multiple", asc: false });
                        setPage(0);
                      }}
                    >
                      Highest ROI
                    </button>
                  </div>
                  <select
                    aria-label="Filter by contract tier"
                    value={tier}
                    onChange={(e) => {
                      setTier(e.target.value);
                      setPage(0);
                    }}
                  >
                    <option value="all">All contract tiers</option>
                    <option value="Rookie Scale">Rookie Scale</option>
                    <option value="Max / Supermax">Max / Supermax</option>
                    <option value="Mid-Level">Mid-Level</option>
                    <option value="Minimum / Rotation">Minimum / Rotation</option>
                    <option value="Two-Way / Unknown">Two-Way / Unknown</option>
                  </select>
                  <select
                    aria-label="Filter by team"
                    value={team}
                    onChange={(e) => {
                      setTeam(e.target.value);
                      setPage(0);
                    }}
                  >
                    <option value="all">All teams</option>
                    {league.teams
                      .toSorted((a, b) => a.name.localeCompare(b.name))
                      .map((t) => (
                        <option key={t.team} value={t.team}>
                          {t.name}
                        </option>
                      ))}
                  </select>
                </div>
              </div>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th className="rank">#</th>
                      <th>PLAYER</th>
                      <th>TEAM</th>
                      <th>TIER</th>
                      {(
                        [
                          ["salary", "SALARY"],
                          ["war", "PROJ. WAR"],
                          ["fair_value", "PRODUCTION"],
                          ["net_surplus", "NET SURPLUS"],
                          ["roi_multiple", "ROI MULTIPLE"],
                        ] as const
                      ).map(([key, label]) => (
                        <th
                          key={key}
                          className="numeric"
                          aria-sort={
                            sort.key === key
                              ? sort.asc
                                ? "ascending"
                                : "descending"
                              : "none"
                          }
                        >
                          <button onClick={() => sortBy(key)}>
                            {label}
                            {sort.key === key && (
                              <ArrowDown
                                size={12}
                                style={{
                                  transform: sort.asc
                                    ? "rotate(180deg)"
                                    : undefined,
                                }}
                              />
                            )}
                          </button>
                        </th>
                      ))}
                      <th>
                        <span className="sr-only">Details</span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {shown.map((p, i) => (
                      <tr key={`${p.team}-${p.player_id}`}>
                        <td className="rank">
                          {String(page * pageSize + i + 1).padStart(2, "0")}
                        </td>
                        <td>
                          <button
                            className="player-button"
                            onClick={() => setSelected(p)}
                          >
                            <span className={`player-avatar tint-${i % 4}`}>
                              {initials(p.player_name)}
                            </span>
                            <span>{p.player_name}</span>
                          </button>
                        </td>
                        <td>
                          <span className="team-pill">{p.team}</span>
                        </td>
                        <td>
                          <span
                            className={`tier-badge tier-${(p.contract_tier || "Standard")
                              .toLowerCase()
                              .replace(/[^a-z0-9]/g, "-")}`}
                          >
                            {p.contract_tier}
                          </span>
                        </td>
                        <td className="numeric">
                          {p.is_salary_known ? (
                            money(p.salary)
                          ) : (
                            <span className="muted" title="Two-way or non-guaranteed salary unverified in cap ledger">
                              Two-Way / ~0
                            </span>
                          )}
                        </td>
                        <td className="numeric">{p.war.toFixed(2)}</td>
                        <td className="numeric">{money(p.fair_value)}</td>
                        <td
                          className={`numeric surplus ${p.net_surplus >= 0 ? "positive" : "negative"}`}
                        >
                          {money(p.net_surplus, true)}
                        </td>
                        <td className="numeric">
                          {p.roi_multiple !== null && p.roi_multiple !== undefined ? (
                            <strong className={p.roi_multiple >= 1.0 ? "positive" : "negative"}>
                              {p.roi_multiple.toFixed(2)}x
                            </strong>
                          ) : (
                            <span className="muted">—</span>
                          )}
                        </td>
                        <td>
                          <button
                            className="icon-button row-arrow"
                            aria-label={`View ${p.player_name}`}
                            onClick={() => setSelected(p)}
                          >
                            <ArrowUpRight size={15} />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {!shown.length && (
                  <div className="empty-state">
                    <Search size={26} />
                    <h3>No players found</h3>
                    <p>
                      Try another name or adjust your team and tier filters.
                    </p>
                    <button
                      className="text-button"
                      onClick={() => {
                        setQuery("");
                        setTeam("all");
                        setTier("all");
                        setMode("all");
                        setSort({ key: "net_surplus", asc: false });
                      }}
                    >
                      Reset filters
                    </button>
                  </div>
                )}
              </div>
              <div className="table-footer">
                <span>
                  {filtered.length
                    ? `${page * pageSize + 1}–${Math.min((page + 1) * pageSize, filtered.length)} of ${filtered.length} contracts`
                    : "0 contracts"}
                </span>
                <span className="table-footnote">
                  Multi-season WAR · Net of apron friction
                </span>
                <div className="pagination">
                  <button
                    className="icon-button"
                    aria-label="Previous page"
                    disabled={page === 0}
                    onClick={() => setPage(page - 1)}
                  >
                    <ChevronLeft size={16} />
                  </button>
                  <button
                    className="icon-button"
                    aria-label="Next page"
                    disabled={(page + 1) * pageSize >= filtered.length}
                    onClick={() => setPage(page + 1)}
                  >
                    <ChevronRight size={16} />
                  </button>
                </div>
              </div>
            </section>
          )}
          {view === "teams" && (
            <>
              <div className="threshold-grid">
                {Object.entries(league.thresholds).map(([key, v], i) => (
                  <Metric
                    key={key}
                    title={
                      [
                        "SALARY CAP",
                        "LUXURY TAX",
                        "FIRST APRON",
                        "SECOND APRON",
                      ][i]
                    }
                    value={compact(v)}
                    note="2025–26 threshold"
                    icon={`0${i + 1}`}
                  />
                ))}
              </div>
              <section className="panel">
                <div className="panel-heading">
                  <div>
                    <h2>The payroll landscape</h2>
                    <p>
                      All 30 franchises, ordered by committed salary. Select a
                      team to explore its contracts.
                    </p>
                  </div>
                </div>
                <div className="team-list">
                  {league.teams.map((t) => (
                    <button
                      className="team-row"
                      key={t.team}
                      onClick={() => {
                        setTeam(t.team);
                        setQuery("");
                        setTier("all");
                        setMode("all");
                        navigate("players");
                      }}
                    >
                      <span className="team-pill">{t.team}</span>
                      <span className="team-name">{t.name}</span>
                      <span className="payroll-bar">
                        <span
                          style={{
                            width: `${(t.total_payroll / 230e6) * 100}%`,
                          }}
                          className={`bracket-${t.bracket}`}
                        />
                        <i
                          style={{
                            left: `${(league.thresholds.second / 230e6) * 100}%`,
                          }}
                        />
                      </span>
                      <strong>{compact(t.total_payroll)}</strong>
                      <span
                        className={`bracket-label bracket-text-${t.bracket}`}
                      >
                        {brackets[t.bracket]}
                      </span>
                      <ArrowUpRight size={15} />
                    </button>
                  ))}
                </div>
              </section>
            </>
          )}
          {view === "methodology" && <Methodology />}
          <footer className="page-footer">
            <span>
              <span className="footer-mark">B.</span>Basketball is a game of
              margins.
            </span>
            <span>
              2025–26 dataset <span className="footer-divider">/</span>{" "}
              Independent research, open by design
            </span>
          </footer>
        </main>
      </div>
      {selected && (
        <PlayerModal onClose={() => setSelected(null)}>
          <section className="player-detail">
            <button
              className="icon-button close-dialog"
              onClick={() => setSelected(null)}
              aria-label="Close player details"
              autoFocus
            >
              <X size={20} />
            </button>
            <span className="eyebrow">CONTRACT PROFILE / {selected.team}</span>
            <div className="detail-avatar">
              {initials(selected.player_name)}
            </div>
            <h2 id="player-title">{selected.player_name}</h2>
            <p>
              {league.teams.find((t) => t.team === selected.team)?.name} ·{" "}
              {league.season}
            </p>
            <div className="detail-value">
              <span>NET SURPLUS VALUE</span>
              <strong
                className={selected.net_surplus >= 0 ? "positive" : "negative"}
              >
                {money(selected.net_surplus, true)}
              </strong>
            </div>
            <dl>
              {[
                ["Contract tier", selected.contract_tier],
                [
                  "Salary allocation",
                  selected.is_salary_known
                    ? money(selected.salary)
                    : "Two-Way / Unverified",
                ],
                ["Projected WAR", selected.war.toFixed(2)],
                ["Fair production value", money(selected.fair_value)],
                ["Gross surplus", money(selected.gross_surplus, true)],
                ["Apron friction drag", money(selected.friction_tax)],
                [
                  "ROI efficiency multiple",
                  selected.roi_multiple !== null && selected.roi_multiple !== undefined
                    ? `${selected.roi_multiple.toFixed(2)}x`
                    : "N/A",
                ],
                ["Team payroll bracket", brackets[selected.bracket]],
              ].map(([k, v]) => (
                <div key={k}>
                  <dt>{k}</dt>
                  <dd>{v}</dd>
                </div>
              ))}
            </dl>
            <p className="detail-note">
              Net surplus = production value − salary − apron friction.
              Estimates use the multi-season talent baseline.
            </p>
            <button
              className="button primary"
              onClick={() => {
                setTeam(selected.team);
                setQuery("");
                setTier("all");
                setMode("all");
                setSelected(null);
                navigate("players");
              }}
            >
              Explore team contracts <ArrowRight size={15} />
            </button>
          </section>
        </PlayerModal>
      )}
    </div>
  );
}

function Metric({
  title,
  value,
  note,
  icon,
  positive = false,
}: {
  title: string;
  value: string;
  note: string;
  icon: string;
  positive?: boolean;
}) {
  return (
    <section className="metric">
      <div className="metric-top">
        <span>{title}</span>
        <span className="metric-number">{icon}</span>
      </div>
      <strong>
        {value}
        {positive && (
          <span className="metric-indicator">
            <ArrowUpRight size={20} />
          </span>
        )}
      </strong>
      <p>{note}</p>
    </section>
  );
}

function Scatter({ onSelect }: { onSelect: (p: Player) => void }) {
  const [hover, setHover] = useState<Player | null>(null);
  const x = (salary: number) => 54 + (salary / 65e6) * 565;
  const y = (war: number) => 245 - ((war + 3) / 31) * 221;
  return (
    <div className="scatter-wrap">
      <svg
        className="scatter"
        viewBox="0 0 660 292"
        role="img"
        aria-label="Scatter plot of player salaries against projected wins. Green points have positive net surplus, terracotta points have negative surplus."
      >
        <text x="16" y="15" className="axis-title">
          PROJ. WAR
        </text>
        {[0, 5, 10, 15, 20, 25].map((n) => (
          <g key={n}>
            <line x1="54" x2="627" y1={y(n)} y2={y(n)} className="grid-line" />
            <text x="35" y={y(n) + 4} textAnchor="end">
              {n}
            </text>
          </g>
        ))}
        {[0, 10, 20, 30, 40, 50, 60].map((n) => (
          <text key={n} x={x(n * 1e6)} y="267" textAnchor="middle">
            ${n}M
          </text>
        ))}
        <line
          x1={x(0)}
          y1={y(0)}
          x2={x(65e6)}
          y2={y(65e6 / league.costPerWin)}
          className="fair-line"
        />
        {active.map((p) => (
          <circle
            key={`${p.team}-${p.player_id}`}
            cx={x(p.salary)}
            cy={y(p.war)}
            r={p.salary > 40e6 ? 4.6 : 3.4}
            className={`scatter-dot ${p.net_surplus > 0 ? "dot-positive" : "dot-negative"}`}
            onMouseEnter={() => setHover(p)}
            onMouseLeave={() => setHover(null)}
            onClick={() => onSelect(p)}
          >
            <title>
              {`${p.player_name}: ${money(p.salary)}, ${p.war} WAR, ${money(p.net_surplus, true)} surplus`}
            </title>
          </circle>
        ))}
        {active.slice(0, 2).map((p, i) => (
          <text
            className="point-label"
            key={p.player_id}
            x={x(p.salary) - 10}
            y={y(p.war) - (i ? 14 : 12)}
            textAnchor="end"
          >
            {p.player_name}
          </text>
        ))}
        <text x="627" y="289" textAnchor="end" className="axis-title">
          ANNUAL SALARY
        </text>
      </svg>
      {hover && (
        <div className="chart-tooltip">
          {hover.player_name}
          <strong>{money(hover.net_surplus, true)} surplus</strong>
        </div>
      )}
    </div>
  );
}

function Methodology() {
  return (
    <div className="methodology">
      <section className="formula-panel">
        <span className="eyebrow">THE CORE IDEA</span>
        <h2>
          What a player creates.
          <br />
          What a contract costs.
          <br />
          <em>What constraints take away.</em>
        </h2>
        <div className="formula">
          Net surplus <span>=</span> Production value <span>−</span> Salary{" "}
          <span>−</span> Apron friction
        </div>
      </section>
      <div className="method-grid">
        {[
          {
            n: "01",
            title: "Start with production",
            text: `A multi-season WAR baseline estimates player talent. Each projected win is valued at ${money(league.costPerWin)}, calibrated from unconstrained veteran contracts.`,
          },
          {
            n: "02",
            title: "Account for the contract",
            text: "Subtract the player’s cap hit from fair production value to calculate gross surplus. A useful first step, but it does not capture a team’s ability to operate.",
          },
          {
            n: "03",
            title: "Price the constraints",
            text: "Friction equals λ × salary × (salary / cap). The model uses λ of 0, 0.15, 0.35, and 0.70 as payroll moves from below the tax to above the second apron.",
          },
          {
            n: "04",
            title: "See the whole roster",
            text: "A trade changes more than two contracts. Crossing an apron can change friction for the entire roster. The trade lab recalculates both teams before and after a deal.",
          },
        ].map((m) => (
          <section className="panel method-card" key={m.n}>
            <span className="eyebrow">{m.n}</span>
            <h3>{m.title}</h3>
            <p>{m.text}</p>
          </section>
        ))}
      </div>
      <section className="panel limitations">
        <h2>A model, with its assumptions in view.</h2>
        <p>
          These are estimates for the repository’s 2025–26 dataset, not live
          roster data or forecasts of transaction acceptance. Friction
          multipliers are scenario assumptions, not empirically identified
          prices. Public box-score metrics cannot fully capture fit, health,
          development, or playoff value.
        </p>
        <p>
          The trade engine checks its implemented salary-matching and apron
          rules. Draft compensation, team-specific exceptions, and every
          contractual restriction are not comprehensively modelled. The surplus
          board excludes dead-money contracts; team payroll and trade valuation
          retain the engine’s full roster context.
        </p>
      </section>
    </div>
  );
}

function PlayerModal({
  children,
  onClose,
}: {
  children: React.ReactNode;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    dialog?.showModal();
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      dialog?.close();
      document.body.style.overflow = previous;
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className="player-dialog"
      aria-labelledby="player-title"
      onCancel={onClose}
    >
      <div className="dialog-backdrop" onClick={onClose} />
      {children}
    </dialog>
  );
}
