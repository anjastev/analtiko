import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Link,
} from "react-router-dom";

import api from "../../services/api";

import type {
  ValueAnalyticsGroup,
  ValueAnalyticsRecentItem,
  ValueAnalyticsResponse,
} from "../../types/valueAnalytics";


function formatPercent(
  value: number | null
) {
  if (value === null) {
    return "-";
  }

  return `${value.toFixed(1)}%`;
}


function formatSignedPercent(
  value: number | null
) {
  if (value === null) {
    return "-";
  }

  const prefix =
    value > 0
      ? "+"
      : "";

  return `${prefix}${value.toFixed(1)}%`;
}


function formatUnits(
  value: number
) {
  const prefix =
    value > 0
      ? "+"
      : "";

  return `${prefix}${value.toFixed(2)}u`;
}


function formatDate(
  value: string
) {
  const date = new Date(
    value
  );

  if (
    Number.isNaN(
      date.getTime()
    )
  ) {
    return value;
  }

  return date.toLocaleString();
}


function ValueAnalytics() {

  const [
    analytics,
    setAnalytics,
  ] =
    useState<ValueAnalyticsResponse | null>(
      null
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    error,
    setError,
  ] =
    useState("");


  // ==========================================================
  // LOAD
  // ==========================================================

  useEffect(() => {

    async function loadAnalytics() {

      try {

        setLoading(
          true
        );

        setError(
          ""
        );

        const response =
          await api.get<ValueAnalyticsResponse>(
            "/api/value-analytics/performance"
          );

        setAnalytics(
          response.data
        );

      } catch (err) {

        console.error(
          "Failed to load VALUE analytics:",
          err
        );

        setError(
          "Could not load VALUE analytics."
        );

      } finally {

        setLoading(
          false
        );
      }
    }

    loadAnalytics();

  }, []);


  // ==========================================================
  // DERIVED DATA
  // ==========================================================

  const pending =
    useMemo(
      () => {

        if (!analytics) {
          return [];
        }

        return analytics.recent.filter(
          (item) =>
            item.correct === null
        );

      },
      [analytics]
    );


  const evaluated =
    useMemo(
      () => {

        if (!analytics) {
          return [];
        }

        return analytics.recent.filter(
          (item) =>
            item.correct !== null
        );

      },
      [analytics]
    );


  const elitePending =
    useMemo(
      () =>
        pending.filter(
          (item) =>
            item.is_elite_value
        ),
      [pending]
    );


  // ==========================================================
  // LOADING
  // ==========================================================

  if (loading) {

    return (
      <div className="page">

        <p>
          Loading VALUE analytics...
        </p>

      </div>
    );
  }


  // ==========================================================
  // ERROR
  // ==========================================================

  if (
    error
    || !analytics
  ) {

    return (
      <div className="page">

        <p>
          {
            error
            || "VALUE analytics unavailable."
          }
        </p>

      </div>
    );
  }


  const summary =
    analytics.summary;

  const value =
    analytics.value;

  const elite =
    analytics.elite_value;

  const consensus =
    analytics.model_consensus;


  // ==========================================================
  // JSX
  // ==========================================================

  return (
    <div className="page value-analytics-page">

      {/* =====================================================
          HEADER
      ====================================================== */}

      <div className="page-header">

        <div>

          <p className="eyebrow">
            Market Intelligence
          </p>

          <h1>
            VALUE Analytics
          </h1>

          <p className="page-subtitle">
            Prospective performance tracking for
            frozen ML probabilities versus market odds.
          </p>

        </div>


        <div className="value-research-status">

          <span>
            RESEARCH
          </span>

          <strong>
            Frozen ML v2
          </strong>

        </div>

      </div>


      {/* =====================================================
          THRESHOLDS
      ====================================================== */}

      <section className="value-threshold-strip">

        <div>

          <span>
            VALUE
          </span>

          <strong>
            Edge ≥ {
              analytics
                .thresholds
                .value_edge
                .toFixed(1)
            }%
          </strong>

        </div>


        <div>

          <span>
            ELITE VALUE
          </span>

          <strong>
            ELITE + Edge ≥ {
              analytics
                .thresholds
                .elite_value_edge
                .toFixed(1)
            }%
          </strong>

        </div>


        <div>

          <span>
            Model
          </span>

          <strong>
            {analytics.model}
          </strong>

        </div>

      </section>


      {/* =====================================================
          MAIN KPI
      ====================================================== */}

      <div className="stats-grid">

        <AnalyticsStatCard
          label="VALUE Snapshots"
          value={
            summary.total
          }
          helper="Saved pre-match signals"
        />

        <AnalyticsStatCard
          label="Pending"
          value={
            summary.pending
          }
          helper="Waiting for result"
        />

        <AnalyticsStatCard
          label="Evaluated"
          value={
            summary.evaluated
          }
          helper="Prospectively evaluated"
        />

        <AnalyticsStatCard
          label="Accuracy"
          value={
            formatPercent(
              summary.accuracy
            )
          }
          helper="All evaluated VALUE picks"
        />

        <AnalyticsStatCard
          label="Profit"
          value={
            formatUnits(
              summary.profit
            )
          }
          helper="1 unit flat stake"
        />

        <AnalyticsStatCard
          label="ROI"
          value={
            formatSignedPercent(
              summary.roi
            )
          }
          helper="Flat-stake prospective ROI"
        />

      </div>


      {/* =====================================================
          SIGNAL PERFORMANCE
      ====================================================== */}

      <section className="dashboard-section">

        <div className="section-header">

          <div>

            <p className="section-label">
              Prospective Performance
            </p>

            <h2>
              Signal Groups
            </h2>

          </div>

        </div>


        <div className="value-signal-grid">

          <ValueGroupCard
            title="All VALUE"
            subtitle={
              `Edge ≥ ${analytics.thresholds.value_edge}%`
            }
            data={
              value
            }
          />


          <ValueGroupCard
            title="ELITE VALUE"
            subtitle={
              `ELITE + edge ≥ ${analytics.thresholds.elite_value_edge}%`
            }
            data={
              elite
            }
            elite
          />


          <ValueGroupCard
            title="ML Consensus"
            subtitle="VALUE side equals frozen ML pick"
            data={
              consensus
            }
          />

        </div>

      </section>


      {/* =====================================================
          CURRENT LIVE SIGNALS
      ====================================================== */}

      <section className="dashboard-section">

        <div className="section-header">

          <div>

            <p className="section-label">
              Live Market
            </p>

            <h2>
              Current VALUE Signals
            </h2>

            <p className="value-section-helper">
              Frozen pre-match snapshots waiting
              for a final result.
            </p>

          </div>

        </div>


        {pending.length > 0
          ? (

            <div className="value-live-grid">

              {
                pending.map(
                  (item) => (

                    <ValueSignalCard
                      key={
                        item.id
                      }
                      item={
                        item
                      }
                    />

                  )
                )
              }

            </div>

          )
          : (

            <p className="empty-state">
              No pending VALUE signals.
            </p>

          )
        }

      </section>


      {/* =====================================================
          ELITE VALUE
      ====================================================== */}

      <section className="dashboard-section value-elite-section">

        <div className="section-header">

          <div>

            <p className="section-label">
              Highest Signal
            </p>

            <h2>
              ELITE VALUE
            </h2>

            <p className="value-section-helper">
              ML ELITE signal combined with
              a qualifying market edge.
            </p>

          </div>

        </div>


        {elitePending.length > 0
          ? (

            <div className="value-live-grid">

              {
                elitePending.map(
                  (item) => (

                    <ValueSignalCard
                      key={
                        item.id
                      }
                      item={
                        item
                      }
                    />

                  )
                )
              }

            </div>

          )
          : (

            <p className="empty-state">
              No pending ELITE VALUE signals.
            </p>

          )
        }

      </section>


      {/* =====================================================
          RECENT RESULTS
      ====================================================== */}

      <section className="dashboard-section">

        <div className="section-header">

          <div>

            <p className="section-label">
              Prospective Tracking
            </p>

            <h2>
              VALUE Results
            </h2>

          </div>

        </div>


        {evaluated.length > 0
          ? (

            <div className="value-results-list">

              {
                evaluated.map(
                  (item) => (

                    <ValueResultCard
                      key={
                        item.id
                      }
                      item={
                        item
                      }
                    />

                  )
                )
              }

            </div>

          )
          : (

            <p className="empty-state">
              No evaluated VALUE predictions yet.
            </p>

          )
        }

      </section>


      {/* =====================================================
          WARNING
      ====================================================== */}

      <div className="prediction-page-warning">

        {analytics.note}

      </div>

    </div>
  );
}


