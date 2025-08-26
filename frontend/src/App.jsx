import React, { useState } from 'react'
import './App.css'

function App() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState([
    { text: 'Hello! How can I help you today?', sender: 'bot' }
  ])

  const handleSend = async () => {
    if (input.trim()) {
      const userMessage = { text: input, sender: 'user' }
      setMessages(prev => [...prev, userMessage])

      const response = await fetch('http://localhost:5000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input })
      })
      const data = await response.json()
      const botMessage = { text: data.reply, sender: 'bot' }
      setMessages(prev => [...prev, botMessage])
      setInput('')
    }
  }

  return (
    <div className="App">
      <div className="chat-window">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            {msg.text}
          </div>
        ))}
      </div>
      <div className="chat-input">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Type a message..."
        />
        <button onClick={handleSend}>Send</button>
      </div>
    </div>
  )
}

export default App
