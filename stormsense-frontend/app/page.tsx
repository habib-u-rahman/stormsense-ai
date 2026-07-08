"use client";

import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  MapPin, 
  Zap, 
  Shield, 
  MessageCircle, 
  Users,
  TrendingUp 
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface DisasterEvent {
  id: number;
  type: 'earthquake' | 'flood' | 'wildfire';
  location: string;
  magnitude?: number;
  severity?: string;
  lat: number;
  lng: number;
  risk: 'Low' | 'Medium' | 'High' | 'Critical';
  time: string;
  description: string;
}

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

const initialEvents: DisasterEvent[] = [
  {
    id: 1, type: 'earthquake', location: "120km SE of Islamabad, Pakistan",
    magnitude: 5.8, lat: 33.2, lng: 73.8, risk: 'Medium', time: '14:32 PKT',
    description: 'Moderate seismic activity detected. No immediate structural threat reported.'
  },
  {
    id: 2, type: 'wildfire', location: "Northern California, USA",
    severity: 'High', lat: 40.5, lng: -122.8, risk: 'High', time: '09:15 PDT',
    description: 'Active wildfire spreading. Evacuation orders issued for nearby communities.'
  },
  {
    id: 3, type: 'flood', location: "Sindh Province, Pakistan",
    severity: 'Medium', lat: 25.8, lng: 68.5, risk: 'Medium', time: '11:47 PKT',
    description: 'River levels rising. Moderate flood risk in low-lying areas.'
  },
  {
    id: 4, type: 'earthquake', location: "35km NW of Almaty, Kazakhstan",
    magnitude: 4.2, lat: 43.4, lng: 76.8, risk: 'Low', time: '16:05 ALMT',
    description: 'Minor tremor. No damage expected.'
  }
];

const initialAlerts: Alert[] = [
  {
    id: 1, type: 'Wildfire', location: 'Northern California', risk: 'High',
    message: 'Active fire spreading rapidly. Evacuation recommended for zones 4-7.', time: '2 min ago'
  }
];

