import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import api from "../../services/api";

import type { TeamListItem } from "../../types/team";


function Teams() {
  const [teams, setTeams] =
    useState<TeamListItem[]>([]);

  const [search, setSearch] =
    useState("");

  const [sortBy, setSortBy] =
    useState("name");

  const [loading, setLoading] =
    useState(true);


  useEffect(() => {
    async function loadTeams() {
      try {
        const response =
          await api.get<TeamListItem[]>(
            "/api/teams"
          );

        setTeams(
          response.data
        );

      } finally {
        setLoading(false);
      }
    }

    loadTeams();

  }, []);


  const filteredTeams =
    useMemo(() => {

      let result =
        [...teams];


      if (search.trim()) {
        const query =
          search.toLowerCase();

        result =
          result.filter(
            (team) =>
              team.name
                .toLowerCase()
                .includes(query)
              ||
              (
                team.country ?? ""
              )
                .toLowerCase()
                .includes(query)
          );
      }


      if (
        sortBy === "name"
      ) {
        result.sort(
          (a, b) =>
            a.name.localeCompare(
              b.name
            )
        );
      }


      if (
        sortBy === "form"
      ) {
        result.sort(
          (a, b) =>
            b.form.form_score
            -
            a.form.form_score
        );
      }


      if (
        sortBy === "goals"
      ) {
        result.sort(
          (a, b) =>
            b.form.goals_for_avg
            -
            a.form.goals_for_avg
        );
      }


      return result;

    }, [
      teams,
      search,
      sortBy,
    ]);


  if (loading) {
    return (
      <div className="page">
        <p>
          Loading teams...
        </p>
      </div>
    );
  }


  return (
    <div className="page">

      <div className="page-header">

        <div>

          <p className="eyebrow">
            Team Intelligence
          </p>

          <h1>
            Teams
          </h1>

          <p className="page-subtitle">
            Recent form and scoring performance
            for tracked teams.
          </p>

        </div>

      </div>


      <div className="teams-toolbar">

        <input
          type="text"
          value={search}
          onChange={
            (event) =>
              setSearch(
                event.target.value
              )
          }
          placeholder="Search team or country..."
          className="filter-input"
        />


        <select
          value={sortBy}
          onChange={
            (event) =>
              setSortBy(
                event.target.value
              )
          }
          className="filter-select"
        >
          <option value="name">
            Sort by name
          </option>

          <option value="form">
            Sort by form
          </option>

          <option value="goals">
            Sort by goals
          </option>

        </select>

      </div>


      <div className="teams-grid">

        {filteredTeams.map(
          (team) => (

            <Link
              key={team.id}
              to={`/teams/${team.id}`}
              className="team-card"
            >

              <div className="team-card-header">

                {team.logo ? (

                  <img
                    src={team.logo}
                    alt={team.name}
                    className="team-logo"
                  />

                ) : (

                  <div className="team-logo team-logo--placeholder">
                    {team.name.charAt(0)}
                  </div>

                )}


                <div>

                  <h3>
                    {team.name}
                  </h3>

                  <span>
                    {team.country || "Unknown"}
                  </span>

                </div>

              </div>


              <div className="team-form-sequence">

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
                      No recent history
                    </span>
                  )
                }

              </div>


              <div className="team-card-stats">

                <div>
                  <span>
                    Form
                  </span>

                  <strong>
                    {team.form.form_score}/10
                  </strong>
                </div>


                <div>
                  <span>
                    Goals
                  </span>

                  <strong>
                    {team.form.goals_for_avg}
                  </strong>
                </div>


                <div>
                  <span>
                    Conceded
                  </span>

                  <strong>
                    {team.form.goals_against_avg}
                  </strong>
                </div>

              </div>


              <div className="team-record">

                <span>
                  W {team.form.wins}
                </span>

                <span>
                  D {team.form.draws}
                </span>

                <span>
                  L {team.form.losses}
                </span>

              </div>

            </Link>

          )
        )}

      </div>


      {filteredTeams.length === 0 && (

        <div className="matches-empty">

          <h3>
            No teams found
          </h3>

          <p>
            Try changing your search.
          </p>

        </div>

      )}

    </div>
  );
}


export default Teams;