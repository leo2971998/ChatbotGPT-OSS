import React, { useState } from 'react'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'

export default function App() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([
    { id: 0, type: 'text', text: 'Hello! Ask me for weather (e.g., "weather in Houston").', sender: 'bot' }
  ])
  const [loading, setLoading] = useState(false)

  const handleSend = async () => {
    const text = input.trim()
    if (!text || loading) return
    setInput('')

    setMessages(prev => [...prev, { id: Date.now(), type: 'text', text, sender: 'user' }])
    setLoading(true)
    try {
      const res = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.error || 'Request failed')

      if (data.reply) {
        setMessages(prev => [...prev, { id: Date.now() + 1, type: 'text', text: data.reply, sender: 'bot' }])
      }
      if (data.ui?.type === 'weather') {
        setMessages(prev => [...prev, { id: Date.now() + 2, type: 'card', sender: 'bot', card: data.ui }])
      }
    } catch (e) {
      setMessages(prev => [...prev, { id: Date.now() + 3, type: 'text', text: '⚠️ ' + e.message, sender: 'bot' }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="App">
      <div className="chat-window">
        {messages.map(msg =>
          msg.type === 'card' ? (
            <WeatherCard key={msg.id} data={msg.card} />
          ) : (
            <div key={msg.id} className={`message ${msg.sender}`}>
              {msg.text}
            </div>
          )
        )}
        {loading && <div className="message bot">…</div>}
      </div>
      <div className="chat-input">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyPress={e => e.key === 'Enter' && handleSend()}
          placeholder="Type a message..."
        />
        <button onClick={handleSend} disabled={loading}>Send</button>
      </div>
    </div>
  )
}

function WeatherCard({ data }) {
  const { location, icon, condition, temperature, feelsLike, high, low, humidity, wind, uv } = data || {}
  return (
    <div className="weather-card">
      <div className="wc-left">
        <div className="wc-icon">{icon || '🌡️'}</div>
        <div>
          <div className="wc-location">{location}</div>
          <div className="wc-cond">{condition}</div>
        </div>
      </div>
      <div className="wc-main">
        <div className="wc-temp">{Math.round(temperature)}°</div>
        <div className="wc-feels">Feels {Math.round(feelsLike)}°</div>
      </div>
      <div className="wc-right">
        <div>H:{Math.round(high)}° / L:{Math.round(low)}°</div>
        <div>Humidity: {Math.round(humidity)}%</div>
        <div>Wind: {Math.round(wind)} km/h</div>
        <div>UV: {uv ?? '—'}</div>
        <Legend />
      </div>
    </div>
  )
}

function Legend() {
  return (
    <div className="legend">
      <span className="chip good">Good</span>
      <span className="chip fair">Fair</span>
      <span className="chip poor">Poor</span>
    </div>
  )
}

