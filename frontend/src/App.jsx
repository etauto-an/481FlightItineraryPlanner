import { useState, useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Popup } from 'react-leaflet';
import * as L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './App.css';

// Base URL for the backend API.
const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000';

function App() {
  const [start, setStart] = useState('LAX');
  const [targets, setTargets] = useState([]);
  const [selectedTarget, setSelectedTarget] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [airports, setAirports] = useState([]);

  const airportDict = useMemo(() => Object.fromEntries(airports.map(a => [a.code, a])), [airports]);

  useEffect(() => {
    async function loadAirports() {
      try {
        const res = await fetch('/airportList.json');
        if (!res.ok) throw new Error('Failed to load airports');
        const data = await res.json();
        setAirports(data);
      } catch (err) {
        setError(err.message || String(err));
      }
    }
    loadAirports();
  }, []);

  const addTarget = () => {
    if (selectedTarget && !targets.includes(selectedTarget) && selectedTarget !== start) {
      setTargets([...targets, selectedTarget]);
      setSelectedTarget('');
    }
  };

  const removeTarget = (code) => {
    setTargets(targets.filter(t => t !== code));
  };

  async function handleSubmit(e) {
    e.preventDefault();
    if (targets.length === 0) {
      setError('Please add at least one destination');
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);

    const body = {
      start: start.trim().toUpperCase(),
      targets: targets,
      max_iterations: 50000,
      time_limit: 5,
    };

    try {
      const res = await fetch(`${API_BASE}/itinerary`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || res.statusText);
      }
      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err.message || String(err));
    } finally {
      setLoading(false);
    }
  }

  const formatDuration = (seconds) => {
    if (!seconds) return 'N/A';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${h}h ${m}m`;
  };

  return (
    <div className="app">
      <header className="hero">
        <h1>Where to?</h1>
      </header>

      <main className="search-card">
        <form onSubmit={handleSubmit} className="search-form">
          <div className="fields" style={{ alignItems: 'flex-start' }}>
            <label style={{ flex: 1 }}>
              Start From:
              <select 
                value={start} 
                onChange={(e) => {
                  setStart(e.target.value);
                  if (targets.includes(e.target.value)) {
                    removeTarget(e.target.value);
                  }
                }}
                style={{ width: '100%', marginTop: '0.5rem' }}
              >
                <option value="LAX">Los Angeles (LAX)</option>
                <option value="LGB">Long Beach (LGB)</option>
                <option value="SNA">John&nbsp;Wayne (SNA)</option>
              </select>
            </label>

            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <label>
                Add Destinations:
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                  <select
                    value={selectedTarget}
                    onChange={(e) => setSelectedTarget(e.target.value)}
                    style={{ flex: 1 }}
                  >
                    <option value="">Select airport...</option>
                    {airports
                      .filter(a => a.code !== start && !targets.includes(a.code))
                      .sort((a, b) => a.city.localeCompare(b.city))
                      .map((airport) => (
                      <option key={airport.code} value={airport.code}>
                        {airport.city}, {airport.state} - {airport.name} ({airport.code})
                      </option>
                    ))}
                  </select>
                  <button 
                    type="button" 
                    onClick={addTarget}
                    disabled={!selectedTarget}
                    style={{ padding: '0 1rem', background: '#304CB2', color: 'white', border: 'none', borderRadius: '0.5rem', cursor: 'pointer', fontWeight: 'bold' }}
                  >
                    Add
                  </button>
                </div>
              </label>
              
              {targets.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {targets.map(t => (
                    <span key={t} style={{ background: '#e5e7eb', padding: '0.25rem 0.75rem', borderRadius: '999px', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem' }}>
                      {t}
                      <button 
                        type="button" 
                        onClick={() => removeTarget(t)}
                        style={{ border: 'none', background: 'none', cursor: 'pointer', fontWeight: 'bold', color: '#666', padding: 0 }}
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          <button type="submit" disabled={loading || targets.length === 0} className="search-btn">
            {loading ? 'Optimizing Route…' : 'Find Best Route'}
          </button>
        </form>

        {error && <div className="error">Error: {error}</div>}

        {result && (
          <div className="result">
            <h2>Itinerary</h2>
            
            {result.details && result.details.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', margin: '1.5rem 0' }}>
                {result.details.map((flight, i) => {
                   const origin = result.path[i];
                   const dest = result.path[i+1];
                   return (
                     <div key={i} style={{ 
                       border: '1px solid #e5e7eb', 
                       borderRadius: '8px', 
                       padding: '1rem', 
                       textAlign: 'left',
                       backgroundColor: '#f9fafb'
                     }}>
                       <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                          <span style={{ fontWeight: 'bold', fontSize: '1.1rem', color: '#1f2937' }}>
                            {origin} &rarr; {dest}
                          </span>
                          <span style={{ backgroundColor: '#dbeafe', color: '#1e40af', padding: '0.25rem 0.5rem', borderRadius: '9999px', fontSize: '0.875rem' }}>
                             {formatDuration(flight.flight_time)}
                          </span>
                       </div>
                       <div style={{ color: '#4b5563', fontSize: '0.95rem' }}>
                         <strong>Flight:</strong> {flight.flight}
                       </div>
                       <div style={{ color: '#6b7280', fontSize: '0.875rem', marginTop: '0.25rem' }}>
                         Aircraft: {flight.type} • Registration: {flight.reg} • Great Circle Distance: {flight.circle_distance} km
                       </div>
                     </div>
                   );
                })}
              </div>
            ) : (
              <p><strong>Path:</strong> {result.path.join(' → ')}</p>
            )}

            <div style={{ marginTop: '1rem', color: '#666', display: 'flex', gap: '2rem' }}>
              {result.details && (
                <span>
                  <strong>Total Flight Time:</strong>{' '}
                  {formatDuration(
                    result.total_flight_time || 
                    result.details.reduce((acc, item) => acc + (item.flight_time || 0), 0)
                  )}
                </span>
              )}
              <span>
                <strong>Total Distance:</strong> {result.cost.toFixed(1)} km
              </span>
            </div>

            {result.path.length > 1 && (
              <MapContainer
                bounds={result.path.reduce(
                  (bounds, code) => bounds.extend([airportDict[code].latitude_deg, airportDict[code].longitude_deg]), 
                  L.latLngBounds([[airportDict[result.path[0]].latitude_deg, airportDict[result.path[0]].longitude_deg]])
                )}
                boundsOptions={{ padding: [50, 50] }}
                style={{ height: '400px', width: '100%', marginTop: '1.5rem', borderRadius: '0.5rem' }}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                <Polyline
                  positions={result.path.map(code => [airportDict[code].latitude_deg, airportDict[code].longitude_deg])}
                  color="#304CB2"
                  weight={5}
                />
                {result.path.map(code => (
                  <Marker key={code} position={[airportDict[code].latitude_deg, airportDict[code].longitude_deg]}>
                    <Popup>{code} ({airportDict[code].country})</Popup>
                  </Marker>
                ))}
              </MapContainer>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default App;