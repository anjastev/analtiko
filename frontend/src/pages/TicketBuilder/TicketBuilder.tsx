import {
  useEffect,
  useRef,
  useState,
} from "react";

import type {
  FormEvent,
} from "react";

import {
  Bot,
  CalendarDays,
  CheckCircle2,
  CircleDollarSign,
  Send,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
} from "lucide-react";

import {
  buildAiTicket,
} from "../../services/api";

import type {
  TicketBuilderResponse,
} from "../../types/intelligence";


interface ChatMessage {
  id: number;

  role:
    | "user"
    | "assistant";

  content: string;

  ticket?:
    TicketBuilderResponse;
}


const suggestions = [
  "Build me a SAFE ticket for today with 3 matches.",

  "Champions League tomorrow, balanced ticket, 3 matches.",

  "Give me a SAFE ticket around 2.50 odds.",

  "Only use picks above 75% probability.",
];


function TicketBuilder() {

  const [
    message,
    setMessage,
  ] = useState("");


  const [
    loading,
    setLoading,
  ] = useState(false);


  const [
    conversation,
    setConversation,
  ] = useState<ChatMessage[]>([
    {
      id: 1,

      role:
        "assistant",

      content:
        "Tell me what kind of ticket you want. "
        + "You can specify the day, leagues, "
        + "risk level, number of selections, "
        + "minimum probability or target odds.",
    },
  ]);


  const nextId =
    useRef(2);


  const bottomRef =
    useRef<HTMLDivElement | null>(
      null
    );


  useEffect(() => {

    bottomRef.current
      ?.scrollIntoView({
        behavior:
          "smooth",
      });

  }, [
    conversation,
    loading,
  ]);


  async function submit(
    event: FormEvent,
  ) {

    event.preventDefault();

    const value =
      message.trim();

    if (
      !value
      || loading
    ) {
      return;
    }


    const userMessage: ChatMessage = {
      id:
        nextId.current++,

      role:
        "user",

      content:
        value,
    };


    setConversation(
      (current) => [
        ...current,
        userMessage,
      ]
    );


    setMessage("");

    setLoading(true);


    try {

      const result =
        await buildAiTicket({
          message:
            value,
        });


      const assistantMessage:
        ChatMessage = {

        id:
          nextId.current++,

        role:
          "assistant",

        content:
          result.message,

        ticket:
          result,
      };


      setConversation(
        (current) => [
          ...current,
          assistantMessage,
        ]
      );

    } catch (error) {

      console.error(
        "Ticket builder error:",
        error
      );


      setConversation(
        (current) => [
          ...current,

          {
            id:
              nextId.current++,

            role:
              "assistant",

            content:
              "I could not reach the "
              + "Analitiko ticket engine. "
              + "Please try again.",
          },
        ]
      );

    } finally {

      setLoading(false);

    }
  }


  return (
    <div className="page">

      <header className="page-hero">

        <div>

          <p className="eyebrow">
            Conversational Intelligence
          </p>

          <h1>
            AI Ticket Builder
          </h1>

          <p className="page-subtitle">
            Describe what you want and
            Analitiko will search the current
            production-qualified football
            opportunities.
          </p>

        </div>


        <div className="page-hero__icon">
          <Bot size={30} />
        </div>

      </header>


      <div className="ticket-builder-layout">

        <section className="ticket-builder-chat">

          <div className="ticket-builder-chat__header">

            <div className="ticket-builder-avatar">
              <Sparkles size={19} />
            </div>


            <div>

              <strong>
                Analitiko AI
              </strong>

              <span>
                Production Ticket Intelligence
              </span>

            </div>


            <div className="ticket-builder-online">

              <span />

              Live

            </div>

          </div>


          <div className="ticket-builder-messages">

            {conversation.map(
              (item) => (

                <div
                  key={item.id}
                  className={
                    `chat-message chat-message--${
                      item.role
                    }`
                  }
                >

                  {item.role
                    === "assistant"
                    && (
                      <Bot size={17} />
                    )
                  }


                  <div className="chat-message__content">

                    <p>
                      {item.content}
                    </p>


                    {item.ticket
                      && (
                        <GeneratedTicket
                          ticket={
                            item.ticket
                          }
                        />
                      )
                    }

                  </div>

                </div>

              )
            )}


            {loading && (

              <div className="chat-message chat-message--assistant">

                <Bot size={17} />

                <div className="chat-message__content">

                  <div className="ticket-builder-thinking">

                    <span />
                    <span />
                    <span />

                    <small>
                      Searching production signals...
                    </small>

                  </div>

                </div>

              </div>

            )}


            <div ref={bottomRef} />

          </div>


          <div className="ticket-builder-suggestions">

            {suggestions.map(
              (suggestion) => (

                <button
                  type="button"
                  key={suggestion}
                  disabled={
                    loading
                  }
                  onClick={() =>
                    setMessage(
                      suggestion
                    )
                  }
                >
                  {suggestion}
                </button>

              )
            )}

          </div>


          <form
            className="ticket-builder-input"
            onSubmit={submit}
          >

            <textarea
              value={message}
              disabled={loading}
              onChange={(event) =>
                setMessage(
                  event.target.value
                )
              }
              onKeyDown={(event) => {

                if (
                  event.key
                  === "Enter"
                  &&
                  !event.shiftKey
                ) {

                  event.preventDefault();

                  event.currentTarget
                    .form
                    ?.requestSubmit();
                }

              }}
              placeholder={
                "Example: SAFE ticket for "
                + "tomorrow, Champions League, "
                + "3 selections around 2.50 odds..."
              }
            />


            <button
              type="submit"
              disabled={
                loading
                || !message.trim()
              }
            >

              <Send size={18} />

              {
                loading
                  ? "Building..."
                  : "Build"
              }

            </button>

          </form>

        </section>


        <aside className="ticket-builder-info">

          <ShieldCheck size={25} />

          <h3>
            Production rules stay active
          </h3>


          <p>
            Your request changes the search
            criteria. It does not bypass the
            Analitiko production rules.
          </p>


          <ul>

            <li>
              Production-ready match data
            </li>

            <li>
              Active validated markets
            </li>

            <li>
              Fresh executable bookmaker odds
            </li>

            <li>
              Positive VALUE edge
            </li>

            <li>
              Positive expected value
            </li>

            <li>
              Maximum one pick per match
            </li>

          </ul>


          <div className="ticket-builder-help">

            <strong>
              Try asking
            </strong>

            <span>
              “SAFE ticket for today”
            </span>

            <span>
              “3 Champions League picks”
            </span>

            <span>
              “Minimum 75% probability”
            </span>

            <span>
              “Around 2.50 total odds”
            </span>

          </div>

        </aside>

      </div>

    </div>
  );
}


