import axios from "axios";

import type {
  BackendHealth,
  DashboardPayload,
  PerformanceStats,
  Signal,
  Ticket,
  TicketBuilderRequest,
  TicketBuilderResponse,
    OptimizedTicketsResponse,
} from "../types/intelligence";



const api = axios.create({
  baseURL:
    import.meta.env.VITE_API_BASE_URL
    || "http://127.0.0.1:8002",
});

export default api;




/* ============================================================
   DASHBOARD
============================================================ */

export async function getDashboard() {

  const response =
    await api.get<DashboardPayload>(
      "/api/dashboard"
    );

  return response.data;
}


/* ============================================================
   HEALTH
============================================================ */

export async function getBackendHealth() {

  const response =
    await api.get<BackendHealth>(
      "/api/health"
    );

  return response.data;
}


/* ============================================================
   TICKETS
============================================================ */

export async function getTickets(
  status?: string,
) {

  const response =
    await api.get<{
      count: number;
      items: Ticket[];
    }>(
      "/api/combinations",
      {
        params:
          status
            ? {
                status,
              }
            : undefined,
      }
    );

  return response.data;
}


export async function getTicket(
  id: number,
) {

  const response =
    await api.get<Ticket>(
      `/api/combinations/${id}`
    );

  return response.data;
}


/* ============================================================
   VALUE SIGNALS
============================================================ */

export async function getValueSignals() {

  const response =
    await api.get<{
      count: number;
      items: Signal[];
    }>(
      "/api/signals/value"
    );

  return response.data;
}


/* ============================================================
   PERFORMANCE
============================================================ */

export async function getPerformanceStats() {

  const response =
    await api.get<PerformanceStats>(
      "/api/stats"
    );

  return response.data;
}

/* ============================================================
   AI TICKET BUILDER
============================================================ */

export async function buildAiTicket(
  request: TicketBuilderRequest,
) {

  const response =
    await api.post<TicketBuilderResponse>(
      "/api/ticket-builder",
      request
    );

  return response.data;
}

export async function getOptimizedTickets(
  days = 1,
) {

  const response =
    await api.get<OptimizedTicketsResponse>(
      "/api/optimized-tickets",
      {
        params: {
          days,
        },
      }
    );

  return response.data;
}