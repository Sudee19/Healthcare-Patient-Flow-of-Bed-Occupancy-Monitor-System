import React from 'react';
import { Outlet, NavLink, useLocation } from 'react-router-dom';
import { 
  Hospital, 
  LayoutDashboard, 
  TrendingUp, 
  Settings, 
  Brain, 
  Trophy, 
  Route, 
  Radio, 
  User, 
  LogOut,
  Clock,
  Users
} from 'lucide-react';

const Layout = ({ onLogout }) => {
  const location = useLocation();
  const username = sessionStorage.getItem('username') || 'Admin';
  
  const currentTime = new Date().toLocaleTimeString();

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Overview' },
    { path: '/executive', icon: TrendingUp, label: 'Executive' },
    { path: '/operations', icon: Settings, label: 'Operations' },
    { path: '/predictive', icon: Brain, label: 'Predictive' },
    { path: '/performance', icon: Trophy, label: 'Performance' },
    { path: '/patientflow', icon: Route, label: 'Patient Flow' },
    { path: '/realtime', icon: Radio, label: 'Live Monitor' },
  ];

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Top Navigation */}
      <nav className="bg-gradient-to-r from-purple-600 to-blue-700 shadow-lg">
        <div className="container mx-auto px-4">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <div className="text-white">
                <Hospital className="w-8 h-8" />
              </div>
              <div>
                <h1 className="text-white text-xl font-bold">Healthcare Monitor</h1>
                <p className="text-purple-200 text-sm">Patient Flow Dashboard</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <div className="bg-white/20 px-4 py-2 rounded-lg text-white flex items-center">
                <Users className="w-4 h-4 mr-2" />
                <span>267 Active Patients</span>
              </div>
              <div className="bg-white/20 px-4 py-2 rounded-lg text-white flex items-center">
                <Clock className="w-4 h-4 mr-2" />
                <span>{currentTime}</span>
              </div>
              <span className="text-white flex items-center">
                <User className="w-4 h-4 mr-2" />
                {username}
              </span>
              <button
                onClick={onLogout}
                className="bg-white/20 hover:bg-white/30 text-white px-4 py-2 rounded-lg transition duration-200 flex items-center"
              >
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Dashboard Navigation */}
      <div className="bg-white shadow-md">
        <div className="container mx-auto px-4">
          <div className="flex space-x-1 py-3 overflow-x-auto">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `px-4 py-2 rounded-lg transition duration-200 flex items-center whitespace-nowrap ${
                    isActive
                      ? 'bg-purple-600 text-white'
                      : 'text-gray-600 hover:text-purple-600 hover:bg-purple-50'
                  }`
                }
              >
                <item.icon className="w-4 h-4 mr-2" />
                {item.label}
              </NavLink>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
