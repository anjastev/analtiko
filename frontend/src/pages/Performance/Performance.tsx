import {
  useEffect,
  useState,
} from "react";

import {
  Activity,
  BarChart3,
  Target,
  TrendingUp,
} from "lucide-react";

import {
  getPerformanceStats,
} from "../../services/api";

import type {
  PerformanceStats,
} from "../../types/intelligence";


function Performance() {

  const [
    stats,
    setStats,
  ] =
    useState<PerformanceStats | null>(
      null
    );

  const [
    loading,
    setLoading,
  ] = useState(true);


  useEffect(() => {

    getPerformanceStats()
      .then(
        setStats
      )
      .catch(
        (error) => {
          console.error(
            error
          );
        }
      )
      .finally(
        () =>
          setLoading(false)
      );

  }, []);


  if (loading) {

    return (
      <div className="page">
        Loading performance...
      </div>
    );

  }


  if (!stats) {

    return (
      <div className="page">
        Performance data unavailable.
      </div>
    );

  }


  return (
    <div className="page">

      <header className="page-hero">

        <div>

          <p className="eyebrow">
            Historical Validation
          </p>

          <h1>
            Performance
          </h1>

          <p className="page-subtitle">
            Prospective production results,
            hit rate, profit and ROI.
          </p>

        </div>

      </header>


      <div className="performance-grid">

        <PerformanceCard
          icon={Target}
          title="VALUE Hit Rate"
          value={
            `${stats.value_signals.hit_rate.toFixed(1)}%`
          }
          helper={
            `${stats.value_signals.wins} wins / `
            + `${stats.value_signals.evaluated} evaluated`
          }
        />

        <PerformanceCard
          icon={TrendingUp}
          title="VALUE ROI"
          value={
            `${stats.value_signals.roi >= 0 ? "+" : ""}`
            + `${stats.value_signals.roi.toFixed(1)}%`
          }
          helper={
            `${stats.value_signals.profit_units >= 0 ? "+" : ""}`
            + `${stats.value_signals.profit_units.toFixed(2)}u`
          }
        />

        <PerformanceCard
          icon={BarChart3}
          title="Ticket Hit Rate"
          value={
            `${stats.combinations.hit_rate.toFixed(1)}%`
          }
          helper={
            `${stats.combinations.wins} wins / `
            + `${stats.combinations.evaluated} evaluated`
          }
        />

        <PerformanceCard
          icon={Activity}
          title="Ticket ROI"
          value={
            `${stats.combinations.roi >= 0 ? "+" : ""}`
            + `${stats.combinations.roi.toFixed(1)}%`
          }
          helper={
            `${stats.combinations.profit_units >= 0 ? "+" : ""}`
            + `${stats.combinations.profit_units.toFixed(2)}u`
          }
        />

      </div>

    </div>
  );
}


interface PerformanceCardProps {
  icon: React.ElementType;
  title: string;
  value: string;
  helper: string;
}


function PerformanceCard({
  icon: Icon,
  title,
  value,
  helper,
}: PerformanceCardProps) {

  return (
    <article className="performance-card">

      <div className="performance-card__icon">
        <Icon size={21} />
      </div>

      <span>
        {title}
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


export default Performance;