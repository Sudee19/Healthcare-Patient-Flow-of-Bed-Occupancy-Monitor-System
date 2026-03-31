import React, { useState, useEffect } from 'react';
import { Radio, Activity, Users, AlertTriangle, Clock } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const RealTime = () => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [metrics, setMetrics] = useState({
    occupancy: 76.3,
    queue: 12,
    waitTime: 18,
    admissions: 8,
    alerts: 2
  });

  const [chartData, setChartData] = useState(Array(20).fill({ value: 75 }));

  useEffect(() => {
    const timeInterval = setInterval(() => setCurrentTime(new Date()), 1000);
    
    const metricsInterval = setInterval(() => {
      setMetrics({
        occupancy: (70 + Math.random() * 20).toFixed(1),
        queue: Math.floor(5 + Math.random() * 15),
        waitTime: Math.floor(10 + Math.random() * 20),
        admissions: Math.floor(5 + Math.random() * 10),
        alerts: Math.floor(Math.random() * 5)
      });
    }, 5000);

    const chartInterval = setInterval(() => {
      const newValue = 70 + Math.random() * 20;
      setChartData(prev => [...prev.slice(1), { value: newValue }]);
    }, 3000);

    return () => {
      clearInterval(timeInterval);
      clearInterval(metricsInterval);
      clearInterval(chartInterval);
    };
  }, []);

  const wards = [
    { name: 'ICU East', occupancy: 90, status: 'critical', trend: 'up' },
    { name: 'ICU West', occupancy: 80, status: 'warning', trend: 'stable' },
    { name: 'Emergency', occupancy: 90, status: 'critical', trend: 'up' },
    { name: 'General A', occupancy: 80, status: 'normal', trend: 'stable' },
    { name: 'General B', occupancy: 70, status: 'normal', trend: 'down' },
    { name: 'Pediatrics', occupancy: 70, status: 'normal', trend: 'stable' }
  ];

  const events = [
    { time: '14:32:15', type: 'admission', ward: 'ICU East', message: 'Patient admitted to ICU East - Bed A-001' },
    { time: '14:31:42', type: 'discharge', ward: 'General A', message: 'Patient discharged from General A' },
    { time: '14:30:18', type: 'alert', ward: 'Emergency', message: 'Emergency ward capacity exceeded 90%' },
    { time: '14:29:55', type: 'transfer', ward: 'ICU West', message: 'Patient transferred from Emergency to ICU West' },
    { time: '14:28:33', type: 'admission', ward: 'Pediatrics', message: 'Pediatric patient admitted - Bed P-015' }
  ];

  const getStatusColor = (status) => {
    if (status === 'critical') return 'bg-red-500';
    if (status === 'warning') return 'bg-orange-500';
    return 'bg-green-500';
  };

  const getTrendIcon = (trend) => {
    if (trend === 'up') return '↑';
    if (trend === 'down') return '↓';
    return '→';
  };

  return (
    <div className="space-y-6">
      {/* Live Status Bar */}
      <div className="bg-green-500 text-white py-3 px-4 rounded-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-white rounded-full mr-3 animate-pulse"></div>
            <span className="font-semibold">Live Monitoring Active</span>
          </div>
          <div className="text-sm">
            Last Update: {currentTime.toLocaleTimeString()}
          </div>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Current Occupancy</p>
              <p className="text-3xl font-bold text-blue-600">{metrics.occupancy}%</p>
              <p className="text-sm text-gray-500 mt-2">
                <span className="text-green-500">↑</span> +2.1% from last hour
              </p>
            </div>
            <div className="bg-blue-100 p-3 rounded-full">
              <Activity className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Patients in Queue</p>
              <p className="text-3xl font-bold text-orange-600">{metrics.queue}</p>
              <p className="text-sm text-gray-500 mt-2">
                Avg wait: {metrics.waitTime} min
              </p>
            </div>
            <div className="bg-orange-100 p-3 rounded-full">
              <Users className="w-6 h-6 text-orange-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Active Admissions</p>
              <p className="text-3xl font-bold text-green-600">{metrics.admissions}</p>
              <p className="text-sm text-gray-500 mt-2">
                <span className="text-red-500">↓</span> -3 from yesterday
              </p>
            </div>
            <div className="bg-green-100 p-3 rounded-full">
              <Radio className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-500 text-sm">Critical Alerts</p>
              <p className="text-3xl font-bold text-red-600">{metrics.alerts}</p>
              <p className="text-sm text-gray-500 mt-2">
                Action required
              </p>
            </div>
            <div className="bg-red-100 p-3 rounded-full">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Real-time Chart */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h2 className="text-xl font-bold text-gray-800 mb-4 flex items-center">
          <Radio className="w-5 h-5 mr-2 text-purple-600" />
          Real-time Occupancy Stream
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis hide />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Line 
              type="monotone" 
              dataKey="value" 
              stroke="#8b5cf6" 
              strokeWidth={2}
              dot={false}
              fill="rgba(139, 92, 246, 0.1)"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Ward Grid & Event Log */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Ward Status Grid</h3>
          <div className="grid grid-cols-2 gap-4">
            {wards.map((ward, index) => (
              <div key={index} className="bg-gray-50 rounded-lg p-4 border-l-4 border-gray-300">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-gray-800">{ward.name}</h4>
                  <span className="text-sm">{getTrendIcon(ward.trend)}</span>
                </div>
                <div className={`text-2xl font-bold ${
                  ward.status === 'critical' ? 'text-red-600' :
                  ward.status === 'warning' ? 'text-orange-600' :
                  'text-green-600'
                }`}>
                  {ward.occupancy}%
                </div>
                <div className="text-xs text-gray-500 mt-1">{ward.status}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
            <Clock className="w-5 h-5 mr-2 text-blue-600" />
            Live Event Stream
          </h3>
          <div className="space-y-3 max-h-80 overflow-y-auto">
            {events.map((event, index) => (
              <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className={`w-2 h-2 rounded-full ${
                  event.type === 'admission' ? 'bg-green-500' :
                  event.type === 'discharge' ? 'bg-blue-500' :
                  event.type === 'alert' ? 'bg-red-500' : 'bg-purple-500'
                }`}></div>
                <div className="flex-1">
                  <p className="text-sm text-gray-800">{event.message}</p>
                </div>
                <span className="text-xs text-gray-500">{event.time}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default RealTime;