// ============================================================
// KPI CARD
// ============================================================

interface AnalyticsStatCardProps {
  label: string;

  value:
    | number
    | string;

  helper: string;
}


function AnalyticsStatCard({
  label,
  value,
  helper,
}: AnalyticsStatCardProps) {

  return (
    <div className="stat-card">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

      <small>
        {helper}
      </small>

    </div>
  );
}


// ============================================================
// GROUP CARD
// ============================================================

interface ValueGroupCardProps {
  title: string;
  subtitle: string;
  data: ValueAnalyticsGroup;
  elite?: boolean;
}


function ValueGroupCard({
  title,
  subtitle,
  data,
  elite = false,
}: ValueGroupCardProps) {

  return (
    <div
      className={
        elite
          ? (
              "value-group-card "
              + "value-group-card--elite"
            )
          : "value-group-card"
      }
    >

      <div className="value-group-card__header">

        <div>

          <span>
            {title}
          </span>

          <small>
            {subtitle}
          </small>

        </div>


        {elite && (

          <span className="value-elite-badge">
            ELITE
          </span>

        )}

      </div>


      <div className="value-group-metrics">

        <ValueMetric
          label="Total"
          value={
            data.total
          }
        />

        <ValueMetric
          label="Evaluated"
          value={
            data.evaluated
          }
        />

        <ValueMetric
          label="Accuracy"
          value={
            formatPercent(
              data.accuracy
            )
          }
        />

        <ValueMetric
          label="Profit"
          value={
            formatUnits(
              data.profit
            )
          }
        />

        <ValueMetric
          label="ROI"
          value={
            formatSignedPercent(
              data.roi
            )
          }
        />

        <ValueMetric
          label="Avg Edge"
          value={
            formatPercent(
              data.average_edge
            )
          }
        />

        <ValueMetric
          label="Avg Odds"
          value={
            data.average_odds === null
              ? "-"
              : data.average_odds.toFixed(
                  2
                )
          }
        />

      </div>

    </div>
  );
}


// ============================================================
// METRIC
// ============================================================

interface ValueMetricProps {
  label: string;

  value:
    | number
    | string;
}


function ValueMetric({
  label,
  value,
}: ValueMetricProps) {

  return (
    <div className="value-metric">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}


// ============================================================
// LIVE SIGNAL CARD
// ============================================================

interface ValueSignalCardProps {
  item: ValueAnalyticsRecentItem;
}


function ValueSignalCard({
  item,
}: ValueSignalCardProps) {

  return (
    <Link
      to={
        `/matches/${item.match_id}`
      }
      className={
        item.is_elite_value
          ? (
              "value-signal-card "
              + "value-signal-card--elite"
            )
          : "value-signal-card"
      }
    >

      <div className="value-signal-card__top">

        <div>

          <span className="value-league">
            {item.league}
          </span>

          <strong>
            {item.home_team}
            {" vs "}
            {item.away_team}
          </strong>

          <small>
            {
              formatDate(
                item.match_date
              )
            }
          </small>

        </div>


        <span
          className={
            item.is_elite_value
              ? (
                  "value-signal-badge "
                  + "value-signal-badge--elite"
                )
              : "value-signal-badge"
          }
        >
          {
            item.is_elite_value
              ? "ELITE VALUE"
              : "VALUE"
          }
        </span>

      </div>


      <div className="value-pick-row">

        <div>

          <span>
            Value Pick
          </span>

          <strong>
            {item.value_pick}
          </strong>

        </div>


        <div>

          <span>
            Odds
          </span>

          <strong>
            {item.market_odds.toFixed(2)}
          </strong>

        </div>


        <div>

          <span>
            Edge
          </span>

          <strong className="value-positive">
            +{item.edge.toFixed(1)}%
          </strong>

        </div>

      </div>


      <div className="value-probability-grid">

        <div>

          <span>
            Model
          </span>

          <strong>
            {
              item.model_probability.toFixed(
                1
              )
            }%
          </strong>

        </div>


        <div>

          <span>
            Market
          </span>

          <strong>
            {
              item.market_probability.toFixed(
                1
              )
            }%
          </strong>

        </div>


        <div>

          <span>
            Fair Odds
          </span>

          <strong>
            {
              item.fair_odds === null
                ? "-"
                : item.fair_odds.toFixed(
                    2
                  )
            }
          </strong>

        </div>


        <div>

          <span>
            Expected Value
          </span>

          <strong>
            {
              formatSignedPercent(
                item.expected_value
              )
            }
          </strong>

        </div>

      </div>


      <div className="value-signal-footer">

        <span>
          Score {
            item.analitiko_score.toFixed(
              1
            )
          }
        </span>

        <span>
          {
            item.same_as_model_pick
              ? "ML CONSENSUS"
              : "MARKET DIVERGENCE"
          }
        </span>

        {
          item.bookmaker
          && (
            <span>
              {item.bookmaker}
            </span>
          )
        }

      </div>

    </Link>
  );
}


// ============================================================
// RESULT CARD
// ============================================================

interface ValueResultCardProps {
  item: ValueAnalyticsRecentItem;
}


function ValueResultCard({
  item,
}: ValueResultCardProps) {

  return (
    <Link
      to={
        `/matches/${item.match_id}`
      }
      className="value-result-card"
    >

      <div className="value-result-card__header">

        <div>

          <span>
            {item.league}
          </span>

          <strong>
            {item.home_team}
            {" vs "}
            {item.away_team}
          </strong>

        </div>


        <span
          className={
            item.correct
              ? (
                  "value-result-status "
                  + "value-result-status--correct"
                )
              : (
                  "value-result-status "
                  + "value-result-status--wrong"
                )
          }
        >
          {
            item.correct
              ? "WIN"
              : "LOSS"
          }
        </span>

      </div>


      <div className="value-result-grid">

        <ValueMetric
          label="Pick"
          value={
            item.value_pick
          }
        />

        <ValueMetric
          label="Actual"
          value={
            item.actual_result
            ?? "-"
          }
        />

        <ValueMetric
          label="Odds"
          value={
            item.market_odds.toFixed(
              2
            )
          }
        />

        <ValueMetric
          label="Edge"
          value={
            `+${item.edge.toFixed(1)}%`
          }
        />

        <ValueMetric
          label="Profit"
          value={
            item.profit === null
              ? "-"
              : formatUnits(
                  item.profit
                )
          }
        />

        <ValueMetric
          label="ROI"
          value={
            formatSignedPercent(
              item.roi
            )
          }
        />

      </div>


      <div className="value-result-footer">

        {
          item.is_elite_value
          && (
            <span className="value-elite-badge">
              ELITE VALUE
            </span>
          )
        }

        {
          item.same_as_model_pick
          && (
            <span className="value-consensus-badge">
              ML CONSENSUS
            </span>
          )
        }

      </div>

    </Link>
  );
}


export default ValueAnalytics;