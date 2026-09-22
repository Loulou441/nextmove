"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

const NAV_ITEMS = [
  { href: "/me", label: "Me", icon: "👤" },
  { href: "/library", label: "Library", icon: "📚" },
  { href: "/upload", label: "Upload", icon: "⬆️" },
];

const SECONDARY_NAV_ITEMS = [
  { href: "/stats", label: "Évolution", icon: "📈" },
  { href: "/library/compare", label: "Comparer", icon: "⚖️" },
  { href: "/training-plan", label: "Programme", icon: "📋" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="no-print hidden md:flex md:flex-col w-64 shrink-0 bg-nm-card border-r border-nm-border h-screen sticky top-0 p-6">
      <div className="flex items-center gap-2 mb-8">
        <span className="text-2xl">🏓</span>
        <span className="text-lg font-bold text-nm-text">NextMove</span>
      </div>

      <nav className="flex flex-col gap-1">
        {NAV_ITEMS.map(({ href, label, icon }) => {
          const isActive = pathname.startsWith(href) && href !== "/library" || pathname === "/library";
          const active = href === "/library" ? pathname === "/library" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-2.5 px-4 py-2.5 rounded-nm-button text-sm font-medium transition-colors ${
                active ? "bg-nm-green-light text-nm-green" : "text-nm-text-tertiary hover:bg-nm-bg"
              }`}
            >
              <span>{icon}</span>
              {label}
            </Link>
          );
        })}
      </nav>

      <p className="text-[11px] font-semibold text-nm-text-secondary uppercase tracking-wide mt-6 mb-2 px-4">
        Analyse
      </p>
      <nav className="flex flex-col gap-1">
        {SECONDARY_NAV_ITEMS.map(({ href, label, icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-2.5 px-4 py-2.5 rounded-nm-button text-sm font-medium transition-colors ${
                active ? "bg-nm-green-light text-nm-green" : "text-nm-text-tertiary hover:bg-nm-bg"
              }`}
            >
              <span>{icon}</span>
              {label}
            </Link>
          );
        })}
      </nav>

      <div className="mt-auto pt-6 border-t border-nm-border">
        {user && (
          <p className="text-xs text-nm-text-secondary mb-2 truncate">{user.email}</p>
        )}
        <button
          onClick={logout}
          className="text-sm font-semibold text-nm-red"
        >
          Se déconnecter
        </button>
      </div>
    </aside>
  );
}