import { Routes, Route, Navigate } from 'react-router-dom'
import { useSelector } from 'react-redux'
import { RootState } from './store'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'
import ReviewDetail from './pages/ReviewDetail'
import ReviewList from './pages/ReviewList'
import HowItWorks from './pages/HowItWorks'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { token } = useSelector((state: RootState) => state.auth)
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="upload" element={<Upload />} />
        <Route path="reviews" element={<ReviewList />} />
        <Route path="reviews/:reviewId" element={<ReviewDetail />} />
        <Route path="how-it-works" element={<HowItWorks />} />
      </Route>
    </Routes>
  )
}

export default App
