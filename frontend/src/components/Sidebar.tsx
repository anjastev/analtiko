import {
  NavLink,
} from "react-router-dom";

import {
  Activity,
  BarChart3,
  Bot,
  Brain,
  CalendarDays,
  ChartNoAxesCombined,
  CircleDollarSign,
  Gauge,
  LayoutDashboard,
  ListChecks,
  Settings,
  ShieldCheck,
  TrendingUp,
  Trophy,
  Users,
    TicketCheck,
} from "lucide-react";


interface SidebarItem {
  to: string;
  label: string;
  icon: React.ElementType;
}


interface SidebarSection {
  title: string;
  items: SidebarItem[];
}


function Sidebar() {

  const sections: SidebarSection[] = [

    {
      title: "Overview",

      items: [
        {
          to: "/",
          label: "Dashboard",
          icon: LayoutDashboard,
        },
          {
  to: "/tickets",
  label: "Today's Tickets",
  icon: TicketCheck,
},
      ],
    },

    {
      title: "Intelligence",

      items: [
        {
          to: "/tickets",
          label: "Tickets",
          icon: ListChecks,
        },

        {
          to: "/ticket-builder",
          label: "AI Ticket Builder",
          icon: Bot,
        },

        {
          to: "/predictions",
          label: "Predictions",
          icon: Brain,
        },

        {
          to: "/trending",
          label: "Trending",
          icon: TrendingUp,
        },

        {
          to: "/market-movers",
          label: "Market Movers",
          icon: Activity,
        },
      ],
    },

    {
      title: "Football",

      items: [
        {
          to: "/matches",
          label: "Matches",
          icon: CalendarDays,
        },

        {
          to: "/leagues",
          label: "Leagues",
          icon: Trophy,
        },

        {
          to: "/teams",
          label: "Teams",
          icon: Users,
        },
      ],
    },

    {
      title: "Insights",

      items: [
        {
          to: "/analytics",
          label: "Analytics",
          icon: BarChart3,
        },

        {
          to: "/value-analytics",
          label: "Value Analytics",
          icon: CircleDollarSign,
        },

        {
          to: "/performance",
          label: "Performance",
          icon: ChartNoAxesCombined,
        },
      ],
    },

    {
      title: "System",

      items: [
        {
          to: "/system",
          label: "System Status",
          icon: ShieldCheck,
        },

        {
          to: "/admin",
          label: "Admin",
          icon: Settings,
        },
      ],
    },
  ];


  return (
    <aside className="sidebar">

      <div className="sidebar__logo">

        <span className="logo-mark">
          A
        </span>

        <div className="sidebar__brand">

          <strong>
            Analitiko
          </strong>

          <small>
            Sports Intelligence
          </small>

        </div>

      </div>


      <nav className="sidebar__nav">

        {sections.map(
          (section) => (

            <div
              className="sidebar__section"
              key={section.title}
            >

              <span className="sidebar__section-title">
                {section.title}
              </span>


              {section.items.map(
                ({
                  to,
                  label,
                  icon: Icon,
                }) => (

                  <NavLink
                    key={to}
                    to={to}
                    end={to === "/"}
                    className={({
                      isActive,
                    }) =>
                      `sidebar__link ${
                        isActive
                          ? "sidebar__link--active"
                          : ""
                      }`
                    }
                  >

                    <Icon size={18} />

                    <span>
                      {label}
                    </span>

                  </NavLink>

                )
              )}

            </div>

          )
        )}

      </nav>


      <div className="sidebar__footer">

        <Gauge size={16} />

        <div>

          <strong>
            Production
          </strong>

          <small>
            Football engine
          </small>

        </div>

      </div>

    </aside>
  );
}


export default Sidebar;