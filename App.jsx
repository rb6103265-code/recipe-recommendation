import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { useState } from "react";
import LoginPage from "./pages/LoginPage";
import Dashboard from "./pages/Dashboard";
import "./App.css";

export default function App() {
  const [token, setToken] = useState(localStorage.getItem("token"));

  function handleLogin(newToken) {
    setToken(newToken);
    localStorage.setItem("token", newToken);
  }

  function handleLogout() {
    setToken(null);
    localStorage.removeItem("token");
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            token ? (
              <Dashboard token={token} onLogout={handleLogout} />
            ) : (
              <LoginPage onLogin={handleLogin} />
            )
          }
        />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  );
}
