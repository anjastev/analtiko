import {
  BrowserRouter,
  Route,
  Routes,
} from "react-router-dom";

import MainLayout from "./layouts/MainLayout";

import Dashboard from "./pages/Dashboard/Dashboard";
import Matches from "./pages/Matches/Matches";
import MatchDetails from "./pages/MatchDetails/MatchDetails";
import Predictions from "./pages/Predictions/Predictions";
import Trending from "./pages/Trending/Trending";
import MarketMovers from "./pages/MarketMovers/MarketMovers";

import Teams from "./pages/Teams/Teams";
import TeamDetails from "./pages/TeamDetails/TeamDetails";

import Leagues from "./pages/Leagues/Leagues";
import LeagueDetails from "./pages/LeagueDetails/LeagueDetails";

import Analytics from "./pages/Analytics/Analytics";
import ValueAnalytics from "./pages/ValueAnalytics/ValueAnalytics";

import Tickets from "./pages/Tickets/Tickets";
import TicketBuilder from "./pages/TicketBuilder/TicketBuilder";
import Performance from "./pages/Performance/Performance";
import SystemStatus from "./pages/SystemStatus/SystemStatus";

import Admin from "./pages/Admin/Admin";

import "./index.css";


function App() {
  return (
    <BrowserRouter>

      <Routes>

        <Route element={<MainLayout />}>

          {/* OVERVIEW */}

          <Route
            path="/"
            element={<Dashboard />}
          />


          {/* INTELLIGENCE */}

          <Route
            path="/tickets"
            element={<Tickets />}
          />

          <Route
            path="/ticket-builder"
            element={<TicketBuilder />}
          />

          <Route
            path="/predictions"
            element={<Predictions />}
          />

          <Route
            path="/trending"
            element={<Trending />}
          />

          <Route
            path="/market-movers"
            element={<MarketMovers />}
          />


          {/* FOOTBALL */}

          <Route
            path="/matches"
            element={<Matches />}
          />

          <Route
            path="/matches/:id"
            element={<MatchDetails />}
          />

          <Route
            path="/teams"
            element={<Teams />}
          />

          <Route
            path="/teams/:id"
            element={<TeamDetails />}
          />

          <Route
            path="/leagues"
            element={<Leagues />}
          />

          <Route
            path="/leagues/:id"
            element={<LeagueDetails />}
          />


          {/* INSIGHTS */}

          <Route
            path="/analytics"
            element={<Analytics />}
          />

          <Route
            path="/value-analytics"
            element={<ValueAnalytics />}
          />

          <Route
            path="/performance"
            element={<Performance />}
          />


          {/* SYSTEM */}

          <Route
            path="/system"
            element={<SystemStatus />}
          />

          <Route
            path="/admin"
            element={<Admin />}
          />

        </Route>

      </Routes>

    </BrowserRouter>
  );
}


export default App;