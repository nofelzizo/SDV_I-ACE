import React from 'react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer 
} from 'recharts';

const AnalyticsChart = ({ data }) => {
  // data should be an array of objects e.g., [{ time: '10:00', rpm: 2500, speed: 60 }]
  
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-full w-full text-slate-500 text-sm font-medium">
        Waiting for telemetry stream...
      </div>
    );
  }

  return (
    <div className="h-full w-full relative">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
        >
          <defs>
            <linearGradient id="colorPrimary" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#7C3AED" stopOpacity={0.8}/> {/* Purple */}
              <stop offset="95%" stopColor="#7C3AED" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorSecondary" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#2DD4BF" stopOpacity={0.8}/> {/* Teal */}
              <stop offset="95%" stopColor="#2DD4BF" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
          <XAxis 
             dataKey="time" 
             stroke="rgba(255,255,255,0.3)" 
             fontSize={9} 
             tickLine={false} 
             axisLine={false}
             minTickGap={20}
          />
          <YAxis 
             yAxisId="left"
             stroke="#7C3AED" 
             fontSize={9} 
             tickLine={false} 
             axisLine={false}
             domain={['auto', 'auto']}
             tickFormatter={(val) => Math.round(val)}
             orientation="left"
          />
          <YAxis 
             yAxisId="right"
             stroke="#2DD4BF" 
             fontSize={9} 
             tickLine={false} 
             axisLine={false}
             domain={['auto', 'auto']}
             tickFormatter={(val) => val.toFixed(1)}
             orientation="right"
          />
          <Tooltip 
             contentStyle={{
                 backgroundColor: "rgba(10, 10, 10, 0.9)",
                 borderRadius: "16px",
                 border: "1px solid rgba(255,255,255,0.1)",
                 color: "#fff",
                 boxShadow: "0 12px 40px rgba(0, 0, 0, 0.7)",
                 backdropFilter: "blur(20px)"
             }}
             itemStyle={{ color: "#E2E8F0", fontSize: '11px' }}
             labelStyle={{ color: "#94A3B8", marginBottom: '4px', fontSize: '10px' }}
          />
          <Area 
             yAxisId="right"
             type="monotone" 
             dataKey="Speed" 
             stroke="#2DD4BF" 
             strokeWidth={3}
             fillOpacity={1} 
             fill="url(#colorSecondary)" 
             animationDuration={1500}
          />
          <Area 
             yAxisId="left"
             type="monotone" 
             dataKey="RPM" 
             stroke="#7C3AED" 
             strokeWidth={3}
             fillOpacity={1} 
             fill="url(#colorPrimary)" 
             animationDuration={1500}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default AnalyticsChart;
