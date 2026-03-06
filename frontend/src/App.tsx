import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Title, Text, Container } from '@mantine/core';

import { Login } from './modules/auth/Login';
import { Register } from './modules/auth/Register';
import { ForgotPassword } from './modules/auth/ForgotPassword';
import { ResetPassword } from './modules/auth/ResetPassword';
import { HealthPlanList } from './modules/health_plans/HealthPlanList';
import { HealthPlanDetail } from './modules/health_plans/HealthPlanDetail';
import { SOPDetail } from './modules/knowledge_base/SOPDetail';
import { useAuthStore } from './store/authStore';

// Protected Route Wrapper
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = useAuthStore((state) => state.token);
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

// Placeholder components
const Dashboard = () => (
  <Container>
    <Title order={2}>Dashboard</Title>
    <Text mt="md">Bem-vindo ao MediCore. Selecione uma opção no menu lateral.</Text>
  </Container>
);

const Onboarding = () => (
  <Container>
    <Title order={2}>Onboarding & Trilhas</Title>
    <Text mt="md">Gerencie e visualize seu progresso de treinamento.</Text>
  </Container>
);

const Chat = () => (
  <Container>
    <Title order={2}>Chat de Suporte</Title>
    <Text mt="md">Comunicação em tempo real com a gestão.</Text>
  </Container>
);

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        {/* Protected Routes */}
        <Route path="/" element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }>
          <Route index element={<Dashboard />} />
          <Route path="health-plans" element={<HealthPlanList />} />
          <Route path="health-plans/:id" element={<HealthPlanDetail />} />
          <Route path="sops/:id" element={<SOPDetail />} />
          <Route path="onboarding" element={<Onboarding />} />
          <Route path="chat" element={<Chat />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