/* ============================================================
   GENERATED TICKET
============================================================ */

function GeneratedTicket({
  ticket,
}: {
  ticket:
    TicketBuilderResponse;
}) {

  if (
    !ticket.success
    || ticket.selections.length
    === 0
  ) {

    return (
      <div className="ai-ticket-empty">

        <Target size={18} />

        <div>

          <strong>
            No eligible combination
          </strong>

          <span>
            {
              ticket
                .candidates_found
            } candidates matched
            before final selection.
          </span>

        </div>

      </div>
    );

  }


  return (
    <div className="ai-generated-ticket">

      <div className="ai-generated-ticket__header">

        <div>

          <span
            className={
              `ticket-strategy ticket-strategy--${
                ticket.strategy
                  .toLowerCase()
              }`
            }
          >
            {ticket.strategy}
          </span>

          <strong>
            Generated Ticket
          </strong>

        </div>


        <span className="ai-ticket-risk">

          <ShieldCheck size={13} />

          {
            ticket.risk_level
          }

        </span>

      </div>


      <div className="ai-generated-ticket__criteria">

        <span>
          <CalendarDays size={12} />

          {
            ticket
              .parsed_request
              .date
          }
        </span>


        <span>
          <Target size={12} />

          Min{" "}
          {
            ticket
              .parsed_request
              .min_probability
          }%
        </span>


        {ticket
          .parsed_request
          .target_odds
          !== null
          && (

            <span>

              <TrendingUp size={12} />

              Target{" "}
              {
                ticket
                  .parsed_request
                  .target_odds
              }

            </span>

          )
        }

      </div>


      <div className="ai-ticket-selections">

        {ticket.selections.map(
          (
            selection,
            index,
          ) => (

            <div
              className="ai-ticket-selection"
              key={
                selection.signal_id
              }
            >

              <div className="ai-ticket-selection__number">

                {index + 1}

              </div>


              <div className="ai-ticket-selection__main">

                <strong>
                  {
                    selection.match
                  }
                </strong>

                <span>
                  {
                    selection.league
                    ?? "Football"
                  }
                </span>

              </div>


              <div className="ai-ticket-selection__pick">

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


              <div className="ai-ticket-selection__prob">

                <span>
                  Model
                </span>

                <strong>
                  {
                    selection
                      .probability
                      .toFixed(1)
                  }%
                </strong>

              </div>


              <div className="ai-ticket-selection__edge">

                <span>
                  Edge
                </span>

                <strong>
                  {
                    selection.edge
                    !== null
                      ? `+${selection.edge.toFixed(1)}%`
                      : "—"
                  }
                </strong>

              </div>


              <div className="ai-ticket-selection__odds">

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


      <div className="ai-ticket-summary">

        <div>

          <CircleDollarSign
            size={16}
          />

          <span>
            Total Odds
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

          <Target size={16} />

          <span>
            Estimated Probability
          </span>

          <strong>
            {
              ticket
                .estimated_probability
                ?.toFixed(1)
              ?? "—"
            }%
          </strong>

        </div>


        <div>

          <CheckCircle2
            size={16}
          />

          <span>
            Qualified
          </span>

          <strong>
            {
              ticket
                .selections
                .length
            }
          </strong>

        </div>

      </div>


      <div className="ai-ticket-disclaimer">

        Probabilities are model estimates,
        not guarantees of outcome.

      </div>

    </div>
  );
}


export default TicketBuilder;