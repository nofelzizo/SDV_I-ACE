import React from 'react';
import { AlertCircle, X, ShieldAlert } from "lucide-react";
import { motion, AnimatePresence } from 'framer-motion';

const AlertHistory = ({ alerts, onDismiss }) => {
  return (
    <div className="fixed top-8 right-8 z-[100] flex flex-col gap-4 w-full max-w-[360px] pointer-events-none">
      <AnimatePresence>
        {alerts.map(alert => (
          <motion.div 
            key={alert.id}
            initial={{ opacity: 0, x: 50, scale: 0.95 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.2 } }}
            className={`pointer-events-auto flex items-start gap-4 p-4 rounded-2xl glass-panel border border-${alert.severity === "critical" ? "red" : "amber"}-500/30 shadow-[0_8px_32px_rgba(${alert.severity === "critical" ? "239,68,68" : "245,158,11"},0.2)] bg-black/40`}
          >
            <div className={`p-2 rounded-xl bg-white/5 border border-white/5 shrink-0`}>
                {alert.severity === "critical" ? (
                    <ShieldAlert size={18} className="text-red-400" />
                ) : (
                    <AlertCircle size={18} className="text-amber-400" />
                )}
            </div>
            
            <p className={`text-sm font-medium tracking-wide flex-1 m-0 leading-5 pt-1 ${alert.severity === "critical" ? "text-red-100" : "text-amber-100"}`}>
              {alert.message}
            </p>
            
            <button 
              onClick={() => onDismiss(alert.id, alert.message)} 
              className="p-1 rounded-lg opacity-60 hover:opacity-100 hover:bg-white/10 transition-all shrink-0 mt-0.5"
            >
              <X size={16} className="text-slate-300" />
            </button>
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

export default AlertHistory;
