import { useEffect, useMemo, useState } from "react";

import api from "../../services/api";
import MatchCard from "../../components/MatchCard";

import type { Match } from "../../types/match";
import type { PredictionListItem } from "../../types/predictionList";

function Matches() {
  const [matches, setMatches] = useState<Match[]>([]);
  const [predictions, setPredictions] = useState<PredictionListItem[]>([]);

  const [search, setSearch] = useState("");
  const [league, setLeague] = useState("all");
  const [sortBy, setSortBy] = useState("time");
  const [minConfidence, setMinConfidence] = useState(0);
  const [dateFilter, setDateFilter] = useState("all");

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [matchesResponse, predictionsResponse] = await Promise.all([
          api.get<Match[]>("/api/matches"),
          api.get<PredictionListItem[]>("/api/matches/predictions/all"),
        ]);

        setMatches(matchesResponse.data);
        setPredictions(predictionsResponse.data);
      } catch (error) {
        console.error("Failed to load matches:", error);
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const predictionMap = useMemo(() => {
    return new Map(
      predictions.map((item) => [
        item.match_id,
        item.prediction.confidence,
      ])
    );
  }, [predictions]);

  const leagues = useMemo(() => {
    const uniqueLeagues = new Set(
      matches.map((match) => match.league.name)
    );

    return Array.from(uniqueLeagues).sort();
  }, [matches]);

  const filteredMatches = useMemo(() => {
    let result = [...matches];

    // Search
    if (search.trim()) {
      const query = search.toLowerCase();

      result = result.filter((match) => {
        return (
          match.home_team.name.toLowerCase().includes(query) ||
          match.away_team.name.toLowerCase().includes(query) ||
          match.league.name.toLowerCase().includes(query)
        );
      });
    }

    // League filter
    if (league !== "all") {
      result = result.filter(
        (match) => match.league.name === league
      );
    }

    // Date filter
    if (dateFilter !== "all") {
      const target = new Date();

      if (dateFilter === "tomorrow") {
        target.setDate(target.getDate() + 1);
      }

      result = result.filter((match) => {
        const matchDate = new Date(match.match_date);

        return (
          matchDate.getFullYear() === target.getFullYear() &&
          matchDate.getMonth() === target.getMonth() &&
          matchDate.getDate() === target.getDate()
        );
      });
    }

    // Confidence filter
    if (minConfidence > 0) {
      result = result.filter((match) => {
        const confidence = predictionMap.get(match.id) ?? 0;

        return confidence >= minConfidence;
      });
    }

    // Sorting
    if (sortBy === "time") {
      result.sort(
        (a, b) =>
          new Date(a.match_date).getTime() -
          new Date(b.match_date).getTime()
      );
    }

    if (sortBy === "confidence") {
      result.sort((a, b) => {
        const confidenceA = predictionMap.get(a.id) ?? 0;
        const confidenceB = predictionMap.get(b.id) ?? 0;

        return confidenceB - confidenceA;
      });
    }

    if (sortBy === "league") {
      result.sort((a, b) =>
        a.league.name.localeCompare(b.league.name)
      );
    }

    return result;
  }, [
    matches,
    predictions,
    search,
    league,
    sortBy,
    minConfidence,
    dateFilter,
    predictionMap,
  ]);

  if (loading) {
    return (
      <div className="page">
        <p>Loading matches...</p>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <p className="eyebrow">Match Center</p>
          <h1>Matches</h1>

          <p className="page-subtitle">
            Search, filter and analyze available football matches.
          </p>
        </div>
      </div>

      <div className="matches-toolbar">
        <input
          type="text"
          placeholder="Search team or league..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          className="filter-input"
        />

        <select
          value={dateFilter}
          onChange={(event) => setDateFilter(event.target.value)}
          className="filter-select"
        >
          <option value="all">All dates</option>
          <option value="today">Today</option>
          <option value="tomorrow">Tomorrow</option>
        </select>

        <select
          value={league}
          onChange={(event) => setLeague(event.target.value)}
          className="filter-select"
        >
          <option value="all">All leagues</option>

          {leagues.map((leagueName) => (
            <option key={leagueName} value={leagueName}>
              {leagueName}
            </option>
          ))}
        </select>

        <select
          value={minConfidence}
          onChange={(event) =>
            setMinConfidence(Number(event.target.value))
          }
          className="filter-select"
        >
          <option value={0}>Any confidence</option>
          <option value={50}>50%+</option>
          <option value={60}>60%+</option>
          <option value={70}>70%+</option>
          <option value={80}>80%+</option>
        </select>

        <select
          value={sortBy}
          onChange={(event) => setSortBy(event.target.value)}
          className="filter-select"
        >
          <option value="time">Sort by time</option>
          <option value="confidence">Sort by confidence</option>
          <option value="league">Sort by league</option>
        </select>
      </div>

      <div className="matches-summary">
        <span>
          Showing <strong>{filteredMatches.length}</strong> of{" "}
          <strong>{matches.length}</strong> matches
        </span>
      </div>

      <div className="matches-grid">
        {filteredMatches.map((match) => (
          <div key={match.id} className="match-wrapper">
            <MatchCard match={match} />

            {predictionMap.has(match.id) && (
              <div className="match-confidence-badge">
                {predictionMap.get(match.id)?.toFixed(0)}%
              </div>
            )}
          </div>
        ))}
      </div>

      {filteredMatches.length === 0 && (
        <div className="matches-empty">
          <h3>No matches found</h3>
          <p>Try changing your search or filters.</p>
        </div>
      )}
    </div>
  );
}

export default Matches;