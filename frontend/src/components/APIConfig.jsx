import React, { useState } from 'react'
import { setAPI } from '../data'

function APIConfig({ onClose, onSave }) {
  const [endpoints, setEndpoints] = useState({ analyze:'', execute:'', graph:'', log:'' })
  const fields = [
    { key:'analyze', label:'Person 1 — POST /analyze_prompt', placeholder:'http://localhost:8001/analyze_prompt' },
    { key:'execute', label:'Person 3 — POST /should_execute', placeholder:'http://localhost:8003/should_execute' },
    { key:'graph',   label:'Person 3 — GET /graph_status',   placeholder:'http://localhost:8003/graph_status' },
    { key:'log',     label:'Person 2 — POST /log_event',     placeholder:'http://localhost:8002/log_event' },
  ]
  const handleSave = () => { setAPI(endpoints); onSave(endpoints) }
  return (
    <div style={{ position:'fixed', inset:0, background:'rgba(0,0,0,0.3)', zIndex:200, display:'flex', alignItems:'center', justifyContent:'center' }} onClick={onClose}>
      <div style={{ background:'#fff', borderRadius:12, padding:24, width:380, border:'0.5px solid rgba(0,0,0,0.15)' }} onClick={e=>e.stopPropagation()}>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16 }}>
          <span style={{ fontWeight:600, fontSize:14 }}>API endpoints</span>
          <button onClick={onClose} style={{ background:'none', border:'none', cursor:'pointer', fontSize:18, color:'#9c9a92' }}>×</button>
        </div>
        <p style={{ fontSize:12, color:'#5f5e5a', marginBottom:16 }}>Connect to your teammates' real APIs. Leave blank to use mock data.</p>
        {fields.map(f => (
          <div key={f.key} style={{ marginBottom:12 }}>
            <label style={{ fontSize:11, color:'#5f5e5a', display:'block', marginBottom:4 }}>{f.label}</label>
            <input value={endpoints[f.key]} placeholder={f.placeholder}
              onChange={e=>setEndpoints(prev=>({...prev,[f.key]:e.target.value}))}
              style={{ width:'100%', padding:'7px 10px', border:'0.5px solid rgba(0,0,0,0.18)', borderRadius:8, background:'#f5f5f4', fontSize:12, outline:'none' }}/>
          </div>
        ))}
        <button onClick={handleSave} style={{ width:'100%', padding:'8px 0', marginTop:8, background:'#1a1a18', color:'#fff', border:'none', borderRadius:8, cursor:'pointer', fontSize:13, fontWeight:500 }}>Save & connect</button>
      </div>
    </div>
  )
}

export default APIConfig
