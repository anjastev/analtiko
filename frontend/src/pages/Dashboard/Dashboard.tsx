import {
  useEffect,
  useState,
} from "react";

import {
  Link,
} from "react-router-dom";

import {
  ArrowRight,
  Bot,
  CalendarDays,
  CircleDollarSign,
  Database,
  ListChecks,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";

import {
  getDashboard,
  getOptimizedTickets,
} from "../../services/api";

import OptimizedTicketCard
  from "../../components/tickets/OptimizedTicketCard";

import type {
  DashboardPayload,
  OptimizedTicket,
} from "../../types/intelligence";


function Dashboard() {

  const [
    data,
    setData,
  ] = useState<DashboardPayload | null>(
    null
  );


  const [
    optimizedTickets,
    setOptimizedTickets,
  ] = useState<OptimizedTicket[]>(
    []
  );


  const [
    loading,
    setLoading,
  ] = useState(true);


  const [
    error,
    setError,
  ] = useState("");


  // ============================================================
  // LOAD DASHBOARD
  // ============================================================

  useEffect(() => {

    async function load() {

      try {

        setLoading(true);
        setError("");


        const [
          dashboardResult,
          ticketsResult,
        ] = await Promise.all([
          getDashboard(),
          getOptimizedTickets(1),
        ]);


        setData(
          dashboardResult
        );


        setOptimizedTickets(
          ticketsResult.tickets
        );

      } catch (err) {

        console.error(
          "Dashboard error:",
          err
        );


        setError(
          "Could not load production dashboard."
        );

      } finally {

        setLoading(false);

      }
    }


    load();

  }, []);


  // ============================================================
  // LOADING
  // ============================================================

  if (loading) {

    return (
      <div className="page">

        <div className="dashboard-loading">

          <div className="dashboard-loader" />

          <p>
            Loading Analitiko intelligence...
          </p>

        </div>

      </div>
    );
  }


  // ============================================================
  // ERROR
  // ============================================================

  if (
    error
    || !data
  ) {

    return (
      <div className="page">

        <div className="frontend-alert frontend-alert--error">

          <strong>
            Dashboard unavailable
          </strong>

          <span>
            {
              error
              || "No dashboard data."
            }
          </span>

        </div>

      </div>
    );
  }


  const {
    health,
    upcoming_matches,
    value_signals,
  } = data;


  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div className="page analitiko-dashboard">

      {/* =====================================================
          HERO
      ====================================================== */}

      <header className="dashboard-product-hero">

        <div className="dashboard-product-hero__content">

          <div className="dashboard-live-label">

            <span className="dashboard-live-dot" />

            ANALITIKO LIVE

          </div>


          <h1>
            Today's Football
            <span> Intelligence</span>
          </h1>


          <p>
            Live football analysis, VALUE
            opportunities and optimized tickets
            built from model probabilities,
            market prices and production
            quality controls.
          </p>


          <div className="dashboard-hero-actions">

            <Link
              to="/tickets"
              className="primary-action"
            >

              <ListChecks size={18} />

              View Today's Tickets

            </Link>


            <Link
              to="/ticket-builder"
              className="secondary-action"
            >

              <Sparkles size={18} />

              Build a Ticket

            </Link>

          </div>

        </div>


        {/* =================================================
            ENGINE STATUS
        ================================================== */}

        <div className="dashboard-product-hero__status">

          <div className="hero-status-top">

            <ShieldCheck size={21} />

            <span>
              Production Engine
            </span>

          </div>


          <strong>
            {health.status}
          </strong>


          <div className="hero-coverage">

            <div>

              <span>
                Ready coverage
              </span>

              <strong>
                {
                  health
                    .production_coverage
                    .toFixed(1)
                }%
              </strong>

            </div>


            <div className="hero-coverage-track">

              <div
                className="hero-coverage-fill"
                style={{
                  width:
                    `${Math.min(
                      health.production_coverage,
                      100
                    )}%`,
                }}
              />

            </div>

          </div>

        </div>

      </header>


      {/* =====================================================
          KPI
      ====================================================== */}

      <section className="dashboard-kpi-grid">

        <DashboardKpi
          icon={CalendarDays}
          label="Upcoming"
          value={
            health.upcoming_matches
          }
          helper="Tracked matches"
        />


        <DashboardKpi
          icon={ShieldCheck}
          label="Production Ready"
          value={
            health.production_ready_matches
          }
          helper={
            `${health.production_coverage.toFixed(1)}% coverage`
          }
          highlight
        />


        <DashboardKpi
          icon={Target}
          label="Active Signals"
          value={
            health.active_signals
          }
          helper="Validated candidates"
        />


        <DashboardKpi
          icon={CircleDollarSign}
          label="VALUE"
          value={
            health.value_signals
          }
          helper="Qualified market value"
          valueHighlight
        />


        <DashboardKpi
          icon={Database}
          label="Fresh Odds"
          value={
            health.fresh_odds_rows
          }
          helper="Market prices"
        />

      </section>


      {/* =====================================================
          OPTIMIZED TICKETS
      ====================================================== */}

      <section className="dashboard-primary-section">

        <div className="dashboard-section-heading">

          <div>

            <p className="section-label">
              Production optimizer
            </p>

            <h2>
              Today's Optimized Tickets
            </h2>

            <span>
              SAFE, BALANCED and AGGRESSIVE
              combinations generated from
              production-qualified signals.
            </span>

          </div>


          <Link
            to="/tickets"
            className="dashboard-view-all"
          >

            All tickets

            <ArrowRight size={16} />

          </Link>

        </div>


        {optimizedTickets.length > 0
          ? (

            <div className="optimized-ticket-grid">

              {optimizedTickets.map(
                (ticket) => (

                  <OptimizedTicketCard
                    key={
                      ticket.strategy
                    }
                    ticket={
                      ticket
                    }
                  />

                )
              )}

            </div>

          )
          : (

            <div className="dashboard-no-ticket">

              <div className="dashboard-no-ticket__icon">

                <ListChecks size={27} />

              </div>


              <div>

                <h3>
                  No optimized tickets available
                </h3>

                <p>
                  The production optimizer did not
                  find enough qualified selections
                  for the current window.
                </p>

              </div>


              <Link
                to="/ticket-builder"
              >

                Build custom ticket

                <ArrowRight size={15} />

              </Link>

            </div>

          )
        }

      </section>


      {/* =====================================================
          VALUE + AI
      ====================================================== */}

      <div className="dashboard-intelligence-grid">

        {/* =================================================
            VALUE SIGNALS
        ================================================== */}

        <section className="dashboard-primary-section">

          <div className="dashboard-section-heading">

            <div>

              <p className="section-label">
                Market intelligence
              </p>

              <h2>
                Live VALUE Opportunities
              </h2>

              <span>
                Current production signals with
                qualified market value.
              </span>

            </div>


            <Link
              to="/value-analytics"
              className="dashboard-view-all"
            >

              View all

              <ArrowRight size={15} />

            </Link>

          </div>


          <div className="dashboard-value-list">

            {value_signals
              .slice(
                0,
                5
              )
              .map(
                (signal) => (

                  <Link
                    to={
                      `/matches/${signal.match_id}`
                    }
                    key={
                      signal.id
                    }
                    className="dashboard-value-row"
                  >

                    {/* MARKET */}

                    <div className="dashboard-value-market">

                      <span>
                        {
                          signal.market_code
                          ?? "MARKET"
                        }
                      </span>

                      <strong>
                        {
                          signal.selection
                        }
                      </strong>

                    </div>


                    {/* MODEL */}

                    <div className="dashboard-value-probability">

                      <span>
                        Model
                      </span>

                      <strong>
                        {
                          signal
                            .model_probability
                            .toFixed(1)
                        }%
                      </strong>

                    </div>


                    {/* EDGE */}

                    <div className="dashboard-value-edge">

                      <span>
                        Edge
                      </span>

                      <strong>
                        {
                          signal.edge
                          !== null
                            ? `${signal.edge >= 0 ? "+" : ""}${signal.edge.toFixed(1)}%`
                            : "—"
                        }
                      </strong>

                    </div>


                    {/* ODDS */}

                    <div className="dashboard-value-odds">

                      <span>
                        Odds
                      </span>

                      <strong>
                        {
                          signal.odds
                            ?.toFixed(2)
                          ?? "—"
                        }
                      </strong>

                    </div>


                    <ArrowRight size={16} />

                  </Link>

                )
              )
            }


            {value_signals.length === 0 && (

              <div className="dashboard-mini-empty">

                No current VALUE opportunities.

              </div>

            )}

          </div>

        </section>


        {/* =================================================
            AI BUILDER
        ================================================== */}

        <section className="dashboard-ai-card">

          <div className="dashboard-ai-icon">

            <Bot size={26} />

          </div>


          <p className="section-label">
            Conversational intelligence
          </p>


          <h2>
            Ask Analitiko
          </h2>


          <p>
            Choose the leagues, day, number of
            selections, risk profile or target
            odds. Analitiko will search only
            production-qualified opportunities.
          </p>


          <div className="dashboard-ai-example">

            <Sparkles size={17} />

            <span>
              “Build me a SAFE ticket for tomorrow,
              3 selections, minimum 75% probability,
              around 2.50 total odds.”
            </span>

          </div>


          <Link
            to="/ticket-builder"
            className="dashboard-ai-button"
          >

            Open AI Ticket Builder

            <ArrowRight size={17} />

          </Link>

        </section>

      </div>


      {/* =====================================================
          UPCOMING MATCHES
      ====================================================== */}

      <section className="dashboard-primary-section">

        <div className="dashboard-section-heading">

          <div>

            <p className="section-label">
              Football schedule
            </p>

            <h2>
              Upcoming Matches
            </h2>

            <span>
              Current tracked fixtures and
              production data readiness.
            </span>

          </div>


          <Link
            to="/matches"
            className="dashboard-view-all"
          >

            All matches

            <ArrowRight size={15} />

          </Link>

        </div>


        <div className="production-match-list">

          {upcoming_matches
            .slice(
              0,
              7
            )
            .map(
              (match) => (

                <Link
                  to={
                    `/matches/${match.id}`
                  }
                  key={
                    match.id
                  }
                  className="production-match-row"
                >

                  {/* TIME */}

                  <div className="production-match-time">

                    <strong>
                      {
                        match.match_date
                          ? new Date(
                              match.match_date
                            ).toLocaleTimeString(
                              [],
                              {
                                hour:
                                  "2-digit",

                                minute:
                                  "2-digit",
                              }
                            )
                          : "—"
                      }
                    </strong>


                    <span>
                      {
                        match.match_date
                          ? new Date(
                              match.match_date
                            ).toLocaleDateString()
                          : ""
                      }
                    </span>

                  </div>


                  {/* TEAMS */}

                  <div className="production-match-teams">

                    <strong>
                      {
                        match.home_team.name
                      }
                    </strong>

                    <span>
                      vs
                    </span>

                    <strong>
                      {
                        match.away_team.name
                      }
                    </strong>

                  </div>


                  {/* DATA STATUS */}

                  <div>

                    <span
                      className={
                        match.production_ready
                          ? "data-badge data-badge--ready"
                          : "data-badge data-badge--partial"
                      }
                    >

                      {
                        match.production_ready
                          ? "READY"
                          : match.data_quality
                      }

                    </span>

                  </div>


                  <ArrowRight
                    size={16}
                    className="production-match-arrow"
                  />

                </Link>

              )
            )
          }


          {upcoming_matches.length === 0 && (

            <div className="dashboard-mini-empty">

              No upcoming tracked matches.

            </div>

          )}

        </div>

      </section>


      {/* =====================================================
          QUICK NAVIGATION
      ====================================================== */}

      <section className="dashboard-quick-grid">

        <QuickCard
          to="/predictions"
          icon={Target}
          title="Predictions"
          description={
            "Explore model probabilities "
            + "and validated signals."
          }
        />


        <QuickCard
          to="/trending"
          icon={TrendingUp}
          title="Trending"
          description={
            "Discover the strongest "
            + "current football activity."
          }
        />


        <QuickCard
          to="/analytics"
          icon={Database}
          title="Analytics"
          description={
            "Review model and market "
            + "performance."
          }
        />


        <QuickCard
          to="/performance"
          icon={ShieldCheck}
          title="Performance"
          description={
            "Track prospective hit rate, "
            + "profit and ROI."
          }
        />

      </section>

    </div>
  );
}


