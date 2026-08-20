import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import api from "../../services/api";

import type {
  TeamDetailsResponse,
} from "../../types/team";


function TeamDetails() {
  const { id } = useParams();

  const [team, setTeam] =
    useState<TeamDetailsResponse | null>(
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

    async function loadTeam() {
      try {
        setLoading(true);
        setError("");

        const response =
          await api.get<TeamDetailsResponse>(
            `/api/teams/${id}`
          );

        setTeam(
          response.data
        );

      } catch (err) {
        console.error(
          "Failed to load team:",
          err
        );

        setError(
          "Could not load team."
        );

      } finally {
        setLoading(false);
      }
    }

    loadTeam();

  }, [id]);


  if (loading) {
    return (
      <div className="page">
        <p>
          Loading team...
        </p>
      </div>
    );
  }


  if (
    error
    || !team
  ) {
    return (
      <div className="page">
        <p>
          {error || "Team not found."}
        </p>
      </div>
    );
  }


  return (
    <div className="page">

      {/* HEADER */}

      <div className="team-details-header">

        <div className="team-details-identity">

          {team.logo ? (

            <img
              src={team.logo}
              alt={team.name}
              className="team-details-logo"
            />

          ) : (

            <div
              className={
                "team-details-logo "
                + "team-details-logo--placeholder"
              }
            >
              {team.name.charAt(0)}
            </div>

          )}


          <div>

            <p className="eyebrow">
              Team Profile
            </p>

            <h1>
              {team.name}
            </h1>

            <p className="page-subtitle">
              {team.country || "Unknown"}
            </p>

          </div>

        </div>

      </div>


      {/* KPI */}

      <div className="team-details-stats">

        <TeamStat
          label="Form"
          value={`${team.form.form_score}/10`}
        />

        <TeamStat
          label="Wins"
          value={team.form.wins}
        />

        <TeamStat
          label="Draws"
          value={team.form.draws}
        />

        <TeamStat
          label="Losses"
          value={team.form.losses}
        />

        <TeamStat
          label="Goals / Match"
          value={team.form.goals_for_avg}
        />

        <TeamStat
          label="Conceded / Match"
          value={team.form.goals_against_avg}
        />

      </div>


      {/* RECENT FORM */}

      <section className="dashboard-section">

        <div className="section-header">

          <div>

            <p className="section-label">
              Recent Performance
            </p>

            <h2>
              Form
            </h2>

          </div>

        </div>


        <div className="team-details-form">

          {team.form.sequence.length > 0
            ? (
              team.form.sequence.map(
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
              <span className="team-no-data">
                No recent form available
              </span>
            )
          }

        </div>

      </section>


      {/* HISTORY */}

      <section className="dashboard-section">

        <div className="section-header">

          <div>

            <p className="section-label">
              Results
            </p>

            <h2>
              Recent Matches
            </h2>

          </div>

        </div>


        <div className="team-history-list">

          {team.history.map(
            (item) => (

              <div
                key={
                  item.fixture_external_id
                }
                className="team-history-row"
              >

                <div className="team-history-date">

                  <span>
                    {
                      new Date(
                        item.match_date
                      ).toLocaleDateString()
                    }
                  </span>

                  <small>
                    {
                      item.league_name
                      || "Competition"
                    }
                  </small>

                </div>


                <div className="team-history-opponent">

                  <span>
                    {
                      item.venue
                      === "home"
                        ? "vs"
                        : "@"
                    }
                  </span>

                  <strong>
                    {item.opponent_name}
                  </strong>

                </div>


                <div className="team-history-score">

                  <strong>
                    {item.goals_for}
                    {" - "}
                    {item.goals_against}
                  </strong>

                </div>


                <span
                  className={
                    `form-badge form-badge--${item.result.toLowerCase()}`
                  }
                >
                  {item.result}
                </span>

              </div>

            )
          )}

        </div>


        {team.history.length === 0 && (

          <p className="empty-state">
            No historical matches available.
          </p>

        )}

      </section>


      {/* UPCOMING */}

      <section className="dashboard-section">

        <div className="section-header">

          <div>

            <p className="section-label">
              Schedule
            </p>

            <h2>
              Upcoming Matches
            </h2>

          </div>

        </div>


        <div className="team-upcoming-list">

          {team.upcoming_matches.map(
            (match) => (

              <Link
                key={match.id}
                to={`/matches/${match.id}`}
                className="team-upcoming-row"
              >

                <div>

                  <span className="dashboard-league">
                    {match.league}
                  </span>

                  <strong>
                    {match.home_team}
                    {" vs "}
                    {match.away_team}
                  </strong>

                </div>


                <div className="team-upcoming-date">

                  <span>
                    {
                      new Date(
                        match.match_date
                      ).toLocaleDateString()
                    }
                  </span>

                  <strong>
                    {
                      new Date(
                        match.match_date
                      ).toLocaleTimeString(
                        [],
                        {
                          hour: "2-digit",
                          minute: "2-digit",
                        }
                      )
                    }
                  </strong>

                </div>

              </Link>

            )
          )}

        </div>


        {team.upcoming_matches.length === 0 && (

          <p className="empty-state">
            No upcoming matches found.
          </p>

        )}

      </section>

    </div>
  );
}


interface TeamStatProps {
  label: string;

  value:
    | string
    | number;
}


function TeamStat({
  label,
  value,
}: TeamStatProps) {

  return (
    <div className="analysis-card">

      <span>
        {label}
      </span>

      <strong>
        {value}
      </strong>

    </div>
  );
}


export default TeamDetails;