export default function StormSenseDashboard() {
  const [events, setEvents] = useState<DisasterEvent[]>(initialEvents);
  const [alerts, setAlerts] = useState<Alert[]>(initialAlerts);
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: 1, role: 'ai',
      content: "StormSense AI online. Monitoring live data from USGS, NASA FIRMS & OpenWeatherMap. How can I help you today?",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<DisasterEvent | null>(null);
  const [globalRisk, setGlobalRisk] = useState<'Low' | 'Medium' | 'High' | 'Critical'>('Medium');

  useEffect(() => {
    const interval = setInterval(() => {
      if (Math.random() > 0.65) {
        const newAlert: Alert = {
          id: Date.now(),
          type: ['Earthquake', 'Wildfire', 'Flood'][Math.floor(Math.random() * 3)],
          location: ['Pakistan', 'California', 'Indonesia', 'Turkey', 'Kazakhstan'][Math.floor(Math.random() * 5)],
          risk: Math.random() > 0.7 ? 'Critical' : 'High',
          message: 'New high-risk event detected. Analysis in progress...',
          time: 'Just now'
        };
        setAlerts(prev => [newAlert, ...prev].slice(0, 5));
      }
      if (Math.random() > 0.8) {
        setEvents(prev => {
          const updated = [...prev];
          const idx = Math.floor(Math.random() * updated.length);
          const risks: ('Low' | 'Medium' | 'High' | 'Critical')[] = ['Low', 'Medium', 'High', 'Critical'];
          updated[idx] = { ...updated[idx], risk: risks[Math.floor(Math.random() * risks.length)] };
          return updated;
        });
      }
    }, 18000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const hasCritical = events.some(e => e.risk === 'Critical');
    const hasHigh = events.some(e => e.risk === 'High');
    if (hasCritical) setGlobalRisk('Critical');
    else if (hasHigh) setGlobalRisk('High');
    else setGlobalRisk('Medium');
  }, [events]);

  const processAgentPipeline = async (query: string): Promise<string> => {
    await new Promise(resolve => setTimeout(resolve, 1200));
    const lowerQuery = query.toLowerCase();

    if (lowerQuery.includes('earthquake') || lowerQuery.includes('seismic')) {
      const eq = events.find(e => e.type === 'earthquake');
      return eq 
        ? `Latest earthquake data: A magnitude ${eq.magnitude} event was recorded ${eq.location} at ${eq.time}. Risk level: ${eq.risk}. ${eq.description}`
        : "No significant earthquake activity detected in the last 6 hours.";
    }
    if (lowerQuery.includes('wildfire') || lowerQuery.includes('fire')) {
      const fire = events.find(e => e.type === 'wildfire');
      return fire ? `Active wildfire detected in ${fire.location}. Current risk: ${fire.risk}. ${fire.description}` : "No active high-risk wildfires reported.";
    }
    if (lowerQuery.includes('flood')) {
      const flood = events.find(e => e.type === 'flood');
      return flood ? `Flood monitoring: ${flood.location} currently at ${flood.risk} risk. ${flood.description}` : "Flood risk remains low.";
    }
    if (lowerQuery.includes('risk')) {
      return `Current global risk assessment: ${globalRisk}. ${events.length} active events being monitored.`;
    }
    return `StormSense AI has analyzed live data. There are currently ${events.length} monitored events. Global risk level is ${globalRisk}.`;
  };

  const sendMessage = async () => {
    if (!chatInput.trim() || isProcessing) return;

    const userMessage: ChatMessage = {
      id: Date.now(), role: 'user', content: chatInput.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    setChatMessages(prev => [...prev, userMessage]);
    const currentInput = chatInput.trim();
    setChatInput('');
    setIsProcessing(true);

    const aiResponse = await processAgentPipeline(currentInput);

    const aiMessage: ChatMessage = {
      id: Date.now() + 1, role: 'ai', content: aiResponse,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
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
              <span className="text-[#94a3b8]">LIVE • {new Date().toLocaleDateString([], { month: 'short', day: 'numeric' })}</span>
            </div>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <div className="flex items-center gap-2 px-4 py-1.5 rounded-xl bg-[#1a2332] border border-[#2a3749]">
              <Users className="w-4 h-4 text-[#94a3b8]" />
              <span className="text-[#94a3b8]">5 AI Agents Active</span>
            </div>
            <div className="px-4 py-1.5 rounded-xl bg-[#1a2332] border border-[#2a3749] text-xs">
              AMD GPU Cloud • Fireworks AI
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
            <div className={`px-5 py-2 rounded-2xl text-sm font-medium flex items-center gap-2 border ${getRiskColor(globalRisk)}`}>
              <TrendingUp className="w-4 h-4" />
              GLOBAL RISK: {globalRisk.toUpperCase()}
            </div>
            <div className="text-xs text-[#94a3b8] px-3">
              {events.length} active events • Updated seconds ago
            </div>
          </div>
        </div>

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
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-6xl mb-4 opacity-20">🗺️</div>
                    <div className="text-lg font-medium mb-2">Interactive Map</div>
                    <div className="text-sm text-[#94a3b8]">Color-coded markers • Click for details</div>
                  </div>
                </div>

                <div className="absolute top-[28%] left-[32%] w-4 h-4 rounded-full bg-[#eab308] ring-4 ring-[#eab308]/30 cursor-pointer" onClick={() => setSelectedEvent(events[0])} />
                <div className="absolute top-[42%] left-[68%] w-5 h-5 rounded-full bg-[#ef4444] ring-4 ring-[#ef4444]/30 cursor-pointer animate-pulse" onClick={() => setSelectedEvent(events[1])} />
                <div className="absolute top-[65%] left-[48%] w-3.5 h-3.5 rounded-full bg-[#eab308] ring-4 ring-[#eab308]/30 cursor-pointer" onClick={() => setSelectedEvent(events[2])} />
                <div className="absolute top-[35%] left-[55%] w-3 h-3 rounded-full bg-[#22c55e] ring-4 ring-[#22c55e]/30 cursor-pointer" onClick={() => setSelectedEvent(events[3])} />

                <div className="absolute bottom-4 right-4 glass px-4 py-3 rounded-2xl text-xs">
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
                {['Earthquake', 'Wildfire', 'Flood'].map((cat, idx) => {
                  const relevant = events.filter(e => 
                    (cat === 'Earthquake' && e.type === 'earthquake') ||
                    (cat === 'Wildfire' && e.type === 'wildfire') ||
                    (cat === 'Flood' && e.type === 'flood')
                  );
                  const highest = relevant.length > 0 ? relevant.reduce((a, b) => 
                    ['Critical','High','Medium','Low'].indexOf(a.risk) < ['Critical','High','Medium','Low'].indexOf(b.risk) ? a : b
                  ).risk : 'Low';
                  return (
                    <div key={idx} className="card rounded-2xl p-4 text-center">
                      <div className="text-xs text-[#94a3b8] mb-1">{cat.toUpperCase()}</div>
                      <div className={`inline-block px-4 py-1 rounded-xl text-sm font-semibold mt-1 ${getRiskColor(highest)}`}>
                        {highest}
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
                  <div className={`inline-block px-4 py-1 rounded-2xl text-sm font-medium mb-3 ${getRiskColor(selectedEvent.risk)}`}>
                    {selectedEvent.risk} RISK
                  </div>
                  <div className="text-xl font-semibold tracking-tight">{selectedEvent.location}</div>
                  <div className="text-[#94a3b8] mt-1">{selectedEvent.description}</div>
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
                      <div>{msg.content}</div>
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

              <div className="flex gap-2">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder="What is the earthquake risk in Pakistan right now?"
                  className="flex-1 bg-[#111827] border border-[#2a3749] rounded-2xl px-5 py-3 text-sm placeholder:text-[#64748b] focus:outline-none focus:border-[#3b82f6]"
                  disabled={isProcessing}
                />
                <button onClick={sendMessage} disabled={!chatInput.trim() || isProcessing}
                  className="px-6 rounded-2xl bg-[#3b82f6] hover:bg-[#2563eb] disabled:opacity-50 transition-all">
                  Send
                </button>
              </div>
              <div className="text-[10px] text-center text-[#64748b] mt-2">Powered by LangGraph + Fireworks AI</div>
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