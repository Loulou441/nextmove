"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function Home() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;
    router.replace(user ? "/library" : "/login");
  }, [user, isLoading, router]);

  return (
    <div className="flex flex-col flex-1 items-center justify-center">
      <p className="text-nm-text-secondary text-sm">Chargement...</p>
    </div>
  );
}