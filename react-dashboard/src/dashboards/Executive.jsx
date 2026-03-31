import React, { useState, useEffect } from 'react';
import { DollarSign, Bed, Smile, Settings, TrendingUp, TrendingDown } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, PieChart, Pie, Cell } from 'recharts';

const Executive = () => {
  const [metrics, setMetrics] = useState({
    revenue: 124580,
    bedUtilization: 87.4,
    satisfaction: 4.6,
    efficiency: 92.1
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics({
        revenue: 124580 + Math.floor(Math.random() * 5000 - 2500),
        bedUtilization: (85 + Math.random() * 10).toFixed(1),
        satisfaction: (4.4 + Math.random() * 0.4).toFixed(1),
        efficiency: (90 + Math.random() * 5).toFixed(1)
      });
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const kpiCards = [
    { title: 'Daily Revenue Impact', value: `$${metrics.revenue.toLocaleString()}`, icon: DollarSign, color: 'bg-green-100 text-green-600', trend: 'up', change: '8.2%' },
    { title: 'Bed Utilization Rate', value: `${metrics.bedUtilization}%`, icon: Bed, color: 'bg-blue-100 text-blue-600', trend: 'stable', change: 'Target: 85-90%' },
    { title: 'Patient Satisfaction', value: `${metrics.satisfaction}/5.0`, icon: Smile, color: 'bg-purple-100 text-purple-600', trend: 'up', change: '+0.3 vs last week' },
    { title: 'Operational Efficiency', value: `${metrics.efficiency}%`, icon: Settings, color: 'bg-orange-100 text-orange-600', trend: 'down', change: '-1.2% vs last month' }
  ];

  const revenueData = [
    { day: 'Mon', revenue: 118, occupancy: 84 },
    { day: 'Tue', revenue: 122, occupancy: 86 },
    { day: 'Wed', revenue: 120, occupancy: 85 },
    { day: 'Thu', revenue: 125, occupancy: 88 },
    { day: 'Fri', revenue: 124, occupancy: 87 },
    { day: 'Sat', revenue: 119, occupancy: 83 },
    { day: 'Sun', revenue: 124, occupancy: 87 }
  ];

  const deptData = [
    { dept: 'ICU', score: 92 },
    { dept: 'Emergency', score: 88 },
    { dept: 'Surgery', score: 95 },
    { dept: 'General', score: 87 },
    { dept: 'Pediatrics', score: 91 }
  ];

  const qualityData = [
    { subject: 'Patient Safety', A: 95, B: 95 },
    { subject: 'Clinical Outcomes', A: 88, B: 90 },
    { subject: 'Patient Experience', A: 92, B: 95 },
    { subject: 'Efficiency', A: 87, B: 90 },
    { subject: 'Staff Satisfaction', A: 85, B: 90 }
  ];

  const costData = [
    { name: 'Staffing', value: 45, color: '#3b82f6' },
    { name: 'Supplies', value: 25, color: '#22c55e' },
    { name: 'Equipment', value: 15, color: '#f59e0b' },
    { name: 'Utilities', value: 8, color: '#ef4444' },
    { name: 'Other', value: 7, color: '#6b7280' }
  ];

  return (
    <div className="space-y-8">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {kpiCards.map((card, index) => (
          <div key={index} className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div className="flex items-center justify-between mb-4">
              <div>
                <p className="text-gray-500 text-sm">{card.title}</p>
                <p className="text-3xl font-bold text-gray-800">{card.value}</p>
              </div>
              <div className={`${card.color} p-3 rounded-full`}>
                <card.icon className="w-6 h-6" />
              </div>
            </div>
            <div className="flex items-center text-sm">
              {card.trend === 'up' && <TrendingUp className="w-4 h-4 text-green-600 mr-1" />}
              {card.trend === 'down' && <TrendingDown className="w-4 h-4 text-red-600 mr-1" />}
              <span className={card.trend === 'up' ? 'text-green-600' : card.trend === 'down' ? 'text-red-600' : 'text-gray-600'}>
                {card.change}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6 lg:col-span-2">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-800">Revenue & Occupancy Trends</h3>
            <div className="flex space-x-2">
              <button className="px-3 py-1 text-xs bg-green-100 text-green-700 rounded-lg">7D</button>
              <button className="px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded-lg">30D</button>
              <button className="px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded-lg">90D</button>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={revenueData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" domain={[0, 100]} />
              <Tooltip />
              <Line yAxisId="left" type="monotone" dataKey="revenue" stroke="#22c55e" strokeWidth={2} name="Revenue ($K)" />
              <Line yAxisId="right" type="monotone" dataKey="occupancy" stroke="#3b82f6" strokeWidth={2} name="Occupancy (%)" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Key Metrics</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">Avg Length of Stay</span>
              <span className="font-semibold text-gray-800">4.2 days</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">Readmission Rate</span>
              <span className="font-semibold text-green-600">8.5%</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">Mortality Rate</span>
              <span className="font-semibold text-green-600">1.2%</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">Infection Rate</span>
              <span className="font-semibold text-green-600">0.8%</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm text-gray-600">Staff Productivity</span>
              <span className="font-semibold text-blue-600">94.3%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Department Performance</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={deptData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="dept" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Bar dataKey="score" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Cost Analysis</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={costData} cx="50%" cy="50%" outerRadius={80} dataKey="value">
                {costData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Quality Metrics</h3>
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart cx="50%" cy="50%" outerRadius="80%" data={qualityData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="subject" />
              <PolarRadiusAxis angle={30} domain={[0, 100]} />
              <Radar name="Current" dataKey="A" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
              <Radar name="Target" dataKey="B" stroke="#22c55e" fill="#22c55e" fillOpacity={0.1} />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Alerts */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-bold text-gray-800 mb-4">Executive Alerts</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <h4 className="font-semibold text-red-800 flex items-center">
              <AlertTriangle className="w-5 h-5 mr-2" />
              ICU Capacity Alert
            </h4>
            <p className="text-sm text-red-600">ICU East at 95% capacity - Consider transfers</p>
            <span className="text-xs text-red-500">2 mins ago</span>
          </div>
          <div className="p-4 bg-orange-50 border border-orange-200 rounded-lg">
            <h4 className="font-semibold text-orange-800 flex items-center">
              <TrendingUp className="w-5 h-5 mr-2" />
              Revenue Target
            </h4>
            <p className="text-sm text-orange-600">Daily revenue 12% below forecast</p>
            <span className="text-xs text-orange-500">15 mins ago</span>
          </div>
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="font-semibold text-blue-800 flex items-center">
              <Users className="w-5 h-5 mr-2" />
              Staffing Update
            </h4>
            <p className="text-sm text-blue-600">Nursing staff overtime reduced by 18%</p>
            <span className="text-xs text-blue-500">1 hour ago</span>
          </div>
        </div>
      </div>
    </div>
  );
};

// Import AlertTriangle and Users
import { AlertTriangle, Users } from 'lucide-react';

export default Executive;
