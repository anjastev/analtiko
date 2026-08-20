import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";

import api from "../../services/api";

import type { Match } from "../../types/match";
import type { MatchStats } from "../../types/matchStats";
import type { Odds } from "../../types/odds";
import type { PopularityResponse } from "../../types/popularity";
import type { PredictionResponse } from "../../types/prediction";
import type { MatchFormResponse } from "../../types/form";
import type { H2HResponse } from "../../types/h2h";
import type { PredictionComparison } from "../../types/predictionComparison";

import PredictionComparisonCard from "../../components/predictions/PredictionComparisonCard";


function MatchDetails() {
  const { id } = useParams();

  const [match, setMatch] =
    useState<Match | null>(null);

  const [stats, setStats] =
    useState<MatchStats | null>(null);

  const [odds, setOdds] =
    useState<Odds[]>([]);

  const [popularity, setPopularity] =
    useState<PopularityResponse | null>(
      null
    );

  const [prediction, setPrediction] =
    useState<PredictionResponse | null>(
      null
    );

  const [form, setForm] =
    useState<MatchFormResponse | null>(
      null
    );

  const [h2h, setH2h] =
    useState<H2HResponse | null>(
      null
    );

  const [
    predictionComparison,
    setPredictionComparison,
  ] =
    useState<PredictionComparison | null>(
      null
    );

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  // ==========================================================
  // LOAD DATA
  // ==========================================================

  useEffect(() => {
    if (!id) {
      return;
    }


    async function loadMatchData() {
      try {
        setLoading(true);
        setError("");


        // ====================================================
        // MATCH - REQUIRED
        // ====================================================

        const matchResponse =
          await api.get<Match>(
            `/api/matches/${id}`
          );


        setMatch(
          matchResponse.data
        );


        // ====================================================
        // OPTIONAL DATA
        // ====================================================

        const results =
          await Promise.allSettled([

            api.get<MatchStats>(
              `/api/matches/${id}/stats`
            ),

            api.get<Odds[]>(
              `/api/matches/${id}/odds`
            ),

            api.get<PopularityResponse>(
              `/api/matches/${id}/popularity`
            ),

            api.get<PredictionResponse>(
              `/api/matches/${id}/prediction`
            ),

            api.get<MatchFormResponse>(
              `/api/matches/${id}/form`
            ),

            api.get<H2HResponse>(
              `/api/matches/${id}/h2h`
            ),

            api.get<PredictionComparison>(
              `/api/matches/${id}/prediction-comparison`
            ),

          ]);


        // ====================================================
        // STATS
        // ====================================================

        if (
          results[0].status
          === "fulfilled"
        ) {
          setStats(
            results[0].value.data
          );
        } else {
          setStats(null);
        }


        // ====================================================
        // ODDS
        // ====================================================

        if (
          results[1].status
          === "fulfilled"
        ) {
          setOdds(
            results[1].value.data
          );
        } else {
          setOdds([]);
        }


        // ====================================================
        // POPULARITY
        // ====================================================

        if (
          results[2].status
          === "fulfilled"
        ) {
          setPopularity(
            results[2].value.data
          );
        } else {
          setPopularity(null);
        }


        // ====================================================
        // RULE PREDICTION
        // ====================================================

        if (
          results[3].status
          === "fulfilled"
        ) {
          setPrediction(
            results[3].value.data
          );
        } else {
          setPrediction(null);
        }


        // ====================================================
        // FORM
        // ====================================================

        if (
          results[4].status
          === "fulfilled"
        ) {
          setForm(
            results[4].value.data
          );
        } else {
          setForm(null);
        }


        // ====================================================
        // H2H
        // ====================================================

        if (
          results[5].status
          === "fulfilled"
        ) {
          setH2h(
            results[5].value.data
          );
        } else {
          setH2h(null);
        }


        // ====================================================
        // RULE ENGINE VS ML
        // ====================================================

        if (
          results[6].status
          === "fulfilled"
        ) {
          setPredictionComparison(
            results[6].value.data
          );
        } else {
          setPredictionComparison(
            null
          );
        }


      } catch (err) {
        console.error(
          "Failed to load match:",
          err
        );

        setError(
          "Could not load match."
        );

      } finally {
        setLoading(false);
      }
    }


    loadMatchData();

  }, [id]);


  // ==========================================================
  // LOADING
  // ==========================================================

  if (loading) {
    return (
      <div className="page">
        <p>
          Loading match...
        </p>
      </div>
    );
  }


  // ==========================================================
  // ERROR
  // ==========================================================

  if (error || !match) {
    return (
      <div className="page">
        <p>
          {error || "Match not found."}
        </p>
      </div>
    );
  }


  // ==========================================================
  // PREPARE DATA
  // ==========================================================

  const matchDate =
    new Date(
      match.match_date
    );


  const sortedOdds =
    [...odds].sort(
      (a, b) =>
        new Date(
          a.recorded_at
        ).getTime()
        -
        new Date(
          b.recorded_at
        ).getTime()
    );


  const openingOdds =
    sortedOdds.length > 0
      ? sortedOdds[0]
      : null;


  const latestOdds =
    sortedOdds.length > 0
      ? sortedOdds[
          sortedOdds.length - 1
        ]
      : null;


  const oddsChartData =
    sortedOdds.map(
      (item) => ({
        time:
          new Date(
            item.recorded_at
          ).toLocaleTimeString(
            [],
            {
              hour: "2-digit",
              minute: "2-digit",
            }
          ),

        home:
          item.home_win,

        draw:
          item.draw,

        away:
          item.away_win,
      })
    );


  // ==========================================================
  // JSX
  // ==========================================================

  return (
    <div className="page">

      {/* =====================================================
          HEADER
      ====================================================== */}

      <div className="match-details-header">

        <div>

          <p className="eyebrow">
            {match.league.name}
          </p>

          <h1>
            {match.home_team.name}
            {" vs "}
            {match.away_team.name}
          </h1>

          <p className="page-subtitle">

            {matchDate.toLocaleDateString()}

            {" • "}

            {matchDate.toLocaleTimeString(
              [],
              {
                hour: "2-digit",
                minute: "2-digit",
              }
            )}

          </p>

        </div>


        <span className="match-status">
          {match.status}
        </span>

      </div>


      {/* =====================================================
          TEAMS
      ====================================================== */}

      <div className="teams-versus">

        <div className="team-panel">

          <span className="team-label">
            HOME
          </span>

          <h2>
            {match.home_team.name}
          </h2>

          <strong className="team-score">
            {match.home_score ?? "-"}
          </strong>

        </div>


        <div className="versus">
          VS
        </div>


        <div className="team-panel">

          <span className="team-label">
            AWAY
          </span>

          <h2>
            {match.away_team.name}
          </h2>

          <strong className="team-score">
            {match.away_score ?? "-"}
          </strong>

        </div>

      </div>


      {/* =====================================================
          RECENT FORM
      ====================================================== */}

      {form && (
        <section className="comparison-section">

          <div className="section-header">

            <div>

              <p className="section-label">
                Recent Form
              </p>

              <h2>
                Last Matches
              </h2>

            </div>

          </div>


          <div className="form-grid">

            {/* HOME FORM */}

            <div className="form-team-card">

              <h3>
                {form.home_team.name}
              </h3>


              <div className="form-sequence">

                {form.home_team.sequence.length > 0
                  ? (
                    form.home_team.sequence.map(
                      (result, index) => (

                        <span
                          key={index}
                          className={
                            `form-badge form-badge--${result.toLowerCase()}`
                          }
                        >
                          {result}
                        </span>

                      )
                    )
                  )
                  : (
                    <span className="page-subtitle">
                      No recent matches
                    </span>
                  )
                }

              </div>


              <div className="form-stats">

                <span>
                  Matches:
                  <strong>
                    {" "}
                    {form.home_team.matches}
                  </strong>
                </span>


                <span>
                  Form score:
                  <strong>
                    {" "}
                    {form.home_team.form_score}/10
                  </strong>
                </span>


                <span>
                  W / D / L:
                  <strong>
                    {" "}
                    {form.home_team.wins}
                    {" / "}
                    {form.home_team.draws}
                    {" / "}
                    {form.home_team.losses}
                  </strong>
                </span>


                <span>
                  Goals / match:
                  <strong>
                    {" "}
                    {form.home_team.goals_for_avg}
                  </strong>
                </span>


                <span>
                  Conceded / match:
                  <strong>
                    {" "}
                    {form.home_team.goals_against_avg}
                  </strong>
                </span>

              </div>

            </div>


            {/* AWAY FORM */}

            <div className="form-team-card">

              <h3>
                {form.away_team.name}
              </h3>


              <div className="form-sequence">

                {form.away_team.sequence.length > 0
                  ? (
                    form.away_team.sequence.map(
                      (result, index) => (

                        <span
                          key={index}
                          className={
                            `form-badge form-badge--${result.toLowerCase()}`
                          }
                        >
                          {result}
                        </span>

                      )
                    )
                  )
                  : (
                    <span className="page-subtitle">
                      No recent matches
                    </span>
                  )
                }

              </div>


              <div className="form-stats">

                <span>
                  Matches:
                  <strong>
                    {" "}
                    {form.away_team.matches}
                  </strong>
                </span>


                <span>
                  Form score:
                  <strong>
                    {" "}
                    {form.away_team.form_score}/10
                  </strong>
                </span>


                <span>
                  W / D / L:
                  <strong>
                    {" "}
                    {form.away_team.wins}
                    {" / "}
                    {form.away_team.draws}
                    {" / "}
                    {form.away_team.losses}
                  </strong>
                </span>


                <span>
                  Goals / match:
                  <strong>
                    {" "}
                    {form.away_team.goals_for_avg}
                  </strong>
                </span>


                <span>
                  Conceded / match:
                  <strong>
                    {" "}
                    {form.away_team.goals_against_avg}
                  </strong>
                </span>

              </div>

            </div>

          </div>

        </section>
      )}


      {/* =====================================================
          HEAD TO HEAD
      ====================================================== */}

      {h2h && (
        <section className="comparison-section">

          <div className="section-header">

            <div>

              <p className="section-label">
                Head to Head
              </p>

              <h2>
                Previous Meetings
              </h2>

            </div>

          </div>


          <div className="h2h-summary">

            <div className="h2h-summary-card">

              <span>
                {h2h.home_team}
              </span>

              <strong>
                {h2h.summary.home_wins}
              </strong>

              <small>
                Wins
              </small>

            </div>


            <div className="h2h-summary-card">

              <span>
                Draws
              </span>

              <strong>
                {h2h.summary.draws}
              </strong>

              <small>
                Draws
              </small>

            </div>


            <div className="h2h-summary-card">

              <span>
                {h2h.away_team}
              </span>

              <strong>
                {h2h.summary.away_wins}
              </strong>

              <small>
                Wins
              </small>

            </div>

          </div>


          <div className="h2h-goals">

            <div>

              <span>
                Avg Goals
              </span>

              <strong>
                {h2h.summary.home_goals_avg}
              </strong>

              <small>
                {h2h.home_team}
              </small>

            </div>


            <div>

              <span>
                Avg Goals
              </span>

              <strong>
                {h2h.summary.away_goals_avg}
              </strong>

              <small>
                {h2h.away_team}
              </small>

            </div>

          </div>


          <div className="h2h-list">

            {h2h.matches.map(
              (item, index) => (

                <div
                  key={index}
                  className="h2h-row"
                >

                  <span className="h2h-date">

                    {new Date(
                      item.date
                    ).toLocaleDateString()}

                  </span>


                  <div className="h2h-teams">

                    <span>
                      {item.home_team}
                    </span>

                    <strong>
                      {item.home_goals}
                      {" - "}
                      {item.away_goals}
                    </strong>

                    <span>
                      {item.away_team}
                    </span>

                  </div>

                </div>

              )
            )}

          </div>

        </section>
      )}


      {/* =====================================================
          CURRENT ODDS
      ====================================================== */}

      {latestOdds && openingOdds && (

        <section className="odds-section">

          <div className="section-header">

            <div>

              <p className="section-label">
                Market
              </p>

              <h2>
                Current Odds
              </h2>

              {latestOdds.bookmaker && (
                <p className="page-subtitle">
                  {latestOdds.bookmaker}
                </p>
              )}

            </div>

          </div>


          <div className="odds-grid">

            <OddsCard
              label="1"
              current={
                latestOdds.home_win
              }
              opening={
                openingOdds.home_win
              }
            />


            <OddsCard
              label="X"
              current={
                latestOdds.draw
              }
              opening={
                openingOdds.draw
              }
            />


            <OddsCard
              label="2"
              current={
                latestOdds.away_win
              }
              opening={
                openingOdds.away_win
              }
            />

          </div>

        </section>

      )}


      {/* =====================================================
          ODDS HISTORY
      ====================================================== */}

      {sortedOdds.length > 1 && (

        <section className="odds-section">

          <div className="section-header">

            <div>

              <p className="section-label">
                Movement
              </p>

              <h2>
                Odds History
              </h2>

            </div>

          </div>


          <div className="chart-wrapper">

            <ResponsiveContainer
              width="100%"
              height={320}
            >

              <LineChart
                data={oddsChartData}
              >

                <CartesianGrid
                  strokeDasharray="3 3"
                />

                <XAxis
                  dataKey="time"
                  tick={{
                    fontSize: 11,
                  }}
                />

                <YAxis />

                <Tooltip />

                <Legend />


                <Line
                  type="monotone"
                  dataKey="home"
                  name="Home"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  dot
                />


                <Line
                  type="monotone"
                  dataKey="draw"
                  name="Draw"
                  stroke="#f59e0b"
                  strokeWidth={2}
                  dot
                />


                <Line
                  type="monotone"
                  dataKey="away"
                  name="Away"
                  stroke="#22c55e"
                  strokeWidth={2}
                  dot
                />

              </LineChart>

            </ResponsiveContainer>

          </div>

        </section>

      )}


      {/* =====================================================
          ADVANCED STATS CARDS
      ====================================================== */}

      {stats && (

        <div className="analysis-grid">

          <div className="analysis-card">

            <span>
              Home Form
            </span>

            <strong>
              {stats.home_form}/10
            </strong>

          </div>


          <div className="analysis-card">

            <span>
              Away Form
            </span>

            <strong>
              {stats.away_form}/10
            </strong>

          </div>


          <div className="analysis-card">

            <span>
              Home xG
            </span>

            <strong>
              {stats.home_xg_avg}
            </strong>

          </div>


          <div className="analysis-card">

            <span>
              Away xG
            </span>

            <strong>
              {stats.away_xg_avg}
            </strong>

          </div>

        </div>

      )}


      {/* =====================================================
          TEAM COMPARISON
      ====================================================== */}

      {stats && (

        <section className="comparison-section">

          <div className="section-header">

            <div>

              <p className="section-label">
                Analytics
              </p>

              <h2>
                Team Comparison
              </h2>

            </div>

          </div>


          <ComparisonRow
            label="Form"
            home={
              stats.home_form
            }
            away={
              stats.away_form
            }
            max={10}
          />


          <ComparisonRow
            label="Goals / Match"
            home={
              stats.home_goals_avg
            }
            away={
              stats.away_goals_avg
            }
            max={4}
          />


          <ComparisonRow
            label="Shots / Match"
            home={
              stats.home_shots_avg
            }
            away={
              stats.away_shots_avg
            }
            max={25}
          />


          <ComparisonRow
            label="Corners / Match"
            home={
              stats.home_corners_avg
            }
            away={
              stats.away_corners_avg
            }
            max={12}
          />


          <ComparisonRow
            label="Possession"
            home={
              stats.home_possession_avg
            }
            away={
              stats.away_possession_avg
            }
            max={100}
            suffix="%"
          />


          <ComparisonRow
            label="xG"
            home={
              stats.home_xg_avg
            }
            away={
              stats.away_xg_avg
            }
            max={4}
          />

        </section>

      )}


      {/* =====================================================
          POPULARITY
      ====================================================== */}

      {popularity && (

        <section className="popularity-section">

          <div className="section-header">

            <div>

              <p className="section-label">
                Trending
              </p>

              <h2>
                Analitiko Popularity
              </h2>

            </div>

          </div>


          <div className="popularity-main">

            <div className="popularity-score">

              <strong>
                {
                  popularity
                    .popularity_score
                }
              </strong>

              <span>
                / 100
              </span>

            </div>


            <div className="popularity-info">

              <span
                className={
                  `popularity-level popularity-level--${popularity.level}`
                }
              >

                {
                  popularity.level.replace(
                    "_",
                    " "
                  )
                }

              </span>


              <p>
                Estimated interest based on
                odds movement, recent form,
                scoring data and league
                strength.
              </p>

            </div>

          </div>


          <div className="popularity-breakdown">

            <BreakdownBar
              label="Odds movement"
              value={
                popularity.breakdown
                  .odds_movement
              }
            />


            <BreakdownBar
              label="Form"
              value={
                popularity.breakdown.form
              }
            />


            <BreakdownBar
              label="Goals"
              value={
                popularity.breakdown.goals
              }
            />


            {"xg" in popularity.breakdown && (
              <BreakdownBar
                label="xG"
                value={
                  popularity.breakdown.xg
                }
              />
            )}


            <BreakdownBar
              label="League"
              value={
                popularity.breakdown.league
              }
            />

          </div>

        </section>

      )}


      {/* =====================================================
          RULE ENGINE PREDICTION
      ====================================================== */}

      {prediction && (

        <section className="prediction-section">

          <div className="section-header">

            <div>

              <p className="section-label">
                Model
              </p>

              <h2>
                Analitiko Prediction
              </h2>

            </div>

          </div>


          <div className="prediction-main">

            <div className="prediction-pick">

              <span>
                Main Pick
              </span>

              <strong>
                {
                  prediction
                    .prediction
                    .main_pick
                }
              </strong>

            </div>


            <div className="prediction-confidence">

              <span>
                Confidence
              </span>

              <strong>
                {
                  prediction
                    .prediction
                    .confidence
                }
                %
              </strong>

            </div>

          </div>


          <div className="prediction-grid">

            <PredictionBox
              label="1"
              value={
                prediction
                  .prediction
                  .home_win
              }
            />


            <PredictionBox
              label="X"
              value={
                prediction
                  .prediction
                  .draw
              }
            />


            <PredictionBox
              label="2"
              value={
                prediction
                  .prediction
                  .away_win
              }
            />


            <PredictionBox
              label="Over 2.5"
              value={
                prediction
                  .prediction
                  .over_25
              }
            />


            <PredictionBox
              label="BTTS"
              value={
                prediction
                  .prediction
                  .btts_yes
              }
            />

          </div>


          <div className="prediction-reasons">

            <h3>
              Why?
            </h3>

            {
              prediction.reasons.map(
                (reason, index) => (

                  <p key={index}>
                    ✓ {reason}
                  </p>

                )
              )
            }

          </div>

        </section>

      )}


      {/* =====================================================
          RULE ENGINE VS ML
      ====================================================== */}

      {predictionComparison && (

        <PredictionComparisonCard
          comparison={
            predictionComparison
          }
        />

      )}


      {/* =====================================================
          NO ANALYSIS YET
      ====================================================== */}

      {!form &&
        !stats &&
        !prediction &&
        !predictionComparison && (

          <div className="analysis-card">

            <span>
              Analysis
            </span>

            <strong>
              Not enough historical data yet.
            </strong>

          </div>

        )}

    </div>
  );
}