/* ============================================================
   KPI
============================================================ */

interface DashboardKpiProps {

  icon:
    React.ElementType;

  label:
    string;

  value:
    string | number;

  helper:
    string;

  highlight?:
    boolean;

  valueHighlight?:
    boolean;
}


function DashboardKpi({
  icon: Icon,
  label,
  value,
  helper,
  highlight = false,
  valueHighlight = false,
}: DashboardKpiProps) {

  return (
    <article
      className={
        `dashboard-kpi ${
          highlight
            ? "dashboard-kpi--highlight"
            : ""
        }`
      }
    >

      <div className="dashboard-kpi__top">

        <span>
          {label}
        </span>

        <Icon size={17} />

      </div>


      <strong
        className={
          valueHighlight
            ? "dashboard-kpi__value--green"
            : ""
        }
      >

        {value}

      </strong>


      <small>
        {helper}
      </small>

    </article>
  );
}


/* ============================================================
   QUICK CARD
============================================================ */

interface QuickCardProps {

  to:
    string;

  icon:
    React.ElementType;

  title:
    string;

  description:
    string;
}


function QuickCard({
  to,
  icon: Icon,
  title,
  description,
}: QuickCardProps) {

  return (
    <Link
      to={to}
      className="dashboard-quick-card"
    >

      <div>

        <Icon size={19} />

      </div>


      <strong>
        {title}
      </strong>


      <span>
        {description}
      </span>


      <ArrowRight size={16} />

    </Link>
  );
}


export default Dashboard;