"use client";

import React, { useState, useEffect, useCallback } from 'react';
import dynamic from 'next/dynamic';
import {
  AlertTriangle,
  MapPin,
  Zap,
  Shield,
  MessageCircle,
  Users,
  TrendingUp,
  Activity,
  Flame,
  Waves,
  Info
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { analyze, DisasterEvent } from './lib/api';

// Leaflet needs `window`, so the map must never render on the server.
const DisasterMap = dynamic(() => import('./components/DisasterMap'), { ssr: false });

// Icons and plain-language guidance for the AI Analysis Panel, so a
// non-technical user immediately understands what an event means for them.
const EVENT_ICONS: Record<string, typeof Activity> = {
  earthquake: Activity,
  wildfire: Flame,
  flood: Waves,
};

const RISK_GUIDANCE: Record<string, string> = {
  Low: "No action needed — this is just for your awareness.",
  Medium: "Stay aware and keep an eye on local updates.",
  High: "Take precautions and avoid the affected area if you can.",
  Critical: "Seek safety immediately and follow local emergency guidance.",
};

interface Alert {
  id: number;
  type: string;
  location: string;
  risk: string;
  message: string;
  time: string;
}

interface ChatMessage {
  id: number;
  role: 'user' | 'ai';
  content: string;
  timestamp: string;
}

const DASHBOARD_REFRESH_MS = 90000;

export default function StormSenseDashboard() {
  const [events, setEvents] = useState<DisasterEvent[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [overallRisk, setOverallRisk] = useState<'Low' | 'Medium' | 'High' | 'Critical'>('Low');
  const [earthquakeRisk, setEarthquakeRisk] = useState('Low');
  const [floodRisk, setFloodRisk] = useState('Low');
  const [wildfireRisk, setWildfireRisk] = useState('Low');
  const [isDashboardLoading, setIsDashboardLoading] = useState(true);
  const [dashboardError, setDashboardError] = useState<string | null>(null);

  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: 1, role: 'ai',
      content: "StormSense AI online. Monitoring live data from USGS, NASA FIRMS & OpenWeatherMap. How can I help you today?",
      timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLocation, setChatLocation] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<DisasterEvent | null>(null);

  // Runs the real 5-agent pipeline via the backend and applies the result to
  // every piece of dashboard state (map, risk cards, alerts). Used both for
  // the periodic global refresh and for user chat queries, so asking about a
  // specific place also updates the live map/risk view.
  const runAnalysis = useCallback(async (query: string, location: string = '') => {
    const result = await analyze(query, location);

    setEvents(result.events);
    setOverallRisk((result.overall_risk as typeof overallRisk) || 'Low');
    setEarthquakeRisk(result.earthquake_risk || 'Low');
    setFloodRisk(result.flood_risk || 'Low');
    setWildfireRisk(result.wildfire_risk || 'Low');

    if (result.alert_triggered && result.alert_message) {
      const hazards = [
        result.earthquake_risk === result.overall_risk ? 'Earthquake' : null,
        result.flood_risk === result.overall_risk ? 'Flood' : null,
        result.wildfire_risk === result.overall_risk ? 'Wildfire' : null,
      ].filter(Boolean).join(' & ');

      setAlerts(prev => {
        if (prev[0]?.message === result.alert_message) return prev;
        const newAlert: Alert = {
          id: Date.now(),
          type: hazards || 'Multiple Hazards',
          location: location || 'Global',
          risk: result.overall_risk,
          message: result.alert_message,
          time: 'Just now'
        };
        return [newAlert, ...prev].slice(0, 5);
      });
    }

    return result;
  }, []);

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        await runAnalysis('Global disaster risk overview');
        setDashboardError(null);
      } catch (err) {
        console.error('Dashboard refresh failed:', err);
        setDashboardError(err instanceof Error ? err.message : String(err));
      } finally {
        setIsDashboardLoading(false);
      }
    };

    loadDashboard();
    const interval = setInterval(loadDashboard, DASHBOARD_REFRESH_MS);
    return () => clearInterval(interval);
  }, [runAnalysis]);

  const sendMessage = async () => {
    if (!chatInput.trim() || isProcessing) return;

    const userMessage: ChatMessage = {
      id: Date.now(), role: 'user', content: chatInput.trim(),
      timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    };
    setChatMessages(prev => [...prev, userMessage]);
    const currentInput = chatInput.trim();
    setChatInput('');
    setIsProcessing(true);

    let aiResponse: string;
    try {
      const result = await runAnalysis(currentInput, chatLocation.trim());
      aiResponse = result.final_response || result.final_explanation || "No response from the analysis pipeline.";
    } catch (err) {
      console.error("Analyze request failed:", err);
      const detail = err instanceof Error ? err.message : String(err);
      aiResponse = `Sorry, I couldn't get an answer right now (${detail}). This is usually a temporary issue with one of the live data sources — please try again in a moment.`;
    }

    const aiMessage: ChatMessage = {
      id: Date.now() + 1, role: 'ai', content: aiResponse,
      timestamp: new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    };
    setChatMessages(prev => [...prev, aiMessage]);
    setIsProcessing(false);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'Low': return 'risk-low';
      case 'Medium': return 'risk-medium';
      case 'High': return 'risk-high';
      case 'Critical': return 'risk-critical';
      default: return 'risk-medium';
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0f1a] text-[#e2e8f0] overflow-hidden">
      <nav className="border-b border-white/10 bg-[#0a0f1a]/90 backdrop-blur-2xl sticky top-0 z-50">
        <div className="max-w-[1600px] mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-[#3b82f6] to-[#1e40af] flex items-center justify-center shadow-lg shadow-blue-500/30">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="font-semibold tracking-[-1.5px] text-2xl">StormSense</div>
                <div className="text-[10px] text-[#64748b] -mt-1.5 tracking-[2px]">AI • 2090 DISASTER INTELLIGENCE</div>
              </div>
            </div>
            <div className="ml-6 px-3 py-1 rounded-full bg-[#1a2332] text-xs flex items-center gap-2 border border-[#2a3749]">
              <div className="w-2 h-2 rounded-full bg-[#22c55e] status-dot" />
              <span className="text-[#94a3b8]">LIVE • {new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2 px-4 py-1.5 rounded-xl bg-[#1a2332] border border-[#2a3749]">
              <Users className="w-4 h-4 text-[#94a3b8]" />
              <span className="text-[#94a3b8]">5 AI Agents Active</span>
            </div>
            <div className="px-4 py-1.5 rounded-xl bg-[#1a2332] border border-[#2a3749] text-xs">
              AMD GPU Cloud • Groq AI
            </div>
          </div>
        </div>
      </nav>

      <div className="max-w-[1600px] mx-auto px-6 pt-6 pb-8">
        <div className="flex items-end justify-between mb-6">
          <div>
            <div className="text-4xl font-semibold tracking-tighter">Global Monitoring Dashboard</div>
            <div className="text-[#94a3b8] mt-1">Autonomous 24/7 surveillance • USGS + NASA FIRMS + OpenWeatherMap</div>
          </div>
          <div className="flex items-center gap-3">
            <div className={`px-5 py-2 rounded-2xl text-sm font-medium flex items-center gap-2 border ${getRiskColor(overallRisk)}`}>
              <TrendingUp className="w-4 h-4" />
              GLOBAL RISK: {overallRisk.toUpperCase()}
            </div>
            <div className="text-xs text-[#94a3b8] px-3">
              {isDashboardLoading ? 'Loading live data…' : `${events.length} active events • Updated seconds ago`}
            </div>
          </div>
        </div>

        {dashboardError && (
          <div className="mb-5 px-4 py-3 rounded-2xl bg-[#7f1d1d]/40 border border-[#ef4444]/40 text-sm text-[#fca5a5] flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            Live data refresh failed: {dashboardError}. Showing the last known data — retrying automatically.
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">

          {/* MAP */}
          <div className="lg:col-span-7">
            <div className="glass rounded-3xl p-6 h-full flex flex-col">
              <div className="flex items-center justify-between mb-4 px-1">
                <div className="flex items-center gap-3">
                  <MapPin className="w-5 h-5 text-[#3b82f6]" />
                  <div>
                    <div className="font-semibold">Live Disaster Map</div>
                    <div className="text-xs text-[#94a3b8]">Real-time from space & ground sensors</div>
                  </div>
                </div>
                <div className="text-xs px-3 py-1 rounded-full bg-[#1a2332] border border-[#2a3749]">
                  Leaflet.js • Auto-refresh
                </div>
              </div>

              <div className="map-container flex-1 min-h-[420px] bg-[#111827] relative rounded-2xl overflow-hidden border border-[#2a3749]">
                <DisasterMap events={events} onSelect={setSelectedEvent} />

                <div className="absolute top-3 left-3 glass px-3 py-1.5 rounded-xl text-[10px] text-[#94a3b8] z-[1000] pointer-events-none">
                  🖱️ Click + drag to move • Scroll to zoom
                </div>

                <div className="absolute bottom-4 right-4 glass px-4 py-3 rounded-2xl text-xs z-[1000]">
                  <div className="flex flex-col gap-1.5">
                    <div className="flex items-center gap-2"><div className="w-2.5 h-2.5 rounded-full bg-[#22c55e]" /> Low</div>
                    <div className="flex items-center gap-2"><div className="w-2.5 h-2.5 rounded-full bg-[#eab308]" /> Medium</div>
                    <div className="flex items-center gap-2"><div className="w-2.5 h-2.5 rounded-full bg-[#ef4444]" /> High / Critical</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* RIGHT COLUMN */}
          <div className="lg:col-span-5 space-y-5">
            <div className="glass rounded-3xl p-5">
              <div className="flex items-center gap-2 mb-4 px-1">
                <Shield className="w-5 h-5 text-[#3b82f6]" />
                <div className="font-semibold">Risk Score Dashboard</div>
              </div>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: 'Earthquake', risk: earthquakeRisk, type: 'earthquake', Icon: Activity },
                  { label: 'Wildfire', risk: wildfireRisk, type: 'wildfire', Icon: Flame },
                  { label: 'Flood', risk: floodRisk, type: 'flood', Icon: Waves },
                ].map((cat) => {
                  const count = events.filter(e => e.type === cat.type).length;
                  return (
                    <div key={cat.label} className="card rounded-2xl p-4">
                      <div className="flex items-center gap-1.5 mb-2">
                        <cat.Icon className="w-3.5 h-3.5 text-[#94a3b8]" />
                        <div className="text-xs text-[#94a3b8]">{cat.label.toUpperCase()}</div>
                      </div>
                      <div className={`inline-block px-3 py-1 rounded-xl text-sm font-semibold ${getRiskColor(cat.risk)}`}>
                        {cat.risk}
                      </div>
                      <div className="text-[10px] text-[#64748b] mt-2 leading-snug">
                        {RISK_GUIDANCE[cat.risk] || RISK_GUIDANCE.Low}
                      </div>
                      <div className="text-[10px] text-[#3b82f6] mt-1.5">
                        {count} event{count !== 1 ? 's' : ''} tracked
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="glass rounded-3xl p-5 flex flex-col h-[320px]">
              <div className="flex items-center justify-between mb-4 px-1">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-[#ef4444]" />
                  <div className="font-semibold">Real-Time Alerts</div>
                </div>
                <div className="text-[10px] px-2.5 py-0.5 rounded-full bg-[#7f1d1d] text-[#fca5a5]">LIVE</div>
              </div>
              <div className="flex-1 overflow-auto space-y-2 pr-1">
                {alerts.length === 0 && (
                  <div className="text-xs text-[#94a3b8] px-1">No active High/Critical alerts right now.</div>
                )}
                <AnimatePresence>
                  {alerts.map((alert) => (
                    <motion.div key={alert.id} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
                      className="card rounded-2xl p-4 text-sm border-l-4 border-[#ef4444]">
                      <div className="font-semibold flex items-center gap-2">
                        {alert.type} • {alert.location}
                        <span className={`text-xs px-2 py-px rounded ${getRiskColor(alert.risk)}`}>{alert.risk}</span>
                      </div>
                      <div className="text-[#94a3b8] mt-1 text-xs">{alert.message}</div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>
          </div>

          {/* AI ANALYSIS */}
          <div className="lg:col-span-7">
            <div className="glass rounded-3xl p-6 h-full">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-8 h-8 rounded-xl bg-[#3b82f6]/10 flex items-center justify-center">
                  <Zap className="w-4 h-4 text-[#3b82f6]" />
                </div>
                <div>
                  <div className="font-semibold">AI Analysis Panel</div>
                  <div className="text-xs text-[#94a3b8]">Writer Agent • Plain language</div>
                </div>
              </div>
              {selectedEvent ? (
                <div>
                  <div className="flex items-center gap-3 mb-3">
                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${getRiskColor(selectedEvent.risk)}`}>
                      {(() => {
                        const Icon = EVENT_ICONS[selectedEvent.type] || Info;
                        return <Icon className="w-4 h-4" />;
                      })()}
                    </div>
                    <div className={`inline-block px-4 py-1 rounded-2xl text-sm font-medium capitalize ${getRiskColor(selectedEvent.risk)}`}>
                      {selectedEvent.type} • {selectedEvent.risk} risk
                    </div>
                  </div>
                  <div className="text-xl font-semibold tracking-tight">{selectedEvent.location}</div>
                  <div className="text-[#94a3b8] mt-1">{selectedEvent.description}</div>

                  <div className="card rounded-2xl p-4 mt-4 flex items-start gap-3">
                    <Info className="w-4 h-4 text-[#3b82f6] mt-0.5 shrink-0" />
                    <div>
                      <div className="text-xs text-[#94a3b8] mb-0.5">What this means for you</div>
                      <div className="text-sm">{RISK_GUIDANCE[selectedEvent.risk] || RISK_GUIDANCE.Low}</div>
                    </div>
                  </div>

                  {selectedEvent.time && (
                    <div className="text-xs text-[#64748b] mt-3">Detected: {selectedEvent.time}</div>
                  )}
                  <button onClick={() => setSelectedEvent(null)} className="mt-4 text-xs px-4 py-2 rounded-xl border border-[#2a3749] hover:bg-[#1a2332]">
                    Close
                  </button>
                </div>
              ) : (
                <div className="text-[#94a3b8] text-sm">Click any marker on the map or ask a question below.</div>
              )}
            </div>
          </div>

          {/* CHAT */}
          <div className="lg:col-span-5">
            <div className="glass rounded-3xl p-5 flex flex-col h-[380px]">
              <div className="flex items-center gap-3 mb-4 px-1">
                <MessageCircle className="w-5 h-5 text-[#3b82f6]" />
                <div>
                  <div className="font-semibold">Ask StormSense</div>
                  <div className="text-[10px] text-[#94a3b8]">Full 5-agent pipeline</div>
                </div>
              </div>

              <div className="flex-1 overflow-auto space-y-4 pr-2 mb-4 text-sm">
                {chatMessages.map((msg) => (
                  <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] px-4 py-3 rounded-3xl ${msg.role === 'user' ? 'bg-[#3b82f6] text-white rounded-br-none' : 'glass rounded-bl-none'}`}>
                      <div className="whitespace-pre-wrap">{msg.content}</div>
                      <div className="text-[10px] opacity-60 mt-1.5 text-right">{msg.timestamp}</div>
                    </div>
                  </div>
                ))}
                {isProcessing && (
                  <div className="glass px-4 py-3 rounded-3xl rounded-bl-none text-sm flex items-center gap-2">
                    <div className="flex gap-1">
                      <div className="w-1.5 h-1.5 bg-[#3b82f6] rounded-full animate-bounce" />
                      <div className="w-1.5 h-1.5 bg-[#3b82f6] rounded-full animate-bounce [animation-delay:150ms]" />
                      <div className="w-1.5 h-1.5 bg-[#3b82f6] rounded-full animate-bounce [animation-delay:300ms]" />
                    </div>
                    <span className="text-xs text-[#94a3b8]">Thinking...</span>
                  </div>
                )}
              </div>

              <input
                type="text"
                value={chatLocation}
                onChange={(e) => setChatLocation(e.target.value)}
                placeholder="Location (optional) — e.g. Pakistan, Tokyo, California"
                className="mb-2 bg-[#111827] border border-[#2a3749] rounded-xl px-4 py-2 text-xs placeholder:text-[#64748b] focus:outline-none focus:border-[#3b82f6]"
                disabled={isProcessing}
              />
              <div className="flex gap-2">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder="What is the earthquake risk right now?"
                  className="flex-1 bg-[#111827] border border-[#2a3749] rounded-2xl px-5 py-3 text-sm placeholder:text-[#64748b] focus:outline-none focus:border-[#3b82f6]"
                  disabled={isProcessing}
                />
                <button onClick={sendMessage} disabled={!chatInput.trim() || isProcessing}
                  className="px-6 rounded-2xl bg-[#3b82f6] hover:bg-[#2563eb] disabled:opacity-50 transition-all">
                  Send
                </button>
              </div>
              <div className="text-[10px] text-center text-[#64748b] mt-2">Powered by LangGraph + Groq AI</div>
            </div>
          </div>
        </div>

        <div className="mt-8 text-center text-xs text-[#64748b] tracking-[3px] font-mono">
          STORMSENSE AI • 5 SPECIALIZED AGENTS • FULLY AUTONOMOUS • AMD HACKATHON 2026
        </div>
      </div>
    </div>
  );
}