// ============================================================
// ODDS CARD
// ============================================================

interface OddsCardProps {
  label: string;
  current: number;
  opening: number;
}


function OddsCard({
  label,
  current,
  opening,
}: OddsCardProps) {

  const difference =
    current - opening;


  const percentage =
    opening !== 0
      ? (
          difference
          / opening
        ) * 100
      : 0;


  let movement =
    "No change";


  if (difference < 0) {

    movement =
      `↓ ${Math.abs(
        percentage
      ).toFixed(1)}%`;

  }


  if (difference > 0) {

    movement =
      `↑ ${percentage.toFixed(
        1
      )}%`;

  }


  return (
    <div className="odds-card">

      <span>
        {label}
      </span>

      <strong>
        {current.toFixed(2)}
      </strong>

      <small>
        Open: {opening.toFixed(2)}
      </small>


      <div
        className={
          difference < 0
            ? (
                "odds-movement "
                + "odds-movement--down"
              )

            : difference > 0
              ? (
                  "odds-movement "
                  + "odds-movement--up"
                )

              : "odds-movement"
        }
      >
        {movement}
      </div>

    </div>
  );
}


// ============================================================
// BREAKDOWN BAR
// ============================================================

interface BreakdownBarProps {
  label: string;
  value: number;
}


function BreakdownBar({
  label,
  value,
}: BreakdownBarProps) {

  return (
    <div className="breakdown-row">

      <div className="breakdown-header">

        <span>
          {label}
        </span>

        <strong>
          {value.toFixed(0)}
        </strong>

      </div>


      <div className="breakdown-track">

        <div
          className="breakdown-fill"
          style={{
            width:
              `${Math.min(
                value,
                100
              )}%`,
          }}
        />

      </div>

    </div>
  );
}


