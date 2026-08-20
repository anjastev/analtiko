import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import api from "../../services/api";

import type { LeagueListItem } from "../../types/league";


function Leagues() {
  const [leagues, setLeagues] =
    useState<LeagueListItem[]>([]);

  const [search, setSearch] =
    useState("");

  const [sortBy, setSortBy] =
    useState("name");

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState("");


  useEffect(() => {
    async function loadLeagues() {
      try {
        setLoading(true);
        setError("");

        const response =
          await api.get<LeagueListItem[]>(
            "/api/leagues"
          );

        setLeagues(response.data);

      } catch (err) {
        console.error(
          "Failed to load leagues:",
          err
        );

        setError(
          "Could not load leagues."
        );

      } finally {
        setLoading(false);
      }
    }

    loadLeagues();

  }, []);


  const filteredLeagues =
    useMemo(() => {

      let result =
        [...leagues];


      if (search.trim()) {
        const query =
          search.toLowerCase();

        result =
          result.filter(
            (league) =>
              league.name
                .toLowerCase()
                .includes(query)
              ||
              (
                league.country ?? ""
              )
                .toLowerCase()
                .includes(query)
          );
      }


      if (sortBy === "name") {
        result.sort(
          (a, b) =>
            a.name.localeCompare(
              b.name
            )
        );
      }


      if (sortBy === "matches") {
        result.sort(
          (a, b) =>
            b.matches_count
            - a.matches_count
        );
      }


      return result;

    }, [
      leagues,
      search,
      sortBy,
    ]);


  if (loading) {
    return (
      <div className="page">
        <p>Loading leagues...</p>
      </div>
    );
  }


  if (error) {
    return (
      <div className="page">
        <p>{error}</p>
      </div>
    );
  }


  return (
    <div className="page">

      <div className="page-header">

        <div>
          <p className="eyebrow">
            Competition Intelligence
          </p>

          <h1>Leagues</h1>

          <p className="page-subtitle">
            Browse tracked competitions and
            their available matches.
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
          placeholder="Search league or country..."
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

          <option value="matches">
            Most matches
          </option>
        </select>

      </div>


      <div className="leagues-grid">

        {filteredLeagues.map(
          (league) => (

            <Link
              key={league.id}
              to={`/leagues/${league.id}`}
              className="league-card"
            >

              <div className="league-card-header">

                {league.logo ? (

                  <img
                    src={league.logo}
                    alt={league.name}
                    className="league-logo"
                  />

                ) : (

                  <div className="league-logo league-logo--placeholder">
                    {league.name.charAt(0)}
                  </div>

                )}


                <div>

                  <h3>
                    {league.name}
                  </h3>

                  <span>
                    {league.country || "International"}
                  </span>

                </div>

              </div>


              <div className="league-card-footer">

                <span>
                  Available matches
                </span>

                <strong>
                  {league.matches_count}
                </strong>

              </div>

            </Link>

          )
        )}

      </div>


      {filteredLeagues.length === 0 && (

        <div className="matches-empty">

          <h3>No leagues found</h3>

          <p>
            Try changing your search.
          </p>

        </div>

      )}

    </div>
  );
}


export default Leagues;