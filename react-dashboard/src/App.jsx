import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Layout from './components/Layout';
import Overview from './dashboards/Overview';
import Executive from './dashboards/Executive';
import Operations from './dashboards/Operations';
import Predictive from './dashboards/Predictive';
import Performance from './dashboards/Performance';
import PatientFlow from './dashboards/PatientFlow';
import RealTime from './dashboards/RealTime';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    const auth = sessionStorage.getItem('authenticated');
    if (auth === 'true') {
      setIsAuthenticated(true);
    }
  }, []);

  const handleLogin = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    sessionStorage.removeItem('authenticated');
    sessionStorage.removeItem('username');
    setIsAuthenticated(false);
  };

  return (
    <Router>
      <Routes>
        <Route 
          path="/login" 
          element={isAuthenticated ? <Navigate to="/" /> : <Login onLogin={handleLogin} />} 
        />
        <Route 
          path="/" 
          element={isAuthenticated ? <Layout onLogout={handleLogout} /> : <Navigate to="/login" />}
        >
          <Route index element={<Overview />} />
          <Route path="executive" element={<Executive />} />
          <Route path="operations" element={<Operations />} />
          <Route path="predictive" element={<Predictive />} />
          <Route path="performance" element={<Performance />} />
          <Route path="patientflow" element={<PatientFlow />} />
          <Route path="realtime" element={<RealTime />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
