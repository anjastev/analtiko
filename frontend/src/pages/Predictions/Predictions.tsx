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
  MlPredictionItem,
  MatchPick,
} from "../../types/mlPrediction";


// ============================================================
// PICK LABEL
// ============================================================

function getPickLabel(
  pick: MatchPick,
  homeTeam: string,
  awayTeam: string,
) {

  if (pick === "HOME") {
    return homeTeam;
  }

  if (pick === "AWAY") {
    return awayTeam;
  }

  return "Draw";
}


// ============================================================
// SIGNAL PRIORITY
// ============================================================

function getSignalPriority(
  item: MlPredictionItem,
) {

  const prediction =
    item.prediction;


  if (
    prediction.is_elite_pick
  ) {
    return 4;
  }


  if (
    prediction.is_strong_pick
  ) {
    return 3;
  }


  if (
    prediction.confidence_level
    === "MEDIUM"
  ) {
    return 2;
  }


  return 1;
}


// ============================================================
// PREDICTIONS PAGE
// ============================================================

function Predictions() {

  const [
    predictions,
    setPredictions,
  ] =
    useState<MlPredictionItem[]>(
      []
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


  const [
    leagueFilter,
    setLeagueFilter,
  ] =
    useState("ALL");


  const [
    signalFilter,
    setSignalFilter,
  ] =
    useState<
      | "ALL"
      | "STRONG"
      | "ELITE"
    >("ALL");


  // ==========================================================
  // LOAD ML PREDICTIONS
  // ==========================================================

  useEffect(() => {

    async function loadPredictions() {

      try {

        setLoading(true);
        setError("");


        const response =
          await api.get<
            MlPredictionItem[]
          >(
            "/api/matches/ml-predictions/all"
          );


        setPredictions(
          response.data
        );


      } catch (err) {

        console.error(
          "Failed to load ML predictions:",
          err
        );


        setError(
          "Could not load ML predictions."
        );


      } finally {

        setLoading(false);

      }
    }


    loadPredictions();

  }, []);


  // ==========================================================
  // LEAGUES
  // ==========================================================

  const leagues =
    useMemo(() => {

      return Array.from(
        new Set(
          predictions.map(
            (item) =>
              item.league
          )
        )
      ).sort();

    }, [predictions]);


  // ==========================================================
  // ELITE PICKS
  // ==========================================================

  const elitePicks =
    useMemo(() => {

      return predictions
        .filter(
          (item) =>
            item
              .prediction
              .is_elite_pick
        )
        .sort(
          (a, b) =>
            b.prediction
              .analitiko_score
            -
            a.prediction
              .analitiko_score
        )
        .slice(
          0,
          6
        );

    }, [predictions]);


  // ==========================================================
  // STRONG PICKS
  //
  // ELITE is intentionally excluded here so the same match
  // does not appear in both highlighted sections.
  // ==========================================================

  const strongPicks =
    useMemo(() => {

      return predictions
        .filter(
          (item) =>
            item
              .prediction
              .is_strong_pick
            &&
            !item
              .prediction
              .is_elite_pick
        )
        .sort(
          (a, b) =>
            b.prediction
              .analitiko_score
            -
            a.prediction
              .analitiko_score
        )
        .slice(
          0,
          6
        );

    }, [predictions]);


  // ==========================================================
  // COUNTERS
  // ==========================================================

  const eliteCount =
    useMemo(() => {

      return predictions.filter(
        (item) =>
          item
            .prediction
            .is_elite_pick
      ).length;

    }, [predictions]);


  const strongCount =
    useMemo(() => {

      return predictions.filter(
        (item) =>
          item
            .prediction
            .is_strong_pick
          &&
          !item
            .prediction
            .is_elite_pick
      ).length;

    }, [predictions]);


  // ==========================================================
  // FILTERED DATA
  // ==========================================================

  const filteredPredictions =
    useMemo(() => {

      let result =
        [...predictions];


      // ======================================================
      // LEAGUE
      // ======================================================

      if (
        leagueFilter
        !== "ALL"
      ) {

        result =
          result.filter(
            (item) =>
              item.league
              === leagueFilter
          );

      }


      // ======================================================
      // SIGNAL FILTER
      // ======================================================

      if (
        signalFilter
        === "ELITE"
      ) {

        result =
          result.filter(
            (item) =>
              item
                .prediction
                .is_elite_pick
          );

      }


      if (
        signalFilter
        === "STRONG"
      ) {

        result =
          result.filter(
            (item) =>
              item
                .prediction
                .is_strong_pick
          );

      }


      // ======================================================
      // SORT
      //
      // ELITE -> STRONG -> MEDIUM -> LOW
      // Then Analitiko Score inside each level.
      // ======================================================

      result.sort(
        (a, b) => {

          const priorityDifference =
            getSignalPriority(b)
            -
            getSignalPriority(a);


          if (
            priorityDifference
            !== 0
          ) {

            return (
              priorityDifference
            );

          }


          return (
            b.prediction
              .analitiko_score
            -
            a.prediction
              .analitiko_score
          );

        }
      );


      return result;

    }, [
      predictions,
      leagueFilter,
      signalFilter,
    ]);


  // ==========================================================
  // LOADING
  // ==========================================================

  if (loading) {

    return (
      <div className="page">

        <p>
          Loading ML predictions...
        </p>

      </div>
    );
  }


  // ==========================================================
  // ERROR
  // ==========================================================

  if (error) {

    return (
      <div className="page">

        <p>
          {error}
        </p>

      </div>
    );
  }


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
            Machine Learning
          </p>

          <h1>
            Predictions
          </h1>

          <p className="page-subtitle">
            Frozen ML v2 predictions ranked
            by Analitiko Score and signal
            strength.
          </p>

        </div>

      </div>


      {/* =====================================================
          SIGNAL SUMMARY
      ====================================================== */}

      <div className="prediction-signal-summary">

        <div>

          <span>
            Predictions
          </span>

          <strong>
            {predictions.length}
          </strong>

        </div>


        <div className="prediction-summary-strong">

          <span>
            Strong
          </span>

          <strong>
            {strongCount}
          </strong>

        </div>


        <div className="prediction-summary-elite">

          <span>
            Elite
          </span>

          <strong>
            {eliteCount}
          </strong>

          <small>
            Score ≥ 50
          </small>

        </div>

      </div>


      {/* =====================================================
          ELITE PICKS
      ====================================================== */}

      {elitePicks.length > 0 && (

        <section className="elite-picks-section">

          <div
            className={
              "section-header "
              + "section-header--row"
            }
          >

            <div>

              <p className="section-label">
                Highest Signal
              </p>

              <h2>
                Elite Picks
              </h2>

              <p className="page-subtitle">
                Experimental ML predictions
                with Analitiko Score ≥ 50.
              </p>

            </div>


            <span className="elite-threshold-label">
              Score ≥ 50
            </span>

          </div>


          <div className="elite-picks-grid">

            {elitePicks.map(
              (item) => (

                <PredictionCard
                  key={
                    item.match_id
                  }
                  item={item}
                  elite
                />

              )
            )}

          </div>

        </section>

      )}


      {/* =====================================================
          STRONG PICKS
      ====================================================== */}

      {strongPicks.length > 0 && (

        <section className="strong-picks-section">

          <div className="section-header">

            <div>

              <p className="section-label">
                High Confidence
              </p>

              <h2>
                Strong Picks
              </h2>

              <p className="page-subtitle">
                Predictions above their
                league-specific strong
                threshold but below the
                global Elite threshold.
              </p>

            </div>

          </div>


          <div className="strong-picks-grid">

            {strongPicks.map(
              (item) => (

                <PredictionCard
                  key={
                    item.match_id
                  }
                  item={item}
                  featured
                />

              )
            )}

          </div>

        </section>

      )}


      {/* =====================================================
          FILTERS
      ====================================================== */}

      <div className="predictions-toolbar">

        {/* ===================================================
            LEAGUE FILTER
        ==================================================== */}

        <select
          value={
            leagueFilter
          }
          onChange={
            (event) =>
              setLeagueFilter(
                event.target.value
              )
          }
          className="filter-select"
        >

          <option value="ALL">
            All leagues
          </option>


          {leagues.map(
            (league) => (

              <option
                key={
                  league
                }
                value={
                  league
                }
              >
                {league}
              </option>

            )
          )}

        </select>


        {/* ===================================================
            SIGNAL FILTER
        ==================================================== */}

        <select
          value={
            signalFilter
          }
          onChange={(event) =>
  setSignalFilter(
    event.target.value as
      | "ALL"
      | "STRONG"
      | "ELITE"
  )
}
          className="filter-select"
        >

          <option value="ALL">
            All signals
          </option>

          <option value="STRONG">
            Strong + Elite
          </option>

          <option value="ELITE">
            Elite only
          </option>

        </select>

      </div>


      {/* =====================================================
          ALL PREDICTIONS
      ====================================================== */}

      <section className="predictions-list-section">

        <div
          className={
            "section-header "
            + "section-header--row"
          }
        >

          <div>

            <p className="section-label">
              ML Model
            </p>

            <h2>
              All Predictions
            </h2>

          </div>


          <span className="predictions-count">

            {
              filteredPredictions.length
            }

            {" matches"}

          </span>

        </div>


        {filteredPredictions.length > 0
          ? (

            <div className="ml-predictions-grid">

              {
                filteredPredictions.map(
                  (item) => (

                    <PredictionCard
                      key={
                        item.match_id
                      }
                      item={item}
                    />

                  )
                )
              }

            </div>

          )
          : (

            <div className="matches-empty">

              <h3>
                No predictions found
              </h3>

              <p>
                Try changing the league
                or signal filter.
              </p>

            </div>

          )
        }

      </section>


      {/* =====================================================
          WARNING
      ====================================================== */}

      <div className="prediction-page-warning">

        ML predictions are experimental.
        Strong thresholds were frozen using
        development-period validation.
        Elite represents Analitiko Score ≥ 50.
        Historical validation does not
        guarantee future results.

      </div>

    </div>
  );
}


