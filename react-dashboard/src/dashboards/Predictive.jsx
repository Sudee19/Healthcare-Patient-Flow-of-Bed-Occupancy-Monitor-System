import React, { useState, useEffect } from 'react';
import { Brain, AlertTriangle, Users, TrendingUp, Clock, Zap } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, PieChart, Pie, Cell } from 'recharts';

const Predictive = () => {
  const [predictions, setPredictions] = useState({
    nextHour: 82.3,
    peakForecast: 89.7,
    anomalies: 2,
    optimalStaff: 156
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setPredictions({
        nextHour: (80 + Math.random() * 10).toFixed(1),
        peakForecast: (85 + Math.random() * 8).toFixed(1),
        anomalies: Math.floor(Math.random() * 4),
        optimalStaff: 150 + Math.floor(Math.random() * 15)
      });
    }, 15000);
    return () => clearInterval(interval);
  }, []);

  const heatmapData = [
    { ward: 'ICU East', intensity: 95, level: 'critical' },
    { ward: 'Emergency', intensity: 88, level: 'warning' },
    { ward: 'ICU West', intensity: 82, level: 'warning' },
    { ward: 'General A', intensity: 78, level: 'normal' },
    { ward: 'Surgery', intensity: 72, level: 'normal' },
    { ward: 'General B', intensity: 68, level: 'normal' },
    { ward: 'Maternity', intensity: 65, level: 'normal' },
    { ward: 'Pediatrics', intensity: 58, level: 'normal' }
  ];

  const forecastData = [
    { day: 'Mon', predicted: 82, historical: 80 },
    { day: 'Tue', predicted: 85, historical: 83 },
    { day: 'Wed', predicted: 88, historical: 85 },
    { day: 'Thu', predicted: 91, historical: 87 },
    { day: 'Fri', predicted: 89, historical: 86 },
    { day: 'Sat', predicted: 84, historical: 81 },
    { day: 'Sun', predicted: 86, historical: 83 }
  ];

  const features = [
    { name: 'Historical Occupancy', importance: 92 },
    { name: 'Time of Day', importance: 85 },
    { name: 'Day of Week', importance: 78 },
    { name: 'Seasonal Trends', importance: 72 },
    { name: 'Emergency Admissions', importance: 68 },
    { name: 'Discharge Rate', importance: 64 }
  ];

  const qualityData = [
    { subject: 'Patient Safety', A: 95, B: 95 },
    { subject: 'Clinical Outcomes', A: 88, B: 90 },
    { subject: 'Patient Experience', A: 92, B: 95 },
    { subject: 'Efficiency', A: 87, B: 90 },
    { subject: 'Staff Satisfaction', A: 85, B: 90 }
  ];

  const accuracyData = [
    { name: 'Accurate', value: 78, color: '#22c55e' },
    { name: 'Within 5%', value: 16, color: '#3b82f6' },
    { name: 'Error', value: 6, color: '#ef4444' }
  ];

  const insights = [
    { icon: Users, color: 'blue', title: 'Staffing Recommendation', message: 'Increase nursing staff by 12% for predicted surge' },
    { icon: Bed, color: 'orange', title: 'Capacity Planning', message: 'ICU capacity will reach 95% by 2 PM - consider early discharges' },
    { icon: Zap, color: 'purple', title: 'Resource Allocation', message: 'Medical supplies demand expected to increase 18% next week' },
    { icon: Clock, color: 'green', title: 'Efficiency Insight', message: 'Optimal discharge window: 10 AM - 2 PM for faster bed turnover' },
    { icon: AlertTriangle, color: 'red', title: 'Risk Alert', message: 'Readmission risk elevated for cardiac patients - monitor closely' },
    { icon: TrendingUp, color: 'indigo', title: 'Trend Analysis', message: 'Weekend occupancy patterns shifting - adjust staffing models' }
  ];

  const getLevelColor = (level) => {
    if (level === 'critical') return 'bg-red-500';
    if (level === 'warning') return 'bg-orange-500';
    return 'bg-green-500';
  };

  return (
    <div className="space-y-6">
      {/* Prediction Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-6 border border-purple-200">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-purple-600 text-sm font-semibold">Next Hour Occupancy</p>
              <p className="text-3xl font-bold text-gray-800">{predictions.nextHour}%</p>
            </div>
            <div className="bg-purple-100 p-3 rounded-full">
              <Clock className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <p className="text-sm text-green-600 font-semibold">94% Confidence</p>
        </div>

        <div className="bg-gradient-to-br from-indigo-50 to-indigo-100 rounded-xl p-6 border border-indigo-200">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-indigo-600 text-sm font-semibold">24H Peak Forecast</p>
              <p className="text-3xl font-bold text-gray-800">{predictions.peakForecast}%</p>
            </div>
            <div className="bg-indigo-100 p-3 rounded-full">
              <TrendingUp className="w-6 h-6 text-indigo-600" />
            </div>
          </div>
          <p className="text-sm text-green-600 font-semibold">Expected at 14:00</p>
        </div>

        <div className="bg-gradient-to-br from-red-50 to-red-100 rounded-xl p-6 border border-red-200">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-red-600 text-sm font-semibold">Anomaly Alerts</p>
              <p className="text-3xl font-bold text-gray-800">{predictions.anomalies}</p>
            </div>
            <div className="bg-red-100 p-3 rounded-full">
              <AlertTriangle className="w-6 h-6 text-red-600" />
            </div>
          </div>
          <p className="text-sm text-red-600 font-semibold">ICU & Emergency</p>
        </div>

        <div className="bg-gradient-to-br from-emerald-50 to-emerald-100 rounded-xl p-6 border border-emerald-200">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-emerald-600 text-sm font-semibold">Optimal Staffing</p>
              <p className="text-3xl font-bold text-gray-800">{predictions.optimalStaff}</p>
            </div>
            <div className="bg-emerald-100 p-3 rounded-full">
              <Users className="w-6 h-6 text-emerald-600" />
            </div>
          </div>
          <p className="text-sm text-emerald-600 font-semibold">+14 needed</p>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">7-Day Occupancy Forecast</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={forecastData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="day" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Line type="monotone" dataKey="predicted" stroke="#8b5cf6" strokeWidth={3} name="Predicted" />
              <Line type="monotone" dataKey="historical" stroke="#9ca3af" strokeWidth={2} strokeDasharray="5 5" name="Historical" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Demand Intensity Heatmap</h3>
          <div className="space-y-2">
            {heatmapData.map((item, index) => (
              <div key={index} className="flex items-center space-x-3">
                <span className="w-24 text-sm text-gray-600">{item.ward}</span>
                <div className="flex-1 bg-gray-200 rounded-full h-4">
                  <div className={`${getLevelColor(item.level)} h-4 rounded-full`} style={{ width: `${item.intensity}%` }}></div>
                </div>
                <span className="w-10 text-sm font-semibold text-gray-800">{item.intensity}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Model Accuracy</h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={accuracyData} cx="50%" cy="50%" outerRadius={80} dataKey="value">
                {accuracyData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-4 grid grid-cols-2 gap-4 text-center">
            <div className="bg-green-50 rounded-lg p-3">
              <p className="text-2xl font-bold text-green-600">94.2%</p>
              <p className="text-xs text-gray-600">Overall Accuracy</p>
            </div>
            <div className="bg-blue-50 rounded-lg p-3">
              <p className="text-2xl font-bold text-blue-600">0.92</p>
              <p className="text-xs text-gray-600">R² Score</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Feature Importance</h3>
          <div className="space-y-3">
            {features.map((feature, index) => (
              <div key={index} className="flex items-center space-x-3">
                <span className="w-32 text-xs text-gray-600">{feature.name}</span>
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${feature.importance}%` }}></div>
                </div>
                <span className="w-8 text-xs font-semibold text-gray-800">{feature.importance}%</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Quality Metrics</h3>
          <ResponsiveContainer width="100%" height={200}>
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

      {/* Insights */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-bold text-gray-800 mb-4">AI-Generated Insights</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {insights.map((insight, index) => (
            <div key={index} className={`p-4 border-l-4 rounded-lg ${
              insight.color === 'blue' ? 'border-blue-400 bg-blue-50' :
              insight.color === 'orange' ? 'border-orange-400 bg-orange-50' :
              insight.color === 'purple' ? 'border-purple-400 bg-purple-50' :
              insight.color === 'green' ? 'border-green-400 bg-green-50' :
              insight.color === 'red' ? 'border-red-400 bg-red-50' :
              'border-indigo-400 bg-indigo-50'
            }`}>
              <div className="flex items-start space-x-3">
                <insight.icon className={`w-5 h-5 mt-1 text-${insight.color}-600`} />
                <div>
                  <h4 className="font-semibold text-gray-800 text-sm">{insight.title}</h4>
                  <p className="text-sm text-gray-600 mt-1">{insight.message}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

// Import missing icons
import { Bed } from 'lucide-react';

export default Predictive;
