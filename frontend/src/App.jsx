import React, { useState, useEffect, useRef, useCallback } from 'react';
import useWebSocket from 'react-use-websocket';
import { Play, LayoutDashboard, Activity, Settings, Zap, ShieldAlert } from "lucide-react";
import { motion, AnimatePresence } from 'framer-motion';

import Gauge from './components/common/Gauge';
import AlertHistory from './components/AlertHistory';
import AnalyticsChart from './components/AnalyticsChart';

const SENSOR_GROUPS = {
  "MOTOR DYNAMICS": ["engine_speed", "engine_temperature", "engine_vibration", "engine_load"],
  "BRAKING SYSTEM": ["brakes_pressure", "brakes_efficiency", "brakes_current"],
  "POWER & TIRES": ["battery_voltage", "battery_current", "tires_pressure", "tires_load"]
};

// Framer motion variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
};

const itemVariants = {
  hidden: { y: 20, opacity: 0 },
  visible: { y: 0, opacity: 1, transition: { type: "spring", stiffness: 300, damping: 24 } }
};

const AcousticWaveform = ({ state }) => {
  const isDanger = state && state !== "NORMAL_ENGINE_IDLE" && !state.includes("INITIALIZING") && !state.includes("LISTENING");
  const isInitializing = state?.includes("INITIALIZING");
  
  let colorClass = "bg-[#2dd4bf] shadow-[0_0_15px_rgba(45,212,191,0.5)]";
  if (isDanger) colorClass = "bg-[#ef4444] shadow-[0_0_20px_rgba(239,68,68,0.8)]";
  else if (isInitializing) colorClass = "bg-neutral-600";
  
  return (
    <div className="flex items-center justify-center gap-[4px] h-12 w-full mt-4">
      {[1, 2, 3, 4, 5, 6, 7].map((i) => (
        <div key={i} className={`w-2.5 rounded-full wave-bar h-full transition-colors duration-500 ${colorClass}`}></div>
      ))}
    </div>
  );
};

