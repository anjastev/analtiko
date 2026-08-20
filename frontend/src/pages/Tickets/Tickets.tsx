import {
  useEffect,
  useState,
} from "react";

import {
  CalendarDays,
  RefreshCw,
  Sparkles,
} from "lucide-react";

import {
  getOptimizedTickets,
} from "../../services/api";

import OptimizedTicketCard
  from "../../components/tickets/OptimizedTicketCard";

import type {
  OptimizedTicketsResponse,
} from "../../types/intelligence";


function Tickets() {

  const [
    data,
    setData,
  ] = useState<
    OptimizedTicketsResponse | null
  >(null);


  const [
    loading,
    setLoading,
  ] = useState(true);


  const [
    error,
    setError,
  ] = useState("");


  const [
    days,
    setDays,
  ] = useState(1);


  async function load() {

    try {

      setLoading(true);
      setError("");

      const result =
        await getOptimizedTickets(
          days
        );

      setData(
        result
      );

    } catch (err) {

      console.error(
        "Tickets error:",
        err
      );

      setError(
        "Could not load optimized tickets."
      );

    } finally {

      setLoading(false);

    }
  }


  useEffect(() => {

    load();

  }, [
    days,
  ]);


  return (
    <div className="page">

      <header className="page-hero">

        <div>

          <p className="eyebrow">
            Production Intelligence
          </p>

          <h1>
            Optimized Tickets
          </h1>

          <p className="page-subtitle">
            Production-qualified combinations
            generated from live signals,
            executable odds, quality scoring
            and uncertainty controls.
          </p>

        </div>


        <button
          className="refresh-button"
          onClick={load}
          disabled={loading}
        >

          <RefreshCw
            size={16}
            className={
              loading
                ? "spin"
                : ""
            }
          />

          Refresh

        </button>

      </header>


      <div className="tickets-toolbar">

        <div className="tickets-toolbar__title">

          <CalendarDays size={17} />

          <span>
            Time window
          </span>

        </div>


        <div className="tickets-day-tabs">

          <button
            className={
              days === 1
                ? "active"
                : ""
            }
            onClick={() =>
              setDays(1)
            }
          >
            Today
          </button>

          <button
            className={
              days === 2
                ? "active"
                : ""
            }
            onClick={() =>
              setDays(2)
            }
          >
            Today + Tomorrow
          </button>

        </div>

      </div>


      {loading && (

        <div className="dashboard-loading">

          <div className="dashboard-loader" />

          <p>
            Optimizing tickets...
          </p>

        </div>

      )}


      {!loading && error && (

        <div className="frontend-alert frontend-alert--error">

          <strong>
            Tickets unavailable
          </strong>

          <span>
            {error}
          </span>

        </div>

      )}


      {!loading
        && !error
        && data
        && (

          <>

            <div className="ticket-intelligence-banner">

              <Sparkles size={18} />

              <div>

                <strong>
                  Live optimization active
                </strong>

                <span>
                  Tickets are generated from
                  current production-qualified
                  signals. Weaker picks are not
                  added just to fill a ticket.
                </span>

              </div>

            </div>


            <div className="optimized-ticket-grid">

              {data.tickets.map(
                (ticket) => (

                  <OptimizedTicketCard
                    key={
                      ticket.strategy
                    }
                    ticket={
                      ticket
                    }
                  />

                )
              )}

            </div>

          </>

        )
      }

    </div>
  );
}


export default Tickets;