import type {
  PredictionComparison,
  PredictionProbabilities,
} from "../../types/predictionComparison";


interface Props {
  comparison: PredictionComparison;
}


function formatPick(
  pick: "HOME" | "DRAW" | "AWAY",
  homeTeam: string,
  awayTeam: string,
) {
  if (pick === "HOME") {
    return homeTeam;
  }

  if (pick === "AWAY") {
    return awayTeam;
  }

  return "Draw";
}


function ProbabilityBars({
  probabilities,
  homeTeam,
  awayTeam,
}: {
  probabilities: PredictionProbabilities;
  homeTeam: string;
  awayTeam: string;
}) {
  const rows = [
    {
      label: homeTeam,
      value: probabilities.HOME,
    },
    {
      label: "Draw",
      value: probabilities.DRAW,
    },
    {
      label: awayTeam,
      value: probabilities.AWAY,
    },
  ];


  return (
    <div className="comparison-probabilities">

      {rows.map((row) => (

        <div
          className="comparison-probability"
          key={row.label}
        >

          <div className="comparison-probability__header">

            <span>
              {row.label}
            </span>

            <strong>
              {row.value.toFixed(1)}%
            </strong>

          </div>


          <div className="comparison-probability__track">

            <div
              className="comparison-probability__fill"
              style={{
                width:
                  `${Math.min(
                    row.value,
                    100,
                  )}%`,
              }}
            />

          </div>

        </div>

      ))}

    </div>
  );
}


function PredictionComparisonCard({
  comparison,
}: Props) {

  const {
    home_team,
    away_team,
    rule_engine,
    ml_model,
  } = comparison;


  return (
    <section className="prediction-comparison-card">

      <div className="prediction-comparison-card__header">

        <div>

          <p className="eyebrow">
            Prediction Intelligence
          </p>

          <h2>
            Rule Engine vs ML
          </h2>

        </div>


        <div
          className={
            comparison.comparison.agreement
              ? "comparison-status comparison-status--agree"
              : "comparison-status comparison-status--disagree"
          }
        >

          {comparison.comparison.agreement
            ? "Models agree"
            : "Models disagree"}

        </div>

      </div>


      <div className="prediction-comparison-grid">

        {/* ==================================================
            RULE ENGINE
        ================================================== */}

        <article className="prediction-model-card">

          <div className="prediction-model-card__top">

            <div>

              <span className="prediction-model-card__label">
                Rule Engine
              </span>

              <h3>
                {formatPick(
                  rule_engine.pick,
                  home_team,
                  away_team,
                )}
              </h3>

            </div>


            <div className="prediction-confidence">

              <strong>
                {rule_engine.confidence.toFixed(
                  1,
                )}%
              </strong>

              <span>
                confidence
              </span>

            </div>

          </div>


          <ProbabilityBars
            probabilities={
              rule_engine.probabilities
            }
            homeTeam={home_team}
            awayTeam={away_team}
          />


          <div className="prediction-model-card__stats">

            <div>

              <span>
                Over 2.5
              </span>

              <strong>
                {rule_engine.over_25.toFixed(
                  1,
                )}%
              </strong>

            </div>


            <div>

              <span>
                BTTS
              </span>

              <strong>
                {rule_engine.btts_yes.toFixed(
                  1,
                )}%
              </strong>

            </div>

          </div>

        </article>


        {/* ==================================================
            ML MODEL
        ================================================== */}

        <article className="prediction-model-card prediction-model-card--ml">

          <div className="prediction-model-card__top">

            <div>

              <span className="prediction-model-card__label">
                ML Model
              </span>

              <h3>
                {formatPick(
                  ml_model.pick,
                  home_team,
                  away_team,
                )}
              </h3>

            </div>


            <div
              className={
                `ml-confidence-badge ml-confidence-badge--${ml_model.confidence_level.toLowerCase()}`
              }
            >

              {
                ml_model.confidence_level
              }

            </div>

          </div>


          <ProbabilityBars
            probabilities={
              ml_model.probabilities
            }
            homeTeam={home_team}
            awayTeam={away_team}
          />


          <div className="prediction-model-card__stats">

            <div>

              <span>
                ML confidence
              </span>

              <strong>
                {ml_model.confidence.toFixed(
                  1,
                )}%
              </strong>

            </div>


            <div>

              <span>
                Margin
              </span>

              <strong>
                {ml_model.margin.toFixed(
                  1,
                )}%
              </strong>

            </div>


            <div>

              <span>
                Analitiko Score
              </span>

              <strong>
                {ml_model.analitiko_score.toFixed(
                  1,
                )}
              </strong>

            </div>


            <div>

              <span>
                Strong threshold
              </span>

              <strong>
                {ml_model.league_threshold.toFixed(
                  1,
                )}
              </strong>

            </div>

          </div>


          {ml_model.is_strong_pick && (

            <div className="strong-pick-banner">

              Strong ML signal

            </div>

          )}

        </article>

      </div>


      <div className="comparison-summary">

        <div>

          <span>
            Rule pick probability
          </span>

          <strong>
            {
              comparison
                .comparison
                .rule_selected_probability
                .toFixed(1)
            }%
          </strong>

        </div>


        <div>

          <span>
            ML pick probability
          </span>

          <strong>
            {
              comparison
                .comparison
                .ml_selected_probability
                .toFixed(1)
            }%
          </strong>

        </div>


        <div>

          <span>
            Difference
          </span>

          <strong>
            {
              comparison
                .comparison
                .probability_difference
                .toFixed(1)
            }%
          </strong>

        </div>

      </div>


      <p className="prediction-experimental-note">
        {comparison.warning}
      </p>

    </section>
  );
}


export default PredictionComparisonCard;