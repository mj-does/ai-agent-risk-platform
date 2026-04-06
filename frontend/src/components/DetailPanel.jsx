import React from 'react'
import { riskColor, riskLabel, propagated } from '../data'

function Bar({ value }) {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:6, marginTop:4 }}>
      <div style={{ flex:1, height:5, background:'#f4f4f2', borderRadius:3, overflow:'hidden' }}>
        <div style={{ height:'100%', borderRadius:3, width:`${Math.round(value*100)}%`, background:riskColor(value), transition:'width 0.5s' }}/>
      </div>
      <span style={{ fontSize:11, color:'#9c9a92', minWidth:28 }}>{Math.round(value*100)}%</span>
    </div>
  )
}

function DetailPanel({ prompt: p }) {
  if (!p) return <div style={{ padding:16, color:'#9c9a92', fontSize:12 }}>Select a prompt</div>
  const pr = propagated(p)
  const chain = [
    { icon:'💬', name:'Prompt', sub:p.text.slice(0,40)+'…', w:p.risk },
    { icon:'🤖', name:p.agent, sub:'Interprets intent', w:p.aw },
    { icon:'🔧', name:p.tool, sub:'Tool selected', w:p.tw },
    { icon:'⚡', name:p.action.replace(/_/g,' '), sub:'Action type', w:p.acw },
    { icon:'🗄️', name:p.system, sub:'Target system', w:p.sw },
  ]
  const bannerStyle = p.status==='blocked' ? { background:'#FCEBEB', border:'0.5px solid #F7C1C1' }
    : p.status==='allowed' ? { background:'#EAF3DE', border:'0.5px solid #C0DD97' }
    : { background:'#FAEEDA', border:'0.5px solid #FAC775' }
  const bannerIcon = p.status==='blocked'?'🛑':p.status==='allowed'?'✅':'⚠️'
  const bannerTitle = p.status==='blocked'?'Execution blocked':p.status==='allowed'?'Execution allowed':'Awaiting approval'
  return (
    <div style={{ background:'#fff', borderLeft:'0.5px solid rgba(0,0,0,0.1)', overflowY:'auto', padding:16 }}>
      <div style={{ fontSize:13, fontWeight:500, marginBottom:12 }}>Prompt detail</div>
      <div style={{ ...bannerStyle, borderRadius:8, padding:'11px 13px', marginBottom:12, display:'flex', alignItems:'flex-start', gap:9 }}>
        <span style={{ fontSize:16 }}>{bannerIcon}</span>
        <div>
          <div style={{ fontSize:12, fontWeight:600 }}>{bannerTitle}</div>
          <div style={{ fontSize:11, color:'#5f5e5a' }}>Propagated risk: {pr.toFixed(2)}</div>
        </div>
      </div>
      <div style={{ marginBottom:12 }}>
        <div style={{ fontSize:11, color:'#5f5e5a', marginBottom:3 }}>Intent</div>
        <div style={{ fontSize:12, fontWeight:500 }}>{p.intent}</div>
      </div>
      <div style={{ marginBottom:14 }}>
        <div style={{ fontSize:11, color:'#5f5e5a', marginBottom:6 }}>Propagated risk</div>
        <div style={{ display:'flex', justifyContent:'space-between', fontSize:11, marginBottom:4 }}>
          <span>{riskLabel(pr)}</span>
          <span style={{ fontWeight:600, color:riskColor(pr) }}>{Math.round(pr*100)}%</span>
        </div>
        <div style={{ height:7, background:'#f4f4f2', borderRadius:3, overflow:'hidden' }}>
          <div style={{ height:'100%', borderRadius:3, width:`${Math.round(pr*100)}%`, background:riskColor(pr) }}/>
        </div>
      </div>
      <div style={{ fontSize:11, fontWeight:500, color:'#5f5e5a', marginBottom:8 }}>Execution chain</div>
      {chain.map((c,i) => (
        <div key={i} style={{ display:'flex', alignItems:'flex-start', gap:10, padding:'9px 0', borderBottom: i<chain.length-1?'0.5px solid rgba(0,0,0,0.08)':'none' }}>
          <div style={{ width:28, height:28, borderRadius:6, background:'#f4f4f2', display:'flex', alignItems:'center', justifyContent:'center', fontSize:13, flexShrink:0 }}>{c.icon}</div>
          <div style={{ flex:1 }}>
            <div style={{ fontSize:12, fontWeight:500 }}>{c.name}</div>
            <div style={{ fontSize:11, color:'#5f5e5a' }}>{c.sub}</div>
            <Bar value={c.w}/>
          </div>
        </div>
      ))}
      <div style={{ marginTop:12, padding:10, background:'#f4f4f2', borderRadius:8, fontSize:11 }}>
        <div style={{ color:'#5f5e5a', marginBottom:3 }}>Propagation formula</div>
        <div style={{ fontSize:10, color:'#9c9a92' }}>{p.risk} × {p.aw} × {p.tw} × {p.acw} × {p.sw} = <strong style={{ color:riskColor(pr) }}>{pr.toFixed(2)}</strong></div>
      </div>
    </div>
  )
}

export default DetailPanel