// ============================================================
// PREDICTION CARD
// ============================================================

interface PredictionCardProps {

  item: MlPredictionItem;

  featured?: boolean;

  elite?: boolean;

}


function PredictionCard({
  item,
  featured = false,
  elite = false,
}: PredictionCardProps) {

  const prediction =
    item.prediction;


  const pickLabel =
    getPickLabel(
      prediction.pick,
      item.home_team,
      item.away_team,
    );


  const matchDate =
    new Date(
      item.match_date
    );


  // ==========================================================
  // CARD CLASS
  // ==========================================================

  let cardClass =
    "ml-prediction-card";


  if (
    elite
    ||
    prediction.is_elite_pick
  ) {

    cardClass +=
      " ml-prediction-card--elite";

  } else if (featured) {

    cardClass +=
      " ml-prediction-card--featured";

  }


  return (
    <Link
      to={
        `/matches/${item.match_id}`
      }
      className={
        cardClass
      }
    >

      {/* =====================================================
          TOP
      ====================================================== */}

      <div className="ml-prediction-card__top">

        <div>

          <span className="ml-prediction-league">
            {item.league}
          </span>


          <span className="ml-prediction-date">

            {
              matchDate
                .toLocaleDateString()
            }

            {" • "}

            {
              matchDate
                .toLocaleTimeString(
                  [],
                  {
                    hour:
                      "2-digit",

                    minute:
                      "2-digit",
                  }
                )
            }

          </span>

        </div>


        <span
          className={
            `ml-confidence-badge ml-confidence-badge--${prediction.confidence_level.toLowerCase()}`
          }
        >
          {
            prediction
              .confidence_level
          }
        </span>

      </div>


      {/* =====================================================
          MATCH
      ====================================================== */}

      <div className="ml-prediction-match">

        <span>
          {item.home_team}
        </span>

        <strong>
          VS
        </strong>

        <span>
          {item.away_team}
        </span>

      </div>


      {/* =====================================================
          PICK
      ====================================================== */}

      <div
        className={
          prediction.is_elite_pick
            ? (
                "ml-main-pick "
                + "ml-main-pick--elite"
              )
            : "ml-main-pick"
        }
      >

        <span>
          ML Pick
        </span>

        <strong>
          {pickLabel}
        </strong>

      </div>


      {/* =====================================================
          PROBABILITIES
      ====================================================== */}

      <div className="ml-card-probabilities">

        <ProbabilityItem
          label="1"
          value={
            prediction
              .probabilities
              .HOME
          }
        />


        <ProbabilityItem
          label="X"
          value={
            prediction
              .probabilities
              .DRAW
          }
        />


        <ProbabilityItem
          label="2"
          value={
            prediction
              .probabilities
              .AWAY
          }
        />

      </div>


      {/* =====================================================
          SCORE DATA
      ====================================================== */}

      <div className="ml-card-metrics">

        <div>

          <span>
            Confidence
          </span>

          <strong>
            {
              prediction
                .confidence
                .toFixed(1)
            }%
          </strong>

        </div>


        <div>

          <span>
            Margin
          </span>

          <strong>
            {
              prediction
                .margin
                .toFixed(1)
            }%
          </strong>

        </div>


        <div>

          <span>
            Analitiko Score
          </span>

          <strong
            className={
              prediction.is_elite_pick
                ? "ml-score-elite"
                : undefined
            }
          >
            {
              prediction
                .analitiko_score
                .toFixed(1)
            }
          </strong>

        </div>

      </div>


      {/* =====================================================
          THRESHOLD
      ====================================================== */}

      <div className="ml-threshold-row">

        <span>
          {
            prediction.is_elite_pick
              ? "Elite threshold"
              : "Strong threshold"
          }
        </span>

        <strong>
          {
            prediction.is_elite_pick
              ? prediction
                  .elite_threshold
                  .toFixed(1)

              : prediction
                  .league_threshold
                  .toFixed(1)
          }
        </strong>

      </div>


      {/* =====================================================
          SIGNAL
      ====================================================== */}

      {prediction.is_elite_pick
        ? (

          <div className="ml-elite-indicator">

            <strong>
              ELITE ML SIGNAL
            </strong>

            <span>
              Analitiko Score ≥ {
                prediction
                  .elite_threshold
                  .toFixed(0)
              }
            </span>

          </div>

        )

        : prediction.is_strong_pick
          ? (

            <div className="ml-strong-indicator">
              Strong ML signal
            </div>

          )

          : null
      }

    </Link>
  );
}


// ============================================================
// PROBABILITY ITEM
// ============================================================

interface ProbabilityItemProps {

  label: string;

  value: number;

}


function ProbabilityItem({
  label,
  value,
}: ProbabilityItemProps) {

  return (
    <div className="ml-probability-item">

      <div className="ml-probability-header">

        <span>
          {label}
        </span>

        <strong>
          {value.toFixed(1)}%
        </strong>

      </div>


      <div className="ml-probability-track">

        <div
          className="ml-probability-fill"
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


export default Predictions;