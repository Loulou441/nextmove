"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import Sidebar from "./Sidebar";
import BottomTabBar from "./BottomTabBar";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !user) {
      router.replace("/login");
    }
  }, [isLoading, user, router]);

  if (isLoading || !user) {
    return (
      <div className="flex flex-col flex-1 items-center justify-center">
        <p className="text-nm-text-secondary text-sm">Chargement...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-1 min-h-screen">
      <Sidebar />
      <main className="flex-1 px-4 py-6 pb-28 md:pb-6 md:px-8 max-w-4xl mx-auto w-full">
        {children}
      </main>
      <BottomTabBar />
    </div>
  );
}