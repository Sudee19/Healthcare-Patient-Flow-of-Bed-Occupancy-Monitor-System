import React, { useState, useEffect } from 'react';
import { Route, Activity, Clock, Users, ArrowRight, AlertTriangle, Lightbulb } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const PatientFlow = () => {
  const [activePatients, setActivePatients] = useState(156);

  useEffect(() => {
    const interval = setInterval(() => {
      setActivePatients(150 + Math.floor(Math.random() * 15));
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  const journeySteps = [
    { name: 'Admission', count: 45, icon: '🏥', color: 'bg-emerald-100' },
    { name: 'Triage', count: 38, icon: '🩺', color: 'bg-blue-100' },
    { name: 'Treatment', count: 89, icon: '🏥', color: 'bg-yellow-100' },
    { name: 'Recovery', count: 42, icon: '💚', color: 'bg-purple-100' },
    { name: 'Discharge', count: 28, icon: '🏠', color: 'bg-green-100' }
  ];

  const activePatientsList = [
    { id: 'P-1001', name: 'John Smith', stage: 'Treatment', ward: 'General A', progress: 65, waitTime: '2.5 hrs', status: 'stable' },
    { id: 'P-1002', name: 'Mary Johnson', stage: 'Recovery', ward: 'ICU East', progress: 85, waitTime: '1 day', status: 'improving' },
    { id: 'P-1003', name: 'Robert Brown', stage: 'Triage', ward: 'Emergency', progress: 25, waitTime: '45 min', status: 'urgent' },
    { id: 'P-1004', name: 'Lisa Davis', stage: 'Treatment', ward: 'Surgery', progress: 40, waitTime: '4 hrs', status: 'stable' },
    { id: 'P-1005', name: 'Michael Wilson', stage: 'Recovery', ward: 'General B', progress: 90, waitTime: '2 days', status: 'ready-discharge' },
    { id: 'P-1006', name: 'Sarah Lee', stage: 'Admission', ward: 'Emergency', progress: 10, waitTime: '15 min', status: 'new' }
  ];

  const volumeData = [
    { time: '00:00', admissions: 8, discharges: 3 },
    { time: '04:00', admissions: 5, discharges: 2 },
    { time: '08:00', admissions: 25, discharges: 8 },
    { time: '12:00', admissions: 35, discharges: 22 },
    { time: '16:00', admissions: 28, discharges: 18 },
    { time: '20:00', admissions: 18, discharges: 12 }
  ];

  const bottlenecks = [
    { stage: 'Emergency Triage', delay: '45 min avg', impact: 'high', patients: 12 },
    { stage: 'Bed Assignment', delay: '18 min avg', impact: 'medium', patients: 8 },
    { stage: 'Discharge Processing', delay: '2.1 hrs avg', impact: 'medium', patients: 6 }
  ];

  const optimizations = [
    { title: 'Fast-Track Discharges', message: 'Implement morning discharge rounds to free up 15 beds by 11 AM', impact: 'High', icon: Activity },
    { title: 'Triage Protocol Update', message: 'Revise emergency triage criteria to reduce wait times by 20%', impact: 'High', icon: Users },
    { title: 'Bed Management AI', message: 'Deploy predictive bed allocation to improve turnover by 12%', impact: 'Medium', icon: Activity },
    { title: 'Staff Reallocation', message: 'Shift 3 nurses from General B to Emergency during peak hours', impact: 'Medium', icon: Users }
  ];

  const getStatusColor = (status) => {
    const colors = {
      stable: 'bg-green-100 text-green-800 border-green-400',
      improving: 'bg-blue-100 text-blue-800 border-blue-400',
      urgent: 'bg-red-100 text-red-800 border-red-400',
      'ready-discharge': 'bg-purple-100 text-purple-800 border-purple-400',
      new: 'bg-yellow-100 text-yellow-800 border-yellow-400'
    };
    return colors[status] || colors.stable;
  };

  const getStageColor = (stage) => {
    const colors = {
      Admission: 'border-yellow-400',
      Triage: 'border-blue-400',
      Treatment: 'border-orange-400',
      Recovery: 'border-purple-400'
    };
    return colors[stage] || 'border-gray-400';
  };

  return (
    <div className="space-y-6">
      {/* Journey Flow */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <h3 className="text-lg font-bold text-gray-800 mb-6 flex items-center">
          <Route className="w-5 h-5 mr-2 text-emerald-600" />
          Patient Journey Flow
        </h3>
        <div className="flex items-center justify-between overflow-x-auto pb-4">
          {journeySteps.map((step, index) => (
            <div key={index} className="flex flex-col items-center min-w-[120px] relative">
              <div className={`w-16 h-16 ${step.color} rounded-full flex items-center justify-center mb-2 text-2xl shadow-md`}>
                {step.icon}
              </div>
              <p className="text-sm font-semibold text-gray-700">{step.name}</p>
              <p className="text-xs text-emerald-600">{step.count} patients</p>
              {index < journeySteps.length - 1 && (
                <ArrowRight className="absolute top-8 -right-4 w-6 h-6 text-emerald-400" />
              )}
            </div>
          ))}
        </div>
        <div className="mt-4">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-gradient-to-r from-emerald-400 to-emerald-600 h-full rounded-full" style={{ width: '75%' }}></div>
          </div>
          <p className="text-center text-sm text-gray-500 mt-2">Average Journey Time: 4.2 days</p>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-gray-500 text-sm">Avg Length of Stay</p>
              <p className="text-3xl font-bold text-emerald-600">4.2 <span className="text-lg">days</span></p>
            </div>
            <div className="bg-emerald-100 p-3 rounded-full">
              <Clock className="w-6 h-6 text-emerald-600" />
            </div>
          </div>
          <p className="text-sm text-green-600 flex items-center">
            <ArrowRight className="w-4 h-4 mr-1 rotate-90" />
            0.3 days improvement
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-gray-500 text-sm">Bed Turnover Rate</p>
              <p className="text-3xl font-bold text-blue-600">2.4 <span className="text-lg">/day</span></p>
            </div>
            <div className="bg-blue-100 p-3 rounded-full">
              <Activity className="w-6 h-6 text-blue-600" />
            </div>
          </div>
          <p className="text-sm text-green-600 flex items-center">
            <ArrowRight className="w-4 h-4 mr-1 -rotate-45" />
            12% efficiency
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-gray-500 text-sm">Admission to Bed</p>
              <p className="text-3xl font-bold text-orange-600">18 <span className="text-lg">min</span></p>
            </div>
            <div className="bg-orange-100 p-3 rounded-full">
              <Clock className="w-6 h-6 text-orange-600" />
            </div>
          </div>
          <p className="text-sm text-orange-600">Target: 15 min</p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <p className="text-gray-500 text-sm">Discharge Process</p>
              <p className="text-3xl font-bold text-purple-600">2.1 <span className="text-lg">hrs</span></p>
            </div>
            <div className="bg-purple-100 p-3 rounded-full">
              <Clock className="w-6 h-6 text-purple-600" />
            </div>
          </div>
          <p className="text-sm text-green-600 flex items-center">
            <ArrowRight className="w-4 h-4 mr-1 -rotate-45" />
            On target
          </p>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Patient Volume by Hour</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={volumeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="time" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="admissions" stroke="#10b981" strokeWidth={2} name="Admissions" />
              <Line type="monotone" dataKey="discharges" stroke="#3b82f6" strokeWidth={2} name="Discharges" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">Active Patient Journey Tracking</h3>
          <div className="space-y-3 max-h-60 overflow-y-auto">
            {activePatientsList.map((patient, index) => (
              <div key={index} className={`p-3 bg-white border-l-4 ${getStageColor(patient.stage)} rounded-lg shadow-sm`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-mono text-gray-500">{patient.id}</span>
                    <h4 className="font-semibold text-gray-800">{patient.name}</h4>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(patient.status)}`}>
                    {patient.status}
                  </span>
                </div>
                <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                  <span>{patient.ward}</span>
                  <span>{patient.waitTime}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${patient.progress}%` }}></div>
                </div>
                <p className="text-xs text-gray-500 mt-1">{patient.stage} - {patient.progress}% complete</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottlenecks & Optimizations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
            <AlertTriangle className="w-5 h-5 mr-2 text-red-600" />
            Flow Bottlenecks
          </h3>
          <div className="space-y-4">
            {bottlenecks.map((item, index) => (
              <div key={index} className={`p-4 rounded-lg ${
                item.impact === 'high' ? 'bg-red-50 border border-red-200' :
                item.impact === 'medium' ? 'bg-orange-50 border border-orange-200' :
                'bg-yellow-50 border border-yellow-200'
              }`}>
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-semibold">{item.stage}</h4>
                    <p className="text-sm opacity-80">{item.delay} wait time</p>
                  </div>
                  <div className="text-right">
                    <span className="text-2xl font-bold">{item.patients}</span>
                    <p className="text-xs">waiting</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
            <Lightbulb className="w-5 h-5 mr-2 text-yellow-600" />
            Flow Optimization
          </h3>
          <div className="space-y-3">
            {optimizations.map((opt, index) => (
              <div key={index} className="flex items-start space-x-3 p-4 bg-gray-50 rounded-lg border-l-4 border-emerald-400">
                <div className="bg-emerald-100 p-2 rounded-full">
                  <opt.icon className="w-4 h-4 text-emerald-600" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold text-gray-800">{opt.title}</h4>
                    <span className={`px-2 py-1 text-xs rounded ${
                      opt.impact === 'High' ? 'bg-red-100 text-red-600' :
                      opt.impact === 'Medium' ? 'bg-orange-100 text-orange-600' :
                      'bg-blue-100 text-blue-600'
                    }`}>
                      {opt.impact} Impact
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mt-1">{opt.message}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PatientFlow;
