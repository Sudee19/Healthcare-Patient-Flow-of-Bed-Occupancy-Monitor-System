import React from 'react';
import { Trophy, Medal, Target, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

const Performance = () => {
  const wardPerformance = [
    { name: 'Pediatrics', score: 94.2, satisfaction: 4.7, waitTime: 12, efficiency: 95, safety: 98, trend: 'up' },
    { name: 'Maternity', score: 91.8, satisfaction: 4.6, waitTime: 15, efficiency: 92, safety: 96, trend: 'stable' },
    { name: 'General A', score: 89.5, satisfaction: 4.4, waitTime: 18, efficiency: 90, safety: 94, trend: 'up' },
    { name: 'Surgery', score: 88.3, satisfaction: 4.5, waitTime: 20, efficiency: 91, safety: 95, trend: 'stable' },
    { name: 'ICU West', score: 85.7, satisfaction: 4.3, waitTime: 8, efficiency: 88, safety: 97, trend: 'down' },
    { name: 'ICU East', score: 84.2, satisfaction: 4.2, waitTime: 5, efficiency: 89, safety: 96, trend: 'down' },
    { name: 'General B', score: 79.4, satisfaction: 4.0, waitTime: 25, efficiency: 82, safety: 91, trend: 'up' },
    { name: 'Emergency', score: 72.8, satisfaction: 3.8, waitTime: 45, efficiency: 78, safety: 89, trend: 'stable' }
  ];

  const topPerformers = [
    { name: 'Dr. Sarah Johnson', role: 'Senior Nurse', ward: 'Pediatrics', score: 98.5, metric: 'Patient Care' },
    { name: 'Dr. Michael Chen', role: 'Physician', ward: 'Surgery', score: 97.2, metric: 'Surgery Success' },
    { name: 'Lisa Rodriguez', role: 'Head Nurse', ward: 'Maternity', score: 96.8, metric: 'Team Leadership' },
    { name: 'Dr. James Wilson', role: 'Attending', ward: 'ICU East', score: 95.4, metric: 'Critical Care' }
  ];

  const trendData = [
    { week: 'Week 1', performance: 82.5 },
    { week: 'Week 2', performance: 84.2 },
    { week: 'Week 3', performance: 86.1 },
    { week: 'Week 4', performance: 87.5 }
  ];

  const qualityMetrics = [
    { subject: 'Patient Safety', A: 95, fullMark: 100 },
    { subject: 'Clinical Outcomes', A: 88, fullMark: 100 },
    { subject: 'Patient Experience', A: 92, fullMark: 100 },
    { subject: 'Efficiency', A: 87, fullMark: 100 },
    { subject: 'Staff Satisfaction', A: 85, fullMark: 100 }
  ];

  const keyMetrics = [
    { name: 'Patient Satisfaction', value: 4.4, target: 4.5, unit: '/5.0', status: 'good' },
    { name: 'Average Wait Time', value: 18.5, target: 15, unit: 'min', status: 'warning' },
    { name: 'Bed Turnover Rate', value: 4.2, target: 4.0, unit: 'days', status: 'excellent' },
    { name: 'Staff Productivity', value: 91.3, target: 90, unit: '%', status: 'excellent' },
    { name: 'Safety Incidents', value: 0.8, target: 1.0, unit: '/1000', status: 'excellent' }
  ];

  const improvements = [
    { area: 'Emergency Wait Times', current: '45 min', target: '30 min', priority: 'high' },
    { area: 'Discharge Process', current: '4.2 days', target: '3.5 days', priority: 'medium' },
    { area: 'ICU Staffing Ratio', current: '1:3', target: '1:2.5', priority: 'high' },
    { area: 'Equipment Utilization', current: '72%', target: '85%', priority: 'medium' }
  ];

  const getScoreColor = (score) => {
    if (score >= 90) return 'bg-green-100 text-green-800';
    if (score >= 80) return 'bg-blue-100 text-blue-800';
    return 'bg-orange-100 text-orange-800';
  };

  const getStatusIcon = (status) => {
    if (status === 'excellent') return <TrendingUp className="w-4 h-4 text-green-600" />;
    if (status === 'warning') return <TrendingDown className="w-4 h-4 text-orange-600" />;
    return <Minus className="w-4 h-4 text-gray-600" />;
  };

  const getTrendIcon = (trend) => {
    if (trend === 'up') return <TrendingUp className="w-4 h-4 text-green-600" />;
    if (trend === 'down') return <TrendingDown className="w-4 h-4 text-red-600" />;
    return <Minus className="w-4 h-4 text-gray-500" />;
  };

  return (
    <div className="space-y-6">
      {/* Header Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-gray-500 text-sm">Overall Performance</p>
              <p className="text-4xl font-bold text-orange-600">87.5</p>
            </div>
            <div className="relative w-16 h-16">
              <svg className="w-16 h-16 transform -rotate-90">
                <circle cx="32" cy="32" r="28" fill="none" stroke="#e2e8f0" strokeWidth="4"/>
                <circle cx="32" cy="32" r="28" fill="none" stroke="#ea580c" strokeWidth="4" 
                        strokeDasharray="176" strokeDashoffset="22"/>
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xs font-bold text-orange-600">A-</span>
              </div>
            </div>
          </div>
          <div className="flex items-center text-sm">
            <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
            <span className="text-green-600 font-semibold">3.2%</span>
            <span className="text-gray-500 ml-1">vs last month</span>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-gray-500 text-sm">Top Performer</p>
              <p className="text-2xl font-bold text-gray-800">Pediatrics</p>
            </div>
            <div className="bg-yellow-100 p-3 rounded-full">
              <Medal className="w-6 h-6 text-yellow-600" />
            </div>
          </div>
          <p className="text-sm text-gray-600">
            Score: <span className="font-bold text-green-600">94.2/100</span>
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-gray-500 text-sm">Staff Efficiency</p>
              <p className="text-4xl font-bold text-blue-600">91.3%</p>
            </div>
            <div className="bg-blue-100 p-3 rounded-full">
              <Target className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <p className="text-sm text-green-600 font-semibold">Optimal</p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-gray-500 text-sm">Needs Attention</p>
              <p className="text-2xl font-bold text-gray-800">Emergency</p>
            </div>
            <div className="bg-red-100 p-3 rounded-full">
              <Trophy className="w-6 h-6 text-red-600" />
            </div>
          </div>
          <p className="text-sm text-gray-600">
            Score: <span className="font-bold text-orange-600">72.8/100</span>
          </p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Ward Performance Rankings</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={wardPerformance}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Bar dataKey="score" fill="#8b5cf6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">30-Day Performance Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="week" />
              <YAxis domain={[70, 100]} />
              <Tooltip />
              <Line type="monotone" dataKey="performance" stroke="#ea580c" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Ward Cards */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-bold text-gray-800 mb-4">Detailed Ward Performance</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {wardPerformance.slice(0, 4).map((ward, index) => (
            <div key={index} className={`rounded-xl p-4 ${
              ward.score >= 90 ? 'bg-gradient-to-br from-green-50 to-green-100 border border-green-200' :
              ward.score >= 80 ? 'bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200' :
              'bg-gradient-to-br from-orange-50 to-orange-100 border border-orange-200'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <h4 className="font-bold text-gray-800">{ward.name}</h4>
                {getTrendIcon(ward.trend)}
              </div>
              <p className="text-3xl font-bold mb-2">{ward.score}</p>
              <div className="text-sm opacity-80">
                <p>Satisfaction: {ward.satisfaction}/5</p>
                <p>Wait: {ward.waitTime} min</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Three Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Top Performers */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Staff Top Performers</h3>
          <div className="space-y-4">
            {topPerformers.map((performer, index) => (
              <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                <Medal className={`w-6 h-6 ${
                  index === 0 ? 'text-yellow-500' :
                  index <= 2 ? 'text-gray-400' : 'text-orange-600'
                }`} />
                <div className="flex-1">
                  <h4 className="font-semibold text-gray-800 text-sm">{performer.name}</h4>
                  <p className="text-xs text-gray-600">{performer.role} - {performer.ward}</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-orange-600">{performer.score}</p>
                  <p className="text-xs text-gray-500">{performer.metric}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Key Metrics */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Key Performance Metrics</h3>
          <div className="space-y-4">
            {keyMetrics.map((metric, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <p className="text-sm text-gray-600">{metric.name}</p>
                  <p className="text-xl font-bold text-gray-800">{metric.value}{metric.unit}</p>
                </div>
                <div className="text-right">
                  {getStatusIcon(metric.status)}
                  <p className="text-xs text-gray-500">Target: {metric.target}{metric.unit}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quality Radar */}
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Quality Metrics</h3>
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart cx="50%" cy="50%" outerRadius="80%" data={qualityMetrics}>
              <PolarGrid />
              <PolarAngleAxis dataKey="subject" />
              <PolarRadiusAxis angle={30} domain={[0, 100]} />
              <Radar name="Current" dataKey="A" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Performance Table */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-bold text-gray-800 mb-4">Comprehensive Performance Report</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ward</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Score</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Satisfaction</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Wait Time</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Efficiency</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Safety</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Trend</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {wardPerformance.map((ward, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{ward.name}</td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full ${getScoreColor(ward.score)}`}>
                      {ward.score}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">{ward.satisfaction}/5.0</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{ward.waitTime} min</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{ward.efficiency}%</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{ward.safety}%</td>
                  <td className="px-6 py-4">{getTrendIcon(ward.trend)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Improvement Areas */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-bold text-gray-800 mb-4">Improvement Areas</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {improvements.map((item, index) => (
            <div key={index} className={`p-4 border-l-4 rounded-r-lg ${
              item.priority === 'high' ? 'border-red-400 bg-red-50' :
              item.priority === 'medium' ? 'border-orange-400 bg-orange-50' :
              'border-blue-400 bg-blue-50'
            }`}>
              <h4 className="font-semibold text-gray-800">{item.area}</h4>
              <div className="flex items-center justify-between mt-2 text-sm">
                <span className="text-red-600">Current: {item.current}</span>
                <span className="text-green-600">Target: {item.target}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Performance;
