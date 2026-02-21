import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "sonner";
import { useAuth } from "@/hooks/useAuth";
import { LoginPage } from "@/pages/Login";
import { AdminLayout } from "@/pages/admin/Layout";
import { CreateTraining } from "@/pages/admin/CreateTraining";
import { Students } from "@/pages/admin/Students";
import { StudentDetail } from "@/pages/admin/StudentDetail";
import { EgeConverting } from "@/pages/admin/EgeConverting";
import { PoolPage } from "@/pages/admin/Pool";
import { AddQuestion } from "@/pages/admin/AddQuestion";
import { StudentViewStats } from "@/pages/student/ViewStats";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-[var(--color-muted-foreground)]">Загрузка...</div>
      </div>
    );
  }
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Toaster richColors position="top-right" />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/student/view-stats" element={<StudentViewStats />} />
        <Route
          path="/admin"
          element={
            <RequireAuth>
              <AdminLayout />
            </RequireAuth>
          }
        >
          <Route index element={<Navigate to="/admin/create-training" replace />} />
          <Route path="create-training" element={<CreateTraining />} />
          <Route path="students" element={<Students />} />
          <Route path="students/:telegramId" element={<StudentDetail />} />
          <Route path="ege-converting" element={<EgeConverting />} />
          <Route path="pool" element={<PoolPage />} />
          <Route path="add-question" element={<AddQuestion />} />
        </Route>
        <Route path="*" element={<Navigate to="/admin" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
