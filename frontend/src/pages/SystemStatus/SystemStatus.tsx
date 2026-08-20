import {
  useEffect,
  useState,
} from "react";

import {
  Activity,
  Database,
  Radio,
  ShieldCheck,
} from "lucide-react";

import {
  getBackendHealth,
} from "../../services/api";

import type {
  BackendHealth,
} from "../../types/intelligence";


function SystemStatus() {

  const [
    health,
    setHealth,
  ] = useState<BackendHealth | null>(
    null
  );

  const [
    loading,
    setLoading,
  ] = useState(true);

  const [
    error,
    setError,
  ] = useState("");


  useEffect(() => {

    async function load() {

      try {

        setLoading(true);
        setError("");

        const result =
          await getBackendHealth();

        setHealth(
          result
        );

      } catch (err) {

        console.error(
          "System status error:",
          err
        );

        setError(
          "Could not load backend health."
        );

      } finally {

        setLoading(false);

      }
    }


    load();

  }, []);


  if (loading) {

    return (
      <div className="page">

        <div className="dashboard-loading">

          <div className="dashboard-loader" />

          <p>
            Loading system status...
          </p>

        </div>

      </div>
    );

  }


  if (
    error
    || !health
  ) {

    return (
      <div className="page">

        <div className="frontend-alert frontend-alert--error">

          <strong>
            System status unavailable
          </strong>

          <span>
            {error || "No health data."}
          </span>

        </div>

      </div>
    );

  }


  return (
    <div className="page">

      <header className="page-hero">

        <div>

          <p className="eyebrow">
            Production
          </p>

          <h1>
            System Status
          </h1>

          <p className="page-subtitle">
            Current production data coverage,
            signals and market-data health.
          </p>

        </div>


        <span
          className={
            `system-health-badge system-health-badge--${
              health.status.toLowerCase()
            }`
          }
        >

          <Radio size={15} />

          {health.status}

        </span>

      </header>


      <div className="system-health-grid">

        <HealthCard
          icon={ShieldCheck}
          label="Production Ready"
          value={
            `${health.production_ready_matches}/`
            + `${health.upcoming_matches}`
          }
          helper={
            `${health.production_coverage.toFixed(1)}% coverage`
          }
        />


        <HealthCard
          icon={Activity}
          label="Active Signals"
          value={
            health.active_signals
          }
          helper="Current production signals"
        />


        <HealthCard
          icon={Database}
          label="VALUE Signals"
          value={
            health.value_signals
          }
          helper="Executable VALUE candidates"
        />


        <HealthCard
          icon={Database}
          label="Fresh Odds"
          value={
            health.fresh_odds_rows
          }
          helper="Fresh normalized market prices"
        />

      </div>

    </div>
  );
}


interface HealthCardProps {

  icon:
    React.ElementType;

  label:
    string;

  value:
    string | number;

  helper:
    string;
}


function HealthCard({
  icon: Icon,
  label,
  value,
  helper,
}: HealthCardProps) {

  return (
    <article className="performance-card">

      <div className="performance-card__icon">

        <Icon size={21} />

      </div>


      <span>
        {label}
      </span>


      <strong>
        {value}
      </strong>


      <small>
        {helper}
      </small>

    </article>
  );
}


export default SystemStatus;