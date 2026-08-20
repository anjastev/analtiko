import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import api from "../../services/api";

import type { TrendingMatch } from "../../types/trending";


function Trending() {
  const [matches, setMatches] =
    useState<TrendingMatch[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  useEffect(() => {
    async function loadTrending() {
      try {
        setLoading(true);
        setError("");

        const response =
          await api.get<TrendingMatch[]>(
            "/api/matches/trending/all"
          );

        setMatches(
          response.data
        );

      } catch (err) {
        console.error(
          "Failed to load trending matches:",
          err
        );

        setError(
          "Could not load trending matches."
        );

      } finally {
        setLoading(false);
      }
    }

    loadTrending();

  }, []);


  if (loading) {
    return (
      <div className="page">
        <p>
          Loading trending matches...
        </p>
      </div>
    );
  }


  if (error) {
    return (
      <div className="page">
        <p>
          {error}
        </p>
      </div>
    );
  }


  return (
    <div className="page">

      <div className="page-header">

        <div>

          <p className="eyebrow">
            Betting Intelligence
          </p>

          <h1>
            Trending Matches
          </h1>

          <p className="page-subtitle">
            Estimated betting interest based
            on odds movement, form, confidence
            and league importance.
          </p>

        </div>

      </div>


      {matches.length === 0 ? (

        <div className="matches-empty">

          <h3>
            No trending matches yet
          </h3>

          <p>
            We need odds and historical data
            before a match can be ranked.
          </p>

        </div>

      ) : (

        <div className="trending-page-list">

          {matches.map(
            (match, index) => (

              <Link
                key={match.match_id}
                to={`/matches/${match.match_id}`}
                className="trending-page-card"
              >

                <div
                  className={
                    `trending-position ${
                      index === 0
                        ? "trending-position--first"
                        : index === 1
                          ? "trending-position--second"
                          : index === 2
                            ? "trending-position--third"
                            : ""
                    }`
                  }
                >
                  #{index + 1}
                </div>


                <div className="trending-main-info">

                  <span className="prediction-league">
                    {match.league}
                  </span>

                  <strong>
                    {match.home_team}
                    {" vs "}
                    {match.away_team}
                  </strong>

                  <small>
                    {new Date(
                      match.match_date
                    ).toLocaleString()}
                  </small>

                </div>


                <div className="trending-score-column">

                  <span>
                    Trending
                  </span>

                  <strong>
                    {match.score}
                  </strong>

                  <small>
                    / 100
                  </small>

                </div>


                <div className="trending-signal-column">

                  <span>
                    Market
                  </span>

                  <MarketSignal
                    signal={
                      match.market_signal
                    }
                  />

                </div>


                <div className="trending-pick-column">

                  <span>
                    Pick
                  </span>

                  <strong>
                    {match.main_pick}
                  </strong>

                </div>


                <div className="trending-confidence-column">

                  <span>
                    Confidence
                  </span>

                  <strong>
                    {match.confidence.toFixed(1)}%
                  </strong>

                  <div className="confidence-track">

                    <div
                      className="confidence-fill"
                      style={{
                        width:
                          `${Math.min(
                            match.confidence,
                            100
                          )}%`,
                      }}
                    />

                  </div>

                </div>


                <div className="trending-odds-column">

                  <span>
                    Odds
                  </span>

                  <div className="trending-mini-odds">

                    <small>
                      1
                    </small>

                    <strong>
                      {match.odds.home.toFixed(2)}
                    </strong>

                    <small>
                      X
                    </small>

                    <strong>
                      {match.odds.draw.toFixed(2)}
                    </strong>

                    <small>
                      2
                    </small>

                    <strong>
                      {match.odds.away.toFixed(2)}
                    </strong>

                  </div>

                </div>

              </Link>

            )
          )}

        </div>

      )}

    </div>
  );
}


interface MarketSignalProps {
  signal:
    | "HOME_DROP"
    | "AWAY_DROP"
    | "STABLE";
}


function MarketSignal({
  signal,
}: MarketSignalProps) {

  if (signal === "HOME_DROP") {
    return (
      <span className="market-signal market-signal--drop">
        ↓ Home odds
      </span>
    );
  }


  if (signal === "AWAY_DROP") {
    return (
      <span className="market-signal market-signal--drop">
        ↓ Away odds
      </span>
    );
  }


  return (
    <span className="market-signal market-signal--stable">
      Stable
    </span>
  );
}


export default Trending;