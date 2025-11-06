import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import RootLayout from './layouts/RootLayout';
import Home from './pages/Home';
import UploadAssessment from './pages/UploadAssessment';
import AssessmentsList from './pages/AssessmentsList';
import AssessmentDetail from './pages/AssessmentDetail';
import MarkAnswers from './pages/MarkAnswers';
import Reports from './pages/Reports';
import ReportDetail from './pages/ReportDetail';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<RootLayout />}>
          <Route index element={<Home />} />
          <Route path="upload-assessment" element={<UploadAssessment />} />
          <Route path="assessments" element={<AssessmentsList />} />
          <Route path="assessments/:id" element={<AssessmentDetail />} />
          <Route path="mark-answers" element={<MarkAnswers />} />
          <Route path="reports" element={<Reports />} />
          <Route path="reports/:id" element={<ReportDetail />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
