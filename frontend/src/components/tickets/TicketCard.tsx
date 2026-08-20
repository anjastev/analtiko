import {
  Link,
} from "react-router-dom";

import {
  ChevronRight,
  ShieldCheck,
  Target,
  TrendingUp,
} from "lucide-react";

import type {
  Ticket,
} from "../../types/intelligence";


interface TicketCardProps {
  ticket: Ticket;
  compact?: boolean;
}


function strategyClass(
  strategy: string,
) {

  return (
    strategy
      .toLowerCase()
      .replace(
        /\s+/g,
        "-"
      )
  );
}


function TicketCard({
  ticket,
  compact = false,
}: TicketCardProps) {

  const strategy =
    ticket.strategy.toUpperCase();

  return (
    <article
      className={
        `ticket-card ${
          compact
            ? "ticket-card--compact"
            : ""
        }`
      }
    >

      <div className="ticket-card__header">

        <div>

          <span
            className={
              `ticket-strategy ticket-strategy--${
                strategyClass(
                  strategy
                )
              }`
            }
          >
            {strategy}
          </span>

          <h3>
            {ticket.name}
          </h3>

        </div>


        <div className="ticket-card__status">

          <span
            className={
              `ticket-status ticket-status--${
                ticket.status
              }`
            }
          >
            {ticket.status}
          </span>

        </div>

      </div>


      <div className="ticket-card__selections">

        {ticket.selections.map(
          (selection) => (

            <div
              className="ticket-selection"
              key={selection.id}
            >

              <div className="ticket-selection__match">

                <strong>
                  {selection.match
                    ?? `Match #${selection.match_id}`}
                </strong>

                <span>
                  {selection.selection}
                </span>

              </div>


              <div className="ticket-selection__numbers">

                {selection.probability
                  !== null && (

                    <span>
                      {selection.probability.toFixed(1)}%
                    </span>

                  )
                }

                {selection.odds
                  !== null && (

                    <strong>
                      {selection.odds.toFixed(2)}
                    </strong>

                  )
                }

              </div>

            </div>

          )
        )}

      </div>


      <div className="ticket-card__metrics">

        <div>

          <Target size={16} />

          <span>
            Probability
          </span>

          <strong>
            {
              ticket.estimated_probability
                ?.toFixed(1)
              ?? "—"
            }%
          </strong>

        </div>


        <div>

          <TrendingUp size={16} />

          <span>
            Total odds
          </span>

          <strong>
            {
              ticket.total_odds
                ?.toFixed(2)
              ?? "—"
            }
          </strong>

        </div>


        <div>

          <ShieldCheck size={16} />

          <span>
            Risk
          </span>

          <strong>
            {
              ticket.risk_score !== null
                ? `${ticket.risk_score.toFixed(1)}`
                : "—"
            }
          </strong>

        </div>

      </div>


      <Link
        to={`/tickets/${ticket.id}`}
        className="ticket-card__action"
        onClick={(event) => {
          // Until TicketDetails route is added,
          // keep card usable without navigating to 404.
          event.preventDefault();
        }}
      >

        View ticket

        <ChevronRight size={17} />

      </Link>

    </article>
  );
}


export default TicketCard;