function App() {
  const [activeTab, setActiveTab] = useState("overview");
  const [telemetry, setTelemetry] = useState(null);
  const [freezeFrame, setFreezeFrame] = useState(null);
  const [dtcWarning, setDtcWarning] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [acousticLog, setAcousticLog] = useState([]);
  const [chartData, setChartData] = useState([]);
  
  const alertId = useRef(0);
  const alertMessages = useRef(new Set());
  const prevStates = useRef({});

  const { lastJsonMessage } = useWebSocket('ws://127.0.0.1:8000/ws/telemetry');

  const pushAlert = useCallback((severity, message) => {
    if (alertMessages.current.has(message)) return;
    alertMessages.current.add(message);
    const id = ++alertId.current;
    
    setAlerts(prev => {
      const newAlerts = [...prev, { id, message, severity }];
      if (newAlerts.length > 3) return newAlerts.slice(-3);
      return newAlerts;
    });

    setTimeout(() => {
      setAlerts(prev => prev.filter(a => a.id !== id));
      alertMessages.current.delete(message);
    }, 8000);
  }, []);

  const dismissAlert = (id, message) => {
    setAlerts(prev => prev.filter(a => a.id !== id));
    alertMessages.current.delete(message);
  };

  useEffect(() => {
    if (!lastJsonMessage) return;

    if (lastJsonMessage.mode === "01") {
      setTelemetry(lastJsonMessage);
      
      // Update chart data
      setChartData(prev => {
        const metrics = lastJsonMessage.live_metrics;
        const newData = [...prev, {
          time: new Date().toLocaleTimeString([], { hour12: false, minute: '2-digit', second: '2-digit' }),
          RPM: Number(metrics.engine_speed || 0),
          Speed: Number(metrics.engine_temperature || 0) 
        }];
        return newData.length > 30 ? newData.slice(1) : newData;
      });

      // Intrusion detection
      if (lastJsonMessage.status === "ANOMALY" && prevStates.current.status !== "ANOMALY") {
          pushAlert("critical", "Network Anomaly: Suspicious payload detected");
      }
      
      // Acoustic warnings
      const isBadAudio = lastJsonMessage.acoustic_state && 
                         lastJsonMessage.acoustic_state !== "NORMAL_ENGINE_IDLE" && 
                         !lastJsonMessage.acoustic_state.includes("INITIALIZING");
      
      if (isBadAudio && prevStates.current.audio !== lastJsonMessage.acoustic_state) {
          pushAlert("warning", `Acoustic Match: ${lastJsonMessage.acoustic_state.replace(/_/g, ' ')}`);
      }
      
      // Threshold checking
      const engineRul = lastJsonMessage.rul_predictions?.engine;
      if (engineRul < 15 && prevStates.current.engine >= 15) {
          pushAlert("critical", "Engine component failure imminent");
      } else if (engineRul < 50 && prevStates.current.engine >= 50) {
          pushAlert("warning", "Engine RUL degraded below threshold");
      }

      prevStates.current = { 
        status: lastJsonMessage.status, 
        audio: lastJsonMessage.acoustic_state, 
        engine: engineRul 
      };
      
      if (lastJsonMessage.acoustic_url && lastJsonMessage.acoustic_state && !lastJsonMessage.acoustic_state.includes("INITIALIZING")) {
            setAcousticLog(prev => {
              const lastEntry = prev[0];
              if (!lastEntry || lastEntry.url !== lastJsonMessage.acoustic_url) {
                  const newLog = [{
                      state: lastJsonMessage.acoustic_state,
                      url: lastJsonMessage.acoustic_url,
                      time: new Date().toLocaleTimeString([], { hour12: false })
                  }, ...prev];
                  return newLog.slice(0, 3);
              }
              return prev;
            });
      }

      setDtcWarning(lastJsonMessage.status === "DTC_WARNING" ? lastJsonMessage : null);
    } else if (lastJsonMessage.mode === "02") {
      setFreezeFrame(lastJsonMessage.freeze_frame);
      // Automatically clear the fault after 60 seconds if not rebooted manually
      setTimeout(() => setFreezeFrame(null), 60000);
    } else if (lastJsonMessage.mode === "03") {
      setDtcWarning(lastJsonMessage);
    }
  }, [lastJsonMessage, pushAlert]);

  if (freezeFrame) {
      const handleReboot = () => {
          setFreezeFrame(null);
          // Optional short timeout for a smoother 'System Reboot' feel
          setTimeout(() => window.location.reload(), 300);
      };

      return (
      <div className="fixed inset-0 z-50 bg-[#050505] flex items-center justify-center p-8 backdrop-blur-3xl">
        <div className="glass-panel border-red-500/50 rounded-3xl p-10 shadow-[0_0_100px_rgba(220,38,38,0.25)] w-full max-w-lg mx-auto">
           <h1 className="text-3xl font-bold tracking-tight text-white mb-2 text-center text-red-500 uppercase">System Integrity Fault</h1>
           <p className="text-center text-red-300/80 font-medium mb-8">
              Failure Protocol active on domain: <span className="font-bold uppercase tracking-widest">{freezeFrame.domain || "CRITICAL_SUBSYSTEM"}</span>
           </p>
           <button 
              onClick={handleReboot} 
              className="bg-red-500/10 hover:bg-red-500/20 border border-red-500/30 text-red-100 rounded-xl px-6 py-4 font-bold text-sm w-full tracking-widest uppercase transition-all backdrop-blur-md"
           >
             Initialize Secure Reboot
           </button>
        </div>
      </div>
    );
  }

  const isAnomaly = telemetry?.status === "ANOMALY";

  return (
    <div className="flex h-screen overflow-hidden">
      
      <AlertHistory alerts={alerts} onDismiss={dismissAlert} />

      {/* --- LEFT VERTICAL SIDEBAR --- */}
      <motion.aside 
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        transition={{ type: "spring", stiffness: 200, damping: 20 }}
        className="w-20 lg:w-64 flex-shrink-0 border-r border-white/5 bg-white/[0.02] backdrop-blur-2xl flex flex-col justify-between py-6 z-40 transition-all duration-300"
      >
        <div>
           <div className="px-6 mb-10 flex items-center gap-3">
             <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-600 to-teal-400 flex items-center justify-center shadow-[0_0_15px_rgba(45,212,191,0.5)]">
                <Zap size={16} className="text-white fill-white" />
             </div>
             <span className="hidden lg:block text-lg font-bold tracking-widest text-slate-100">SDV_KNK</span>
           </div>

           <nav className="flex flex-col gap-2 px-3">
              {[
                { id: "overview", icon: LayoutDashboard, label: "Overview" },
                { id: "analytics", icon: Activity, label: "Analytics" },
                { id: "settings", icon: Settings, label: "Settings" }
              ].map(tab => {
                 const isActive = activeTab === tab.id;
                 return (
                   <button 
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-300 relative group overflow-hidden ${isActive ? 'text-white' : 'text-slate-500 hover:text-slate-300 hover:bg-white/5'}`}
                   >
                      {isActive && (
                          <motion.div 
                              layoutId="activeTabBadge"
                              className="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-teal-500/5 border border-white/10 rounded-xl"
                          />
                      )}
                      <tab.icon size={20} className="relative z-10" />
                      <span className="relative z-10 hidden lg:block text-sm font-semibold tracking-wide">{tab.label}</span>
                      
                      {isActive && <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-teal-400 rounded-r-md shadow-[0_0_10px_#2dd4bf]" />}
                   </button>
                 )
              })}
           </nav>
        </div>

        <div className="px-6 mb-4">
           {isAnomaly && (
              <div className="hidden lg:flex items-center gap-3 p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 transition-all">
                <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                <span className="text-xs font-bold uppercase tracking-widest">IDS Alert Active</span>
              </div>
           )}
        </div>
      </motion.aside>

      {/* --- MAIN CONTENT AREA --- */}
      <main className="flex-1 overflow-y-auto overflow-x-hidden p-6 lg:p-10 custom-scrollbar relative z-10">
         {!telemetry ? (
            <div className="flex h-full items-center justify-center flex-col gap-6">
              <div className="w-12 h-12 border-2 border-slate-600 border-t-teal-400 rounded-full animate-spin shadow-[0_0_20px_rgba(45,212,191,0.2)]"></div>
              <p className="text-slate-500 font-semibold tracking-widest text-sm uppercase">
                Awaiting telemetry stream...
              </p>
            </div>
         ) : (
            <motion.div 
               variants={containerVariants}
               initial="hidden"
               animate="visible"
               className="grid grid-cols-1 xl:grid-cols-3 gap-6 max-w-[1600px] mx-auto"
            >
               {activeTab === "overview" && (
                 <>
                   {/* LEFT COLUMN: DIAGNOSTICS & LIST */}
                   <motion.div variants={itemVariants} className="col-span-1 flex flex-col gap-6">
                     <div className="glass-panel rounded-3xl p-6">
                         <div className="flex justify-between items-start mb-4">
                            <div>
                               <h2 className="text-sm font-semibold tracking-wider text-slate-100">ACOUSTIC INFERENCE</h2>
                               <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1">Real-time MLP Decoder</p>
                            </div>
                            <div className={`px-3 py-1 rounded-full border text-[10px] font-bold uppercase tracking-widest ${telemetry.acoustic_state?.includes("NORMAL") || telemetry.acoustic_state?.includes("INITIALIZING") ? "bg-teal-500/10 border-teal-500/20 text-teal-400" : "bg-red-500/10 border-red-500/20 text-red-400"}`}>
                               {telemetry.acoustic_state?.replace(/_/g, ' ')}
                            </div>
                         </div>
                         
                         <AcousticWaveform state={telemetry.acoustic_state} />
                         
                         <div className="mt-6 space-y-2 max-h-[140px] overflow-y-auto custom-scrollbar pr-2">
                            {acousticLog.map((log, i) => (
                                <div key={i} className="flex justify-between items-center px-4 py-3 bg-black/20 border border-white/5 rounded-xl group transition-all hover:bg-white/5">
                                   <div className="flex flex-col gap-0.5">
                                      <span className={`text-xs font-bold uppercase tracking-wider truncate ${log.state.includes("NORMAL") ? 'text-teal-400' : 'text-red-400'}`}>{log.state.replace(/_/g, ' ')}</span>
                                      <span className="text-[10px] text-slate-500 font-medium tracking-widest uppercase">{log.time}</span>
                                   </div>
                                   <button onClick={() => new Audio(log.url).play()} className="p-2 rounded-lg bg-white/5 hover:bg-teal-500/20 text-slate-300 hover:text-teal-400 transition-colors border border-transparent hover:border-teal-500/30">
                                      <Play fill="currentColor" size={14} />
                                   </button>
                                </div>
                            ))}
                         </div>
                     </div>

                     <div className="glass-panel rounded-3xl p-6 flex-1 flex flex-col">
                         <div className="mb-6 flex justify-between items-center">
                            <h2 className="text-sm font-semibold tracking-wider text-slate-100">CAN BUS FEED</h2>
                            <span className="text-[10px] font-mono text-purple-400 font-bold tracking-widest bg-purple-500/10 px-2 py-1 rounded border border-purple-500/20">0x7E8</span>
                         </div>
                         <div className="space-y-6 flex-1 overflow-y-auto custom-scrollbar pr-2">
                            {Object.entries(SENSOR_GROUPS).map(([groupName, sensors]) => (
                               <div key={groupName}>
                                  <h3 className="text-[10px] font-bold text-slate-500 tracking-widest uppercase mb-3">{groupName}</h3>
                                  <div className="space-y-1">
                                     {sensors.map(sensor => {
                                        const val = telemetry.live_metrics[sensor];
                                        return (
                                           <div key={sensor} className="flex justify-between items-center p-2 rounded-lg hover:bg-white/5 transition-colors">
                                              <span className="text-[11px] font-medium text-slate-400 tracking-widest uppercase">
                                                 {sensor.replace(/_/g, ' ')}
                                              </span>
                                              <span className={`font-mono text-xs font-semibold tracking-tight ${isAnomaly ? 'text-red-400' : 'text-slate-200'}`}>
                                                 {val !== undefined ? Number(val).toFixed(2) : "---"}
                                              </span>
                                           </div>
                                        );
                                     })}
                                  </div>
                               </div>
                            ))}
                         </div>
                     </div>
                   </motion.div>

                   {/* RIGHT COLUMN: GRAPHS AND GAUGES */}
                   <motion.div variants={itemVariants} className="col-span-1 xl:col-span-2 flex flex-col gap-6">
                      
                      {/* Main Main Chart */}
                      <div className="glass-panel rounded-3xl p-6 h-64 lg:h-80 flex flex-col">
                         <div className="flex justify-between items-center mb-4">
                             <div>
                               <h2 className="text-sm font-semibold tracking-wider text-slate-100">PERFORMANCE MATRIX</h2>
                               <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1">RPM vs Speed Context</p>
                             </div>
                             <div className="flex gap-4">
                                <div className="flex items-center gap-2">
                                  <div className="w-2 h-2 rounded-full bg-teal-400 shadow-[0_0_10px_#2DD4BF]" />
                                  <span className="text-[10px] text-slate-400 uppercase font-bold tracking-widest">Speed</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  <div className="w-2 h-2 rounded-full bg-purple-500 shadow-[0_0_10px_#7C3AED]" />
                                  <span className="text-[10px] text-slate-400 uppercase font-bold tracking-widest">RPM</span>
                                </div>
                             </div>
                         </div>
                         <div className="flex-1 overflow-hidden min-h-0">
                           <AnalyticsChart data={chartData} />
                         </div>
                      </div>

                      {/* Gauges Grid */}
                      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
                         {['engine', 'brakes', 'tires', 'battery'].map((domain, idx) => (
                           <motion.div key={domain} variants={itemVariants} custom={idx}>
                             <Gauge 
                                title={domain} 
                                rul={telemetry.rul_predictions?.[domain]} 
                                isAnomaly={isAnomaly} 
                             />
                           </motion.div>
                         ))}
                      </div>

                      {/* Footer bar */}
                      <div className="glass-panel rounded-3xl p-6 flex flex-col lg:flex-row items-center justify-between gap-4 mt-auto">
                         <div className="flex items-center gap-3">
                            <ShieldAlert size={18} className={isAnomaly ? "text-red-500" : "text-teal-400"} />
                            <h3 className="text-xs font-semibold text-slate-300 tracking-widest uppercase">
                               Network Status: <span className={isAnomaly ? "text-red-400 font-bold" : "text-teal-400 font-bold"}>{isAnomaly ? "COMPROMISED" : "SECURE"}</span>
                            </h3>
                         </div>
                         <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">SDV_KNK Platform v4.0</p>
                      </div>

                   </motion.div>
                 </>
               )}
               
               {activeTab !== "overview" && (
                 <div className="col-span-full h-full flex flex-col items-center justify-center opacity-50">
                    <p className="text-xl font-bold text-slate-400 tracking-widest uppercase mb-2">Module Offline</p>
                    <p className="text-sm text-slate-500">Wait for next software upgrade path.</p>
                 </div>
               )}
            </motion.div>
         )}
      </main>
    </div>
  );
}

export default App;
