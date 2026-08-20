import { useState } from "react";

import {
  CalendarSync,
  RefreshCw,
  History,
  Trophy,
  Brain,
  CheckCircle2,
} from "lucide-react";

import api from "../../services/api";

import type {
  AdminJobResponse,
} from "../../types/admin";


interface Job {
  id: string;
  title: string;
  description: string;
  endpoint: string;
  icon: React.ElementType;
}


const jobs: Job[] = [
  {
    id: "fixtures",
    title: "Sync Fixtures",
    description:
      "Fetch and update tracked football fixtures.",
    endpoint:
      "/api/admin/sync-fixtures",
    icon: CalendarSync,
  },

  {
    id: "odds",
    title: "Sync Odds",
    description:
      "Fetch the latest bookmaker odds.",
    endpoint:
      "/api/admin/sync-odds",
    icon: RefreshCw,
  },

  {
    id: "history",
    title: "Sync History",
    description:
      "Update recent team match history.",
    endpoint:
      "/api/admin/sync-history",
    icon: History,
  },

  {
    id: "results",
    title: "Sync Results",
    description:
      "Update final scores and match status.",
    endpoint:
      "/api/admin/sync-results",
    icon: Trophy,
  },

  {
    id: "snapshot",
    title: "Snapshot Predictions",
    description:
      "Store current model predictions.",
    endpoint:
      "/api/admin/snapshot-predictions",
    icon: Brain,
  },

  {
    id: "evaluation",
    title: "Evaluate Predictions",
    description:
      "Compare official predictions with results.",
    endpoint:
      "/api/admin/evaluate-predictions",
    icon: CheckCircle2,
  },
];


function Admin() {
  const [running, setRunning] =
    useState<string | null>(null);

  const [messages, setMessages] =
    useState<Record<string, string>>({});


  async function runJob(
    job: Job,
  ) {
    if (running) {
      return;
    }

    setRunning(job.id);

    setMessages(
      (current) => ({
        ...current,
        [job.id]: "",
      })
    );

    try {
      const response =
        await api.post<AdminJobResponse>(
          job.endpoint
        );

      setMessages(
        (current) => ({
          ...current,
          [job.id]:
            response.data.message,
        })
      );

    } catch (error) {
      console.error(
        `Failed to run ${job.title}:`,
        error
      );

      setMessages(
        (current) => ({
          ...current,
          [job.id]:
            "Job failed. Check backend terminal.",
        })
      );

    } finally {
      setRunning(null);
    }
  }


  return (
    <div className="page">

      <div className="page-header">

        <div>

          <p className="eyebrow">
            System Control
          </p>

          <h1>
            Admin
          </h1>

          <p className="page-subtitle">
            Manually run Analitiko data
            collection and model jobs.
          </p>

        </div>

      </div>


      <div className="admin-warning">

        <strong>
          Development mode
        </strong>

        <p>
          These actions call external APIs
          and may consume your daily quota.
        </p>

      </div>


      <div className="admin-grid">

        {jobs.map(
          (job) => {

            const Icon =
              job.icon;

            const isRunning =
              running === job.id;

            return (
              <div
                key={job.id}
                className="admin-card"
              >

                <div className="admin-card-icon">
                  <Icon size={22} />
                </div>


                <div className="admin-card-content">

                  <h3>
                    {job.title}
                  </h3>

                  <p>
                    {job.description}
                  </p>

                </div>


                <button
                  type="button"
                  className="admin-run-button"
                  disabled={
                    running !== null
                  }
                  onClick={
                    () =>
                      runJob(job)
                  }
                >
                  {isRunning
                    ? "Running..."
                    : "Run"
                  }
                </button>


                {messages[job.id] && (

                  <div className="admin-result">
                    {messages[job.id]}
                  </div>

                )}

              </div>
            );
          }
        )}

      </div>

    </div>
  );
}


export default Admin;