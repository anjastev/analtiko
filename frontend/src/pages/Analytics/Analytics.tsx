import {
  useEffect,
  useState,
} from "react";

import {
  Link,
} from "react-router-dom";

import api from "../../services/api";

import type {
  MlAnalyticsResponse,
} from "../../types/mlAnalytics";


function Analytics() {

  const [
    analytics,
    setAnalytics,
  ] =
    useState<MlAnalyticsResponse | null>(
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

        setLoading(true);
        setError("");


        const response =
          await api.get<MlAnalyticsResponse>(
            "/api/ml-analytics/performance"
          );


        setAnalytics(
          response.data
        );


      } catch (err) {

        console.error(
          "Failed to load ML analytics:",
          err
        );


        setError(
          "Could not load ML analytics."
        );


      } finally {

        setLoading(false);

      }
    }


    loadAnalytics();

  }, []);


  // ==========================================================
  // LOADING
  // ==========================================================

  if (loading) {

    return (
      <div className="page">

        <p>
          Loading ML analytics...
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
            || "ML analytics unavailable."
          }
        </p>

      </div>
    );
  }


  // ==========================================================
  // DATA
  // ==========================================================

  const summary =
    analytics.summary;


  const strong =
    analytics.strong_picks;


  const elite =
    analytics.elite_picks;


  const validation =
    analytics.validation;


  // ==========================================================
  // JSX
  // ==========================================================

  return (
    <div className="page">

      {/* =====================================================
          HEADER
      ====================================================== */}

      <div className="page-header">

        <div>

          <p className="eyebrow">
            Model Intelligence
          </p>

          <h1>
            ML Analytics
          </h1>

          <p className="page-subtitle">
            Live performance tracking for
            frozen ML v2 predictions.
          </p>

        </div>

      </div>


      {/* =====================================================
          LIVE KPI CARDS
      ====================================================== */}

      <div className="stats-grid">

        <AnalyticsStatCard
          label="Snapshots"
          value={
            summary.total_snapshots
          }
          helper="Saved pre-match predictions"
        />


        <AnalyticsStatCard
          label="Pending"
          value={
            summary.pending
          }
          helper="Waiting for final result"
        />


        <AnalyticsStatCard
          label="Evaluated"
          value={
            summary.evaluated
          }
          helper="Completed predictions"
        />


        <AnalyticsStatCard
          label="Correct"
          value={
            summary.correct
          }
          helper="Correct live ML picks"
        />


        <AnalyticsStatCard
          label="Live Accuracy"
          value={
            summary.accuracy === null
              ? "-"
              : `${summary.accuracy.toFixed(1)}%`
          }
          helper={
            `${summary.evaluated} predictions evaluated`
          }
        />


        <AnalyticsStatCard
          label="Strong Accuracy"
          value={
            strong.accuracy === null
              ? "-"
              : `${strong.accuracy.toFixed(1)}%`
          }
          helper={
            `${strong.evaluated} strong picks evaluated`
          }
        />


        <AnalyticsStatCard
          label="Elite Picks"
          value={
            elite.total
          }
          helper={
            `Score ≥ ${elite.threshold.toFixed(0)}`
          }
        />


        <AnalyticsStatCard
          label="Elite Accuracy"
          value={
            elite.accuracy === null
              ? "-"
              : `${elite.accuracy.toFixed(1)}%`
          }
          helper={
            `${elite.evaluated} elite picks evaluated`
          }
        />

      </div>


      {/* =====================================================
          MODEL STATUS
      ====================================================== */}

      <section className="ml-analytics-model">

        <div>

          <span>
            Active model
          </span>

          <strong>
            {analytics.model}
          </strong>

        </div>


        <div className="ml-model-status-group">

          <span className="ml-model-frozen">
            FROZEN
          </span>


          <span
            className={
              analytics.experimental
                ? (
                    "ml-model-status "
                    + "ml-model-status--experimental"
                  )
                : "ml-model-status"
            }
          >
            {
              analytics.experimental
                ? "EXPERIMENTAL"
                : "ACTIVE"
            }
          </span>

        </div>

      </section>


      {/* =====================================================
          STRICT OOS VALIDATION
      ====================================================== */}

      <section className="dashboard-section">

        <div className="section-header">

          <div>

            <p className="section-label">
              Frozen Validation
            </p>

            <h2>
              Strict OOS Benchmark
            </h2>

            <p className="page-subtitle">
              Performance on the untouched
              historical holdout. These
              metrics are kept separate
              from live tracking.
            </p>

          </div>

        </div>


        <div className="ml-validation-grid">

          <div>

            <span>
              Holdout Matches
            </span>

            <strong>
              {
                validation
                  .strict_oos_matches
              }
            </strong>

          </div>


          <div>

            <span>
              Overall Accuracy
            </span>

            <strong>
              {
                validation
                  .strict_oos_accuracy
                  .toFixed(1)
              }%
            </strong>

          </div>


          <div>

            <span>
              Strong Accuracy
            </span>

            <strong>
              {
                validation
                  .strict_oos_strong_accuracy
                  .toFixed(1)
              }%
            </strong>

            <small>
              {
                validation
                  .strict_oos_strong_coverage
                  .toFixed(1)
              }% coverage
            </small>

          </div>


          <div className="ml-validation-elite">

            <span>
              Score 50+ Accuracy
            </span>

            <strong>
              {
                validation
                  .strict_oos_elite_accuracy
                  .toFixed(1)
              }%
            </strong>

            <small>
              Threshold ≥ {
                validation
                  .elite_threshold
                  .toFixed(0)
              }
            </small>

          </div>

        </div>


        <p className="ml-validation-note">
          {validation.note}
        </p>

      </section>


      {/* =====================================================
          LIVE CONFIDENCE TRACKING
      ====================================================== */}

      <section className="dashboard-section">

        <div className="section-header">

          <div>

            <p className="section-label">
              Live Confidence
            </p>

            <h2>
              Signal Performance
            </h2>

            <p className="page-subtitle">
              Prospective results collected
              from saved pre-match snapshots.
            </p>

          </div>

        </div>


        <div className="ml-signal-grid">

          <SignalCard
            title="All Predictions"
            total={
              summary.total_snapshots
            }
            evaluated={
              summary.evaluated
            }
            correct={
              summary.correct
            }
            accuracy={
              summary.accuracy
            }
          />


          <SignalCard
            title="Strong"
            total={
              strong.total
            }
            evaluated={
              strong.evaluated
            }
            correct={
              strong.correct
            }
            accuracy={
              strong.accuracy
            }
          />


          <SignalCard
            title="Elite"
            total={
              elite.total
            }
            evaluated={
              elite.evaluated
            }
            correct={
              elite.correct
            }
            accuracy={
              elite.accuracy
            }
            elite
          />

        </div>

      </section>


      {/* =====================================================
          CONFIDENCE LEVELS
      ====================================================== */}

      <section className="dashboard-section">

        <div className="section-header">

          <div>

            <p className="section-label">
              Confidence
            </p>

            <h2>
              By Signal Level
            </h2>

          </div>

        </div>


        <div className="ml-confidence-level-grid">

          {
            analytics
              .confidence_levels
              .map(
                (item) => (

                  <div
                    key={
                      item.level
                    }
                    className={
                      item.level === "ELITE"
                        ? (
                            "ml-confidence-level-card "
                            + "ml-confidence-level-card--elite"
                          )
                        : "ml-confidence-level-card"
                    }
                  >

                    <span
                      className={
                        `ml-confidence-badge ml-confidence-badge--${item.level.toLowerCase()}`
                      }
                    >
                      {item.level}
                    </span>


                    <strong>
                      {
                        item.accuracy === null
                          ? "-"
                          : `${item.accuracy.toFixed(1)}%`
                      }
                    </strong>


                    <small>
                      {
                        item.correct
                      }
                      /
                      {
                        item.evaluated
                      }
                      {" correct"}
                    </small>


                    <small>
                      {
                        item.total
                      }
                      {" total snapshots"}
                    </small>

                  </div>

                )
              )
          }

        </div>

      </section>


      {/* =====================================================
          LEAGUE PERFORMANCE
      ====================================================== */}

      <section className="dashboard-section">

        <div className="section-header">

          <div>

            <p className="section-label">
              Performance
            </p>

            <h2>
              By League
            </h2>

          </div>

        </div>


        {analytics.by_league.length > 0
          ? (

            <div className="ml-league-table">

              <div className="ml-league-table__header">

                <span>
                  League
                </span>

                <span>
                  Snapshots
                </span>

                <span>
                  Evaluated
                </span>

                <span>
                  Accuracy
                </span>

                <span>
                  Strong
                </span>

                <span>
                  Strong Acc.
                </span>

                <span>
                  Elite
                </span>

                <span>
                  Elite Acc.
                </span>

              </div>


              {
                analytics
                  .by_league
                  .map(
                    (item) => (

                      <div
                        key={
                          item.league
                        }
                        className="ml-league-row"
                      >

                        <strong>
                          {item.league}
                        </strong>


                        <span>
                          {item.snapshots}
                        </span>


                        <span>
                          {item.evaluated}
                        </span>


                        <span>
                          {
                            item.accuracy === null
                              ? "-"
                              : `${item.accuracy.toFixed(1)}%`
                          }
                        </span>


                        <span>
                          {item.strong_picks}
                        </span>


                        <span>
                          {
                            item.strong_accuracy
                            === null
                              ? "-"
                              : `${item.strong_accuracy.toFixed(1)}%`
                          }
                        </span>


                        <span>
                          {item.elite_picks}
                        </span>


                        <span
                          className={
                            item.elite_accuracy
                            !== null
                              ? "ml-elite-table-value"
                              : undefined
                          }
                        >
                          {
                            item.elite_accuracy
                            === null
                              ? "-"
                              : `${item.elite_accuracy.toFixed(1)}%`
                          }
                        </span>

                      </div>

                    )
                  )
              }

            </div>

          )
          : (

            <p className="empty-state">
              No league performance data yet.
            </p>

          )
        }

      </section>


      {/* =====================================================
          STRONG / ELITE TRACKING
      ====================================================== */}

      <section className="dashboard-section">

        <div className="section-header">

          <div>

            <p className="section-label">
              High Confidence
            </p>

            <h2>
              Strong & Elite Tracking
            </h2>

          </div>

        </div>


        <div className="ml-strong-summary">

          <div>

            <span>
              Strong Picks
            </span>

            <strong>
              {strong.total}
            </strong>

          </div>


          <div>

            <span>
              Strong Evaluated
            </span>

            <strong>
              {strong.evaluated}
            </strong>

          </div>


          <div>

            <span>
              Strong Accuracy
            </span>

            <strong>
              {
                strong.accuracy === null
                  ? "-"
                  : `${strong.accuracy.toFixed(1)}%`
              }
            </strong>

          </div>


          <div className="ml-summary-elite">

            <span>
              Elite Picks
            </span>

            <strong>
              {elite.total}
            </strong>

          </div>


          <div className="ml-summary-elite">

            <span>
              Elite Evaluated
            </span>

            <strong>
              {elite.evaluated}
            </strong>

          </div>


          <div className="ml-summary-elite">

            <span>
              Elite Accuracy
            </span>

            <strong>
              {
                elite.accuracy === null
                  ? "-"
                  : `${elite.accuracy.toFixed(1)}%`
              }
            </strong>

          </div>

        </div>

      </section>


      {/* =====================================================
          PENDING LIVE PICKS
      ====================================================== */}

      <section className="dashboard-section">

        <div className="section-header">

          <div>

            <p className="section-label">
              Prospective Tracking
            </p>

            <h2>
              Pending Predictions
            </h2>

            <p className="page-subtitle">
              Predictions already frozen
              before their match result.
            </p>

          </div>

        </div>


        {analytics.recent_pending.length > 0
          ? (

            <div className="ml-results-list">

              {
                analytics
                  .recent_pending
                  .map(
                    (item) => (

                      <Link
                        key={
                          item.snapshot_id
                        }
                        to={
                          `/matches/${item.match_id}`
                        }
                        className={
                          item.is_elite_pick
                            ? (
                                "ml-result-card "
                                + "ml-result-card--elite"
                              )
                            : "ml-result-card"
                        }
                      >

                        <div className="ml-result-card__top">

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
                              `ml-confidence-badge ml-confidence-badge--${item.confidence_level.toLowerCase()}`
                            }
                          >
                            {
                              item.confidence_level
                            }
                          </span>

                        </div>


                        <div className="ml-result-details">

                          <div>

                            <span>
                              Pick
                            </span>

                            <strong>
                              {item.pick}
                            </strong>

                          </div>


                          <div>

                            <span>
                              Confidence
                            </span>

                            <strong>
                              {
                                item.confidence
                                  .toFixed(1)
                              }%
                            </strong>

                          </div>


                          <div>

                            <span>
                              Analitiko Score
                            </span>

                            <strong>
                              {
                                item.analitiko_score
                                  .toFixed(1)
                              }
                            </strong>

                          </div>


                          <div>

                            <span>
                              Threshold
                            </span>

                            <strong>
                              {
                                item.is_elite_pick
                                  ? item.elite_threshold
                                  : item.league_threshold
                              }
                            </strong>

                          </div>

                        </div>


                        {item.is_elite_pick
                          ? (

                            <div className="ml-result-elite">
                              ELITE signal · Score ≥ 50
                            </div>

                          )
                          : item.is_strong_pick
                            ? (

                              <div className="ml-result-strong">
                                Strong signal
                              </div>

                            )
                            : null
                        }

                      </Link>

                    )
                  )
              }

            </div>

          )
          : (

            <p className="empty-state">
              No pending ML predictions.
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
              Live Tracking
            </p>

            <h2>
              Recent Results
            </h2>

          </div>

        </div>


        {analytics.recent_results.length > 0
          ? (

            <div className="ml-results-list">

              {
                analytics
                  .recent_results
                  .map(
                    (item) => (

                      <Link
                        key={
                          item.snapshot_id
                        }
                        to={
                          `/matches/${item.match_id}`
                        }
                        className={
                          item.is_elite_pick
                            ? (
                                "ml-result-card "
                                + "ml-result-card--elite"
                              )
                            : "ml-result-card"
                        }
                      >

                        <div className="ml-result-card__top">

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


                          <div className="ml-result-badges">

                            <span
                              className={
                                `ml-confidence-badge ml-confidence-badge--${item.confidence_level.toLowerCase()}`
                              }
                            >
                              {
                                item.confidence_level
                              }
                            </span>


                            <span
                              className={
                                item.correct
                                  ? (
                                      "ml-result-status "
                                      + "ml-result-status--correct"
                                    )
                                  : (
                                      "ml-result-status "
                                      + "ml-result-status--wrong"
                                    )
                              }
                            >
                              {
                                item.correct
                                  ? "CORRECT"
                                  : "WRONG"
                              }
                            </span>

                          </div>

                        </div>


                        <div className="ml-result-score">

                          <span>
                            Final
                          </span>

                          <strong>
                            {
                              item.home_score
                              ?? "-"
                            }

                            {" - "}

                            {
                              item.away_score
                              ?? "-"
                            }
                          </strong>

                        </div>


                        <div className="ml-result-details">

                          <div>

                            <span>
                              Pick
                            </span>

                            <strong>
                              {item.pick}
                            </strong>

                          </div>


                          <div>

                            <span>
                              Actual
                            </span>

                            <strong>
                              {
                                item.actual_result
                                ?? "-"
                              }
                            </strong>

                          </div>


                          <div>

                            <span>
                              Confidence
                            </span>

                            <strong>
                              {
                                item.confidence
                                  .toFixed(1)
                              }%
                            </strong>

                          </div>


                          <div>

                            <span>
                              Score
                            </span>

                            <strong>
                              {
                                item.analitiko_score
                                  .toFixed(1)
                              }
                            </strong>

                          </div>

                        </div>


                        {item.is_elite_pick
                          ? (

                            <div className="ml-result-elite">
                              ELITE signal
                            </div>

                          )
                          : item.is_strong_pick
                            ? (

                              <div className="ml-result-strong">
                                Strong signal
                              </div>

                            )
                            : null
                        }

                      </Link>

                    )
                  )
              }

            </div>

          )
          : (

            <p className="empty-state">
              No evaluated ML predictions yet.
            </p>

          )
        }

      </section>


      {/* =====================================================
          NOTE
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
// SIGNAL CARD
// ============================================================

interface SignalCardProps {
  title: string;

  total: number;

  evaluated: number;

  correct: number;

  accuracy:
    | number
    | null;

  elite?: boolean;
}


function SignalCard({
  title,
  total,
  evaluated,
  correct,
  accuracy,
  elite = false,
}: SignalCardProps) {

  return (
    <div
      className={
        elite
          ? (
              "ml-signal-card "
              + "ml-signal-card--elite"
            )
          : "ml-signal-card"
      }
    >

      <span>
        {title}
      </span>


      <strong>
        {
          accuracy === null
            ? "-"
            : `${accuracy.toFixed(1)}%`
        }
      </strong>


      <small>
        {correct}
        /
        {evaluated}
        {" correct"}
      </small>


      <small>
        {total}
        {" total snapshots"}
      </small>

    </div>
  );
}


export default Analytics;