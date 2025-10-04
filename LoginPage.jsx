import { useState } from "react";
import axios from "axios";
import "./LoginPage.css";

export default function LoginPage({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const API = "http://127.0.0.1:5000";

  async function register() {
    try {
      const res = await axios.post(`${API}/register`, { name, email, password });
      alert(res.data.msg || "Registered");
      setMode("login");
    } catch (err) {
      alert(err.response?.data?.msg || "Register failed");
    }
  }

  async function login() {
    try {
      const res = await axios.post(`${API}/login`, { email, password });
      onLogin(res.data.access_token);
      alert("Logged in!");
    } catch (err) {
      alert(err.response?.data?.msg || "Login failed");
    }
  }

  return (
    <div className="login-container">
      <h1>🍴 Recipe Recommender</h1>
      <div className="auth">
        <div className="tabs">
          <button className={mode==="login" ? "active":""} onClick={()=>setMode("login")}>Login</button>
          <button className={mode==="register" ? "active":""} onClick={()=>setMode("register")}>Register</button>
        </div>

        {mode === "register" && (
          <input placeholder="Name" value={name} onChange={e=>setName(e.target.value)} />
        )}

        <input placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} />
        <input type="password" placeholder="Password" value={password} onChange={e=>setPassword(e.target.value)} />

        {mode === "register" ? (
          <button onClick={register} className="primary">Register</button>
        ) : (
          <button onClick={login} className="primary">Login</button>
        )}
      </div>
    </div>
  );
}
