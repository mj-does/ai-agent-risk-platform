import React from 'react'

function ActionLog({ logs }) {
  if (!logs.length) return <div style={{ fontSize:11, color:'#9c9a92' }}>No events yet — press Run demo or Simulate attack.</div>
  return (
    <div style={{ display:'flex', flexDirection:'column' }}>
      {[...logs].reverse().slice(0,6).map((l,i) => (
        <div key={i} style={{ display:'flex', alignItems:'center', gap:8, fontSize:11, padding:'5px 0', borderBottom:'0.5px solid rgba(0,0,0,0.07)' }}>
          <span>{l.blocked?'🛑':'✅'}</span>
          <span style={{ flex:1 }}>{l.text}</span>
          <span style={{ color:'#9c9a92' }}>{l.time}</span>
        </div>
      ))}
    </div>
  )
}

export default ActionLog
