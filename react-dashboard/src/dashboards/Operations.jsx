import React, { useState, useEffect } from 'react';
import { Server, BedDouble, UserCheck, AlertTriangle, Activity, Clock } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const Operations = () => {
  const [systemLoad, setSystemLoad] = useState(68);
  const [activeBeds, setActiveBeds] = useState(267);
  const [staffOnDuty, setStaffOnDuty] = useState(142);
  const [activeAlerts, setActiveAlerts] = useState(7);

  useEffect(() => {
    const interval = setInterval(() => {
      setSystemLoad(Math.floor(60 + Math.random() * 25));
      setActiveBeds(250 + Math.floor(Math.random() * 30));
      setStaffOnDuty(135 + Math.floor(Math.random() * 15));
      setActiveAlerts(Math.floor(Math.random() * 8));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const wards = [
    { name: 'ICU East', occupancy: 90, status: 'critical', beds: '18/20' },
    { name: 'ICU West', occupancy: 80, status: 'warning', beds: '16/20' },
    { name: 'Emergency', occupancy: 90, status: 'critical', beds: '45/50' },
    { name: 'General A', occupancy: 80, status: 'normal', beds: '48/60' },
    { name: 'General B', occupancy: 70, status: 'normal', beds: '42/60' },
    { name: 'Pediatrics', occupancy: 70, status: 'normal', beds: '28/40' },
    { name: 'Maternity', occupancy: 73, status: 'normal', beds: '22/30' },
    { name: 'Surgery', occupancy: 69, status: 'normal', beds: '48/70' }
  ];

  const events = [
    { time: '14:32:15', type: 'admission', ward: 'ICU East', message: 'Patient admitted to ICU East' },
    { time: '14:31:42', type: 'discharge', ward: 'General A', message: 'Patient discharged from General A' },
    { time: '14:30:18', type: 'alert', ward: 'Emergency', message: 'Emergency ward capacity alert' },
    { time: '14:29:55', type: 'transfer', ward: 'ICU West', message: 'Patient transferred to ICU West' },
    { time: '14:28:33', type: 'admission', ward: 'Pediatrics', message: 'Pediatric patient admitted' }
  ];

  const [chartData, setChartData] = useState(Array(20).fill({ value: 75 }));

  useEffect(() => {
    const interval = setInterval(() => {
      const newValue = 70 + Math.random() * 20;
      setChartData(prev => [...prev.slice(1), { value: newValue }]);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    if (status === 'critical') return 'bg-gradient-to-br from-red-500 to-red-700';
    if (status === 'warning') return 'bg-gradient-to-br from-orange-500 to-orange-700';
    return 'bg-gradient-to-br from-green-500 to-green-700';
  };

  return (
    <div className="space-y-6">
      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 text-white">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-slate-400 text-sm">System Load</p>
              <p className="text-3xl font-bold text-cyan-400">{systemLoad}%</p>
            </div>
            <div className="bg-cyan-500/20 p-3 rounded-full">
              <Server className="w-6 h-6 text-cyan-400" />
            </div>
          </div>
          <div className="w-full bg-slate-700 rounded-full h-2">
            <div className="bg-cyan-400 h-2 rounded-full transition-all duration-500" style={{ width: `${systemLoad}%` }}></div>
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 text-white">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-slate-400 text-sm">Active Beds</p>
              <p className="text-3xl font-bold text-emerald-400">{activeBeds}/350</p>
            </div>
            <div className="bg-emerald-500/20 p-3 rounded-full">
              <BedDouble className="w-6 h-6 text-emerald-400" />
            </div>
          </div>
          <p className="text-sm text-slate-400">
            <span className="text-emerald-400">{350 - activeBeds}</span> beds available
          </p>
        </div>

        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 text-white">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-slate-400 text-sm">Staff on Duty</p>
              <p className="text-3xl font-bold text-amber-400">{staffOnDuty}</p>
            </div>
            <div className="bg-amber-500/20 p-3 rounded-full">
              <UserCheck className="w-6 h-6 text-amber-400" />
            </div>
          </div>
          <p className="text-sm text-slate-400">Nurses: 89 | Doctors: 53</p>
        </div>

        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 text-white">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-slate-400 text-sm">Active Alerts</p>
              <p className="text-3xl font-bold text-rose-400">{activeAlerts}</p>
            </div>
            <div className="bg-rose-500/20 p-3 rounded-full">
              <AlertTriangle className="w-6 h-6 text-rose-400" />
            </div>
          </div>
          <div className="flex space-x-2">
            <span className="px-2 py-1 bg-rose-500/20 text-rose-400 text-xs rounded">2 Critical</span>
            <span className="px-2 py-1 bg-amber-500/20 text-amber-400 text-xs rounded">5 Warning</span>
          </div>
        </div>
      </div>

      {/* Live Chart & Utilization */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 text-white lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold flex items-center">
              <Activity className="w-5 h-5 mr-2 text-cyan-400" />
              Live Occupancy Stream
            </h3>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-green-400 text-xs">LIVE</span>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis hide />
              <YAxis domain={[0, 100]} stroke="#94a3b8" />
              <Tooltip contentStyle={{ backgroundColor: '#1e293b', border: 'none' }} />
              <Line type="monotone" dataKey="value" stroke="#22d3ee" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 text-white">
          <h3 className="text-lg font-bold mb-4 flex items-center">
            <Activity className="w-5 h-5 mr-2 text-emerald-400" />
            Resource Utilization
          </h3>
          <div className="space-y-4">
            {[
              { label: 'Beds', value: 76, color: 'bg-cyan-400' },
              { label: 'Staff', value: 82, color: 'bg-emerald-400' },
              { label: 'Equipment', value: 64, color: 'bg-amber-400' },
              { label: 'ICU Capacity', value: 91, color: 'bg-rose-400' }
            ].map((item, index) => (
              <div key={index}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-400">{item.label}</span>
                  <span className="text-white">{item.value}%</span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div className={`${item.color} h-2 rounded-full transition-all duration-500`} style={{ width: `${item.value}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Ward Grid & Event Log */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 text-white lg:col-span-2">
          <h3 className="text-lg font-bold mb-4">Ward Status Monitor</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {wards.map((ward, index) => (
              <div key={index} className={`${getStatusColor(ward.status)} rounded-lg p-4 text-white`}>
                <div className="flex justify-between items-start mb-2">
                  <h4 className="font-semibold text-sm">{ward.name}</h4>
                  <span className="text-xs opacity-80">{ward.beds}</span>
                </div>
                <p className="text-2xl font-bold">{ward.occupancy}%</p>
                <p className="text-xs opacity-80">Occupancy</p>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-slate-800 rounded-xl border border-slate-700 p-6 text-white">
          <h3 className="text-lg font-bold mb-4 flex items-center">
            <Clock className="w-5 h-5 mr-2 text-cyan-400" />
            Live Event Log
          </h3>
          <div className="space-y-2 max-h-80 overflow-y-auto">
            {events.map((event, index) => (
              <div key={index} className="flex items-center space-x-3 p-2 bg-slate-700/50 rounded-lg text-sm">
                <div className={`w-2 h-2 rounded-full ${
                  event.type === 'admission' ? 'bg-emerald-400' :
                  event.type === 'discharge' ? 'bg-blue-400' :
                  event.type === 'alert' ? 'bg-rose-400' : 'bg-purple-400'
                }`}></div>
                <div className="flex-1">
                  <p className="text-slate-200">{event.message}</p>
                </div>
                <span className="text-slate-500 text-xs">{event.time}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Operations;
