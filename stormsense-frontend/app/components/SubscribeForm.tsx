"use client";

import { useState } from "react";
import { Mail, Bell } from "lucide-react";
import { subscribe } from "../lib/api";

export default function SubscribeForm() {
  const [value, setValue] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [feedback, setFeedback] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!value.trim() || status === "loading") return;

    setStatus("loading");
    try {
      const message = await subscribe(value.trim());
      setStatus("success");
      setFeedback(message);
      setValue("");
    } catch (err) {
      setStatus("error");
      setFeedback(err instanceof Error ? err.message : "Subscription failed.");
    }
  };

  return (
    <div className="border-t border-[#2a3749] mt-3 pt-3">
      <div className="flex items-center gap-1.5 mb-2">
        <Bell className="w-3.5 h-3.5 text-[#3b82f6]" />
        <span className="text-xs font-medium">Get real alerts by email</span>
      </div>
      <form onSubmit={handleSubmit} className="flex gap-1.5">
        <div className="flex items-center px-2 rounded-lg border border-[#2a3749] bg-[#111827] text-[#64748b] shrink-0">
          <Mail className="w-3.5 h-3.5" />
        </div>
        <input
          type="email"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="you@example.com"
          className="flex-1 min-w-0 bg-[#111827] border border-[#2a3749] rounded-lg px-2.5 py-1.5 text-xs placeholder:text-[#64748b] focus:outline-none focus:border-[#3b82f6]"
          disabled={status === "loading"}
        />
        <button
          type="submit"
          disabled={!value.trim() || status === "loading"}
          className="px-3 rounded-lg bg-[#3b82f6] hover:bg-[#2563eb] disabled:opacity-50 text-xs font-medium transition-all shrink-0"
        >
          {status === "loading" ? "..." : "Subscribe"}
        </button>
      </form>
      {status === "success" && <div className="text-[10px] text-[#22c55e] mt-1.5">{feedback}</div>}
      {status === "error" && <div className="text-[10px] text-[#ef4444] mt-1.5">{feedback}</div>}
    </div>
  );
}
