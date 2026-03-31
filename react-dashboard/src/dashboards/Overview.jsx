import React, { useState, useEffect } from 'react';
import { 
  Bed, 
  UserCheck, 
  BedDouble, 
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Minus
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';

const Overview = () => {
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const stats = [
    { 
      title: 'Total Beds', 
      value: 350, 
      icon: BedDouble, 
      color: 'bg-blue-100 text-blue-600',
      trend: 'stable',
      trendValue: '100% Available'
    },
    { 
      title: 'Occupied Beds', 
      value: 267, 
      icon: UserCheck, 
      color: 'bg-orange-100 text-orange-600',
      trend: 'up',
      trendValue: '76.3% Occupancy'
    },
    { 
      title: 'Available Beds', 
      value: 83, 
      icon: Bed, 
      color: 'bg-green-100 text-green-600',
      trend: 'stable',
      trendValue: '23.7% Free'
    },
    { 
      title: 'Critical Alerts', 
      value: 2, 
      icon: AlertTriangle, 
      color: 'bg-red-100 text-red-600',
      trend: 'up',
      trendValue: 'Action Required'
    }
  ];

  const occupancyData = [
    { time: '00:00', occupancy: 65 },
    { time: '04:00', occupancy: 62 },
    { time: '08:00', occupancy: 68 },
    { time: '12:00', occupancy: 75 },
    { time: '16:00', occupancy: 78 },
    { time: '20:00', occupancy: 76 },
    { time: '24:00', occupancy: 73 }
  ];

  const wardData = [
    { name: 'ICU East', value: 90, color: '#ef4444' },
    { name: 'ICU West', value: 80, color: '#f59e0b' },
    { name: 'Emergency', value: 90, color: '#ef4444' },
    { name: 'General A', value: 80, color: '#3b82f6' },
    { name: 'General B', value: 70, color: '#10b981' },
    { name: 'Pediatrics', value: 70, color: '#10b981' }
  ];

  const wardTableData = [
    { name: 'ICU East', total: 20, occupied: 18, percent: 90, status: 'critical', trend: 'up' },
    { name: 'ICU West', total: 20, occupied: 16, percent: 80, status: 'warning', trend: 'stable' },
    { name: 'Emergency', total: 50, occupied: 45, percent: 90, status: 'warning', trend: 'up' },
    { name: 'General A', total: 60, occupied: 48, percent: 80, status: 'normal', trend: 'stable' },
    { name: 'General B', total: 60, occupied: 42, percent: 70, status: 'normal', trend: 'down' },
    { name: 'Pediatrics', total: 40, occupied: 28, percent: 70, status: 'normal', trend: 'stable' },
    { name: 'Maternity', total: 30, occupied: 22, percent: 73, status: 'normal', trend: 'up' },
    { name: 'Surgery', total: 70, occupied: 48, percent: 69, status: 'normal', trend: 'stable' }
  ];

  const getTrendIcon = (trend) => {
    if (trend === 'up') return <TrendingUp className="w-4 h-4 text-red-500" />;
    if (trend === 'down') return <TrendingDown className="w-4 h-4 text-green-500" />;
    return <Minus className="w-4 h-4 text-gray-500" />;
  };

  const getStatusColor = (status) => {
    if (status === 'critical') return 'bg-red-100 text-red-800';
    if (status === 'warning') return 'bg-orange-100 text-orange-800';
    return 'bg-green-100 text-green-800';
  };

  return (
    <div className="space-y-8">
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white rounded-xl shadow-lg p-6 hover:shadow-xl transition-shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-500 text-sm">{stat.title}</p>
                <p className="text-3xl font-bold text-gray-800">{stat.value}</p>
                <p className={`text-sm mt-2 flex items-center ${
                  stat.trend === 'up' ? 'text-red-600' : 
                  stat.trend === 'down' ? 'text-green-600' : 'text-gray-600'
                }`}>
                  {getTrendIcon(stat.trend)}
                  <span className="ml-1">{stat.trendValue}</span>
                </p>
              </div>
              <div className={`${stat.color} p-3 rounded-full`}>
                <stat.icon className="w-6 h-6" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">24-Hour Occupancy Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={occupancyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Line 
                type="monotone" 
                dataKey="occupancy" 
                stroke="#8b5cf6" 
                strokeWidth={2}
                fill="rgba(139, 92, 246, 0.1)"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Ward Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={wardData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={100}
                paddingAngle={5}
                dataKey="value"
              >
                {wardData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Ward Table */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-bold text-gray-800 mb-4">Ward Status Details</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ward</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total Beds</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Occupied</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Occupancy %</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Trend</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {wardTableData.map((ward, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{ward.name}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{ward.total}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{ward.occupied}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{ward.percent}%</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(ward.status)}`}>
                      {ward.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">{getTrendIcon(ward.trend)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Alerts */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-bold text-gray-800 mb-4">Active Alerts</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center">
              <AlertTriangle className="w-5 h-5 text-red-600 mr-3" />
              <span className="text-red-800">ICU East occupancy above 90% for 2 hours</span>
            </div>
            <span className="text-red-600 text-sm">5 mins ago</span>
          </div>
          <div className="flex items-center justify-between p-4 bg-orange-50 border border-orange-200 rounded-lg">
            <div className="flex items-center">
              <AlertTriangle className="w-5 h-5 text-orange-600 mr-3" />
              <span className="text-orange-800">Emergency ward approaching capacity</span>
            </div>
            <span className="text-orange-600 text-sm">12 mins ago</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Overview;
