"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/me", label: "Me", icon: PersonIcon },
  { href: "/library", label: "Library", icon: LibraryIcon },
  { href: "/upload", label: "Upload", icon: UploadIcon },
];

export default function BottomTabBar() {
  const pathname = usePathname();

  return (
    <nav className="no-print md:hidden fixed left-1/2 -translate-x-1/2 bottom-3 z-50 w-[calc(100vw-24px)] max-w-md">
      <div className="flex justify-around items-center bg-white/97 backdrop-blur-xl border border-nm-border rounded-nm-nav shadow-lg px-2 py-2">
        {TABS.map(({ href, label, icon: Icon }) => {
          const isActive = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex flex-col items-center gap-0.5 px-4 py-1.5 rounded-2xl transition-colors ${
                isActive ? "bg-nm-green-light" : ""
              }`}
            >
              <Icon active={isActive} />
              <span
                className={`text-[11px] font-medium ${
                  isActive ? "text-nm-green" : "text-nm-text-tertiary"
                }`}
              >
                {label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}

function iconColor(active?: boolean) {
  return active ? "#34C759" : "#8E8E93";
}

function PersonIcon({ active }: { active?: boolean }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={iconColor(active)} strokeWidth="2">
      <circle cx="12" cy="8" r="4" />
      <path d="M4 20c0-4 3.6-6 8-6s8 2 8 6" />
    </svg>
  );
}

function LibraryIcon({ active }: { active?: boolean }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={iconColor(active)} strokeWidth="2">
      <rect x="4" y="10" width="3.5" height="10" rx="1" />
      <rect x="10.25" y="6" width="3.5" height="14" rx="1" />
      <rect x="16.5" y="3" width="3.5" height="17" rx="1" />
    </svg>
  );
}

function UploadIcon({ active }: { active?: boolean }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke={iconColor(active)} strokeWidth="2">
      <path d="M12 16V4M12 4l-4 4M12 4l4 4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M4 16v3a1 1 0 001 1h14a1 1 0 001-1v-3" strokeLinecap="round" />
    </svg>
  );
}