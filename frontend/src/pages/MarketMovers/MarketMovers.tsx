import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import api from "../../services/api";

import type { MarketMover } from "../../types/marketMover";


function MarketMovers() {
  const [movers, setMovers] =
    useState<MarketMover[]>([]);

  const [loading, setLoading] =
    useState(true);

  const [marketFilter, setMarketFilter] =
    useState("ALL");

  const [directionFilter, setDirectionFilter] =
    useState("ALL");


  useEffect(() => {
    async function loadMovers() {
      try {
        const response =
          await api.get<MarketMover[]>(
            "/api/matches/market-movers/all"
          );

        setMovers(
          response.data
        );

      } finally {
        setLoading(false);
      }
    }

    loadMovers();

  }, []);


  const filteredMovers =
    useMemo(() => {

      let result =
        [...movers];


      if (
        marketFilter !== "ALL"
      ) {
        result = result.filter(
          (item) =>
            item.market
            === marketFilter
        );
      }


      if (
        directionFilter !== "ALL"
      ) {
        result = result.filter(
          (item) =>
            item.direction
            === directionFilter
        );
      }


      result.sort(
        (a, b) =>
          Math.abs(
            b.change_percentage
          )
          -
          Math.abs(
            a.change_percentage
          )
      );


      return result;

    }, [
      movers,
      marketFilter,
      directionFilter,
    ]);


  if (loading) {
    return (
      <div className="page">
        <p>
          Loading market movers...
        </p>
      </div>
    );
  }


  return (
    <div className="page">

      <div className="page-header">

        <div>

          <p className="eyebrow">
            Market Intelligence
          </p>

          <h1>
            Market Movers
          </h1>

          <p className="page-subtitle">
            Biggest changes between opening
            and current bookmaker odds.
          </p>

        </div>

      </div>


      <div className="market-movers-toolbar">

        <select
          value={marketFilter}
          onChange={
            (event) =>
              setMarketFilter(
                event.target.value
              )
          }
          className="filter-select"
        >
          <option value="ALL">
            All markets
          </option>

          <option value="HOME">
            Home
          </option>

          <option value="DRAW">
            Draw
          </option>

          <option value="AWAY">
            Away
          </option>

        </select>


        <select
          value={directionFilter}
          onChange={
            (event) =>
              setDirectionFilter(
                event.target.value
              )
          }
          className="filter-select"
        >
          <option value="ALL">
            All movement
          </option>

          <option value="DROP">
            Odds drops
          </option>

          <option value="RISE">
            Odds rises
          </option>

        </select>

      </div>


      <div className="market-movers-list">

        {filteredMovers.map(
          (item, index) => (

            <Link
              key={
                `${item.match_id}-${item.market}`
              }
              to={
                `/matches/${item.match_id}`
              }
              className="market-mover-row"
            >

              <div className="market-mover-rank">
                #{index + 1}
              </div>


              <div className="market-mover-info">

                <span>
                  {item.league}
                </span>

                <strong>
                  {item.home_team}
                  {" vs "}
                  {item.away_team}
                </strong>

                <small>
                  {new Date(
                    item.match_date
                  ).toLocaleString()}
                </small>

              </div>


              <div className="market-mover-market">

                <span>
                  Market
                </span>

                <strong>
                  {item.market}
                </strong>

              </div>


              <div className="market-mover-opening">

                <span>
                  Opening
                </span>

                <strong>
                  {item.opening_odd.toFixed(2)}
                </strong>

              </div>


              <div className="market-mover-current">

                <span>
                  Current
                </span>

                <strong>
                  {item.current_odd.toFixed(2)}
                </strong>

              </div>


              <div
                className={
                  item.direction === "DROP"
                    ? "market-mover-change market-mover-change--drop"
                    : "market-mover-change market-mover-change--rise"
                }
              >

                <span>
                  Change
                </span>

                <strong>
                  {
                    item.direction
                    === "DROP"
                      ? "↓"
                      : "↑"
                  }
                  {" "}
                  {
                    Math.abs(
                      item.change_percentage
                    ).toFixed(1)
                  }
                  %
                </strong>

              </div>

            </Link>

          )
        )}

      </div>


      {filteredMovers.length === 0 && (

        <div className="matches-empty">

          <h3>
            No market movement yet
          </h3>

          <p>
            At least two odds snapshots
            are required to calculate movement.
          </p>

        </div>

      )}

    </div>
  );
}


export default MarketMovers;