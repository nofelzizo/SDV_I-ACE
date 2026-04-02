import React from 'react';
import { motion } from 'framer-motion';

const Gauge = ({ rul, maxRul = 500, isAnomaly, title }) => {
  const percentage = Math.max(0, Math.min(100, (rul / maxRul) * 100));
  
  let glowColor = "rgba(45, 212, 191, 0.7)"; // Teal
  let strokeColor = "#2dd4bf";
  
  if (isAnomaly || rul < 15) { 
    glowColor = "rgba(239, 68, 68, 0.7)"; // Red
    strokeColor = "#ef4444";
  } else if (rul < 50) { 
    glowColor = "rgba(245, 158, 11, 0.7)"; // Amber
    strokeColor = "#f59e0b";
  }

  const cx = 130, cy = 130, trackR = 110, strokeW = 12; // Thinner stroke for elegance
  const C = 2 * Math.PI * trackR;
  const arcLen = C * 0.75;
  const gapLen = C - arcLen;
  const progress = isAnomaly ? 0 : (percentage / 100) * arcLen;

  const titleColor = (isAnomaly || rul < 15) ? "text-red-400" : (rul < 50 ? "text-amber-400" : "text-slate-100");

  return (
    <motion.div 
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      className="glass-panel rounded-3xl p-6 flex flex-col justify-between relative overflow-hidden group"
    >
      {/* Subtle background glow effect on hover */}
      <div className="absolute inset-0 opacity-0 group-hover:opacity-20 transition-opacity duration-700 pointer-events-none" 
           style={{ background: `radial-gradient(circle at center, ${glowColor} 0%, transparent 70%)` }} />

      <div className="relative z-10 flex justify-between items-start mb-2">
          <h3 className={`text-sm font-semibold tracking-wider uppercase ${titleColor}`}>{title}</h3>
          <span className="text-[10px] font-medium tracking-widest uppercase text-slate-400">
            Cycles left
          </span>
      </div>
      
      <div className="relative w-full aspect-square max-w-[180px] mx-auto mt-4 mb-2">
        <svg viewBox="0 0 260 260" className="w-full h-full overflow-visible drop-shadow-2xl z-20 relative">
          <circle 
            cx={cx} cy={cy} r={trackR} fill="none" 
            stroke="rgba(255,255,255,0.05)" strokeWidth={strokeW} 
            strokeDasharray={`${arcLen} ${gapLen}`} strokeLinecap="round" 
            transform={`rotate(135, ${cx}, ${cy})`} 
          />
          {!isAnomaly && rul !== undefined && (
              <motion.circle 
                cx={cx} cy={cy} r={trackR} fill="none" 
                stroke={strokeColor} strokeWidth={strokeW} 
                strokeDasharray={`${progress} ${C - progress}`} strokeLinecap="round" 
                transform={`rotate(135, ${cx}, ${cy})`} 
                className="transition-all duration-1000 ease-out drop-shadow-md" 
                style={{ filter: `drop-shadow(0px 0px 10px ${glowColor})` }}
              />
          )}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center pt-2 z-30">
          <span className="text-5xl font-bold tabular-nums tracking-tight text-white mb-1" 
                style={{ textShadow: `0 0 20px ${glowColor}` }}>
              {isAnomaly ? "ERR" : (rul ? rul.toFixed(0) : "---")}
          </span>
          <span className="text-xs font-medium uppercase tracking-widest text-slate-500">
             {isAnomaly ? "Offline" : "RUL"}
          </span>
        </div>
      </div>
    </motion.div>
  );
};

export default Gauge;
