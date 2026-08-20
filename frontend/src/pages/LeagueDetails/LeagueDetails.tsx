import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import api from "../../services/api";

import type {
  LeagueDetailsResponse,
} from "../../types/league";


function LeagueDetails() {
  const { id } = useParams();

  const [league, setLeague] =
    useState<LeagueDetailsResponse | null>(
      null
    );

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  useEffect(() => {
    if (!id) {
      return;
    }

    async function loadLeague() {
      try {
        setLoading(true);
        setError("");

        const response =
          await api.get<LeagueDetailsResponse>(
            `/api/leagues/${id}`
          );

        setLeague(response.data);

      } catch (err) {
        console.error(
          "Failed to load league:",
          err
        );

        setError(
          "Could not load league."
        );

      } finally {
        setLoading(false);
      }
    }

    loadLeague();

  }, [id]);


  const upcomingMatches =
    useMemo(() => {

      if (!league) {
        return [];
      }

      return [...league.matches]
        .sort(
          (a, b) =>
            new Date(
              a.match_date
            ).getTime()
            -
            new Date(
              b.match_date
            ).getTime()
        );

    }, [league]);


  if (loading) {
    return (
      <div className="page">
        <p>Loading league...</p>
      </div>
    );
  }


  if (
    error
    || !league
  ) {
    return (
      <div className="page">
        <p>
          {error || "League not found."}
        </p>
      </div>
    );
  }


  return (
    <div className="page">

      <div className="league-details-header">

        {league.logo ? (

          <img
            src={league.logo}
            alt={league.name}
            className="league-details-logo"
          />

        ) : (

          <div className="league-details-logo league-logo--placeholder">
            {league.name.charAt(0)}
          </div>

        )}


        <div>

          <p className="eyebrow">
            Competition
          </p>

          <h1>
            {league.name}
          </h1>

          <p className="page-subtitle">
            {league.country || "International"}
          </p>

        </div>

      </div>


      <div className="analysis-grid">

        <div className="analysis-card">
          <span>
            Matches
          </span>

          <strong>
            {league.matches_count}
          </strong>
        </div>


        <div className="analysis-card">
          <span>
            Competition
          </span>

          <strong>
            {league.name}
          </strong>
        </div>


        <div className="analysis-card">
          <span>
            Country
          </span>

          <strong>
            {league.country || "International"}
          </strong>
        </div>

      </div>


      <section className="dashboard-section">

        <div className="section-header">

          <div>
            <p className="section-label">
              Schedule
            </p>

            <h2>
              Matches
            </h2>
          </div>

        </div>


        <div className="league-matches-list">

          {upcomingMatches.map(
            (match) => {

              const date =
                new Date(
                  match.match_date
                );

              return (
                <Link
                  key={match.id}
                  to={`/matches/${match.id}`}
                  className="league-match-row"
                >

                  <div className="league-match-date">

                    <strong>
                      {date.toLocaleDateString()}
                    </strong>

                    <span>
                      {date.toLocaleTimeString(
                        [],
                        {
                          hour: "2-digit",
                          minute: "2-digit",
                        }
                      )}
                    </span>

                  </div>


                  <div className="league-match-team">

                    {match.home_team.logo && (
                      <img
                        src={
                          match.home_team.logo
                        }
                        alt=""
                      />
                    )}

                    <span>
                      {match.home_team.name}
                    </span>

                  </div>


                  <div className="league-match-score">

                    <strong>
                      {match.home_score ?? "-"}
                      {" : "}
                      {match.away_score ?? "-"}
                    </strong>

                    <span>
                      {match.status}
                    </span>

                  </div>


                  <div className="league-match-team league-match-team--away">

                    <span>
                      {match.away_team.name}
                    </span>

                    {match.away_team.logo && (
                      <img
                        src={
                          match.away_team.logo
                        }
                        alt=""
                      />
                    )}

                  </div>

                </Link>
              );
            }
          )}

        </div>


        {upcomingMatches.length === 0 && (

          <div className="matches-empty">
            <h3>
              No matches available
            </h3>
          </div>

        )}

      </section>

    </div>
  );
}


export default LeagueDetails;