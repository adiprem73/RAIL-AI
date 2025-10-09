import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import DataLoader from './pages/DataLoader';
import Planner from './pages/Planner';
import PlanResults from './pages/PlanResults';
import Settings from './pages/Settings';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/data" element={<DataLoader />} />
          <Route path="/planner" element={<Planner />} />
          <Route path="/plans/:planId" element={<PlanResults />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