// ============================================================
// PREDICTION BOX
// ============================================================

interface PredictionBoxProps {
  label: string;
  value: number;
}


function PredictionBox({
  label,
  value,
}: PredictionBoxProps) {

  return (
    <div className="prediction-box">

      <span>
        {label}
      </span>

      <strong>
        {value.toFixed(1)}%
      </strong>


      <div className="prediction-track">

        <div
          className="prediction-fill"
          style={{
            width:
              `${Math.min(
                value,
                100
              )}%`,
          }}
        />

      </div>

    </div>
  );
}


// ============================================================
// COMPARISON ROW
// ============================================================

interface ComparisonRowProps {
  label: string;

  home: number;
  away: number;

  max: number;

  suffix?: string;
}


function ComparisonRow({
  label,
  home,
  away,
  max,
  suffix = "",
}: ComparisonRowProps) {

  const homeWidth =
    Math.min(
      (home / max) * 100,
      100
    );


  const awayWidth =
    Math.min(
      (away / max) * 100,
      100
    );


  return (
    <div className="comparison-row">

      <div className="comparison-title">

        <strong>
          {home}
          {suffix}
        </strong>

        <span>
          {label}
        </span>

        <strong>
          {away}
          {suffix}
        </strong>

      </div>


      <div className="comparison-bars">

        <div
          className={
            "comparison-side "
            + "comparison-side--home"
          }
        >

          <div
            className="comparison-fill"
            style={{
              width:
                `${homeWidth}%`,
            }}
          />

        </div>


        <div
          className={
            "comparison-side "
            + "comparison-side--away"
          }
        >

          <div
            className="comparison-fill"
            style={{
              width:
                `${awayWidth}%`,
            }}
          />

        </div>

      </div>

    </div>
  );
}


export default MatchDetails;