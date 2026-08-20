import {
  AlertTriangle,
  CheckCircle2,
  ShieldCheck,
  Target,
  TrendingUp,
} from "lucide-react";

import type {
  OptimizedTicket,
} from "../../types/intelligence";


interface Props {
  ticket: OptimizedTicket;
}


function OptimizedTicketCard({
  ticket,
}: Props) {

  const strategyClass =
    ticket.strategy.toLowerCase();


  if (
    !ticket.success
    || !ticket.metrics
  ) {

    return (
      <article className="optimized-ticket optimized-ticket--empty">

        <div className="optimized-ticket__top">

          <span
            className={
              `strategy-badge strategy-badge--${strategyClass}`
            }
          >
            {ticket.strategy}
          </span>

        </div>


        <div className="optimized-ticket__empty">

          <AlertTriangle size={22} />

          <strong>
            No qualified ticket
          </strong>

          <p>
            {ticket.message}
          </p>

          <span>
            {
              ticket.candidates_found
            } candidates available
          </span>

        </div>

      </article>
    );
  }


  return (
    <article className="optimized-ticket">

      <div className="optimized-ticket__top">

        <div>

          <span
            className={
              `strategy-badge strategy-badge--${strategyClass}`
            }
          >
            {ticket.strategy}
          </span>

          <h3>
            Today's Optimized Ticket
          </h3>

        </div>


        <div className="optimized-ticket__quality">

          <span>
            QUALITY
          </span>

          <strong>
            {
              ticket.metrics
                .average_quality
                .toFixed(1)
            }
          </strong>

        </div>

      </div>


      <div className="optimized-ticket__summary">

        <div>

          <TrendingUp size={16} />

          <span>
            Total Odds
          </span>

          <strong>
            {
              ticket.metrics
                .total_odds
                .toFixed(2)
            }
          </strong>

        </div>


        <div>

          <Target size={16} />

          <span>
            Estimated
          </span>

          <strong>
            {
              ticket.metrics
                .estimated_probability
                .toFixed(1)
            }%
          </strong>

        </div>


        <div>

          <ShieldCheck size={16} />

          <span>
            Uncertainty
          </span>

          <strong>
            {
              ticket.metrics
                .average_uncertainty
                .toFixed(1)
            }%
          </strong>

        </div>

      </div>


      <div className="optimized-ticket__selections">

        {ticket.selections.map(
          (
            selection,
            index,
          ) => (

            <div
              className="optimized-selection"
              key={
                selection.signal_id
              }
            >

              <div className="optimized-selection__index">

                {index + 1}

              </div>


              <div className="optimized-selection__match">

                <strong>
                  {
                    selection.match
                  }
                </strong>

                <span>
                  {
                    selection.league
                  }
                </span>

              </div>


              <div className="optimized-selection__pick">

                <span>
                  {
                    selection.market
                  }
                </span>

                <strong>
                  {
                    selection.selection
                  }
                </strong>

              </div>


              <div className="optimized-selection__probability">

                <span>
                  Probability
                </span>

                <strong>
                  {
                    selection
                      .calibrated_probability
                      .toFixed(1)
                  }%
                </strong>

              </div>


              <div className="optimized-selection__quality">

                <span>
                  Quality
                </span>

                <strong>
                  {
                    selection
                      .quality_score
                      .toFixed(1)
                  }{" "}
                  {
                    selection
                      .quality_tier
                  }
                </strong>

              </div>


              <div className="optimized-selection__price">

                <span>
                  Odds
                </span>

                <strong>
                  {
                    selection.odds
                      .toFixed(2)
                  }
                </strong>

              </div>

            </div>

          )
        )}

      </div>


      <div className="optimized-ticket__footer">

        <div>

          <CheckCircle2 size={14} />

          <span>
            {
              ticket
                .candidates_found
            } qualified candidates
          </span>

        </div>


        <div>

          Avg edge

          <strong>
            +
            {
              ticket.metrics
                .average_edge
                .toFixed(1)
            }%
          </strong>

        </div>

      </div>

    </article>
  );
}


export default OptimizedTicketCard;