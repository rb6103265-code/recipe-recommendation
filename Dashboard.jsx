import { useState } from "react";
import axios from "axios";
import "./Dashboard.css";

export default function Dashboard({ token, onLogout }) {
  const [location, setLocation] = useState("");
  const [weather, setWeather] = useState(null);
  const [recipes, setRecipes] = useState([]);

  const API = "http://127.0.0.1:5000";

  async function getRecommendations() {
    try {
      const res = await axios.get(`${API}/recipes/recommend`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { location: location || "Delhi" },
      });
      setWeather(res.data.weather);
      setRecipes(res.data.recommendations);
    } catch (err) {
      alert(err.response?.data?.msg || "Error fetching recommendations");
    }
  }

  return (
    <div className="dashboard-container">
      <header>
        <h1>🍴 Recipe Recommender</h1>
        <button className="logout" onClick={onLogout}>Logout</button>
      </header>

      <div className="card">
        <h2>Get Recommendations</h2>
        <input
          placeholder="City (e.g. London)"
          value={location}
          onChange={(e)=>setLocation(e.target.value)}
        />
        <button onClick={getRecommendations} className="primary">Get Recipes</button>

        {weather && (
          <div className="weather">
            <strong>Weather ({weather.location})</strong>
            <div className="weather-info">
              <img src={`https://openweathermap.org/img/wn/${weather.icon || "01d"}@2x.png`} alt="weather" />
              <div>
                <div>Condition: {weather.condition}</div>
                <div>Temp: {weather.temp ?? "N/A"} °C</div>
              </div>
            </div>
          </div>
        )}

        <div className="recipes">
          {recipes.map((r) => (
            <div className="recipe-card" key={r.id}>
              <h3>{r.title}</h3>
              <div>Prep: {r.prep_time_minutes ?? r.prep_time} min</div>
              <div>Tags: {Array.isArray(r.tags) ? r.tags.join(", ") : String(r.tags)}</div>
            </div>
          ))}
          {recipes.length === 0 && <p>No recommendations yet.</p>}
        </div>
      </div>
    </div>
  );
}
