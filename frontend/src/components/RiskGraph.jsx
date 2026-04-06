import React from 'react'
import { riskColor, propagated } from '../data'

function RiskGraph({ prompt: p }) {
  if (!p) return null
  const pr = propagated(p)
  const blocked = p.status === 'blocked'
  const nodes = [
    { x: 30,  y: 110, label: 'Prompt',                       sub: Math.round(p.risk*100)+'%', c: riskColor(p.risk), icon: '💬' },
    { x: 160, y: 50,  label: p.agent.replace(' Agent',''),   sub: Math.round(p.aw*100)+'%',   c: riskColor(p.aw),   icon: '🤖' },
    { x: 295, y: 110, label: p.tool,                         sub: Math.round(p.tw*100)+'%',   c: riskColor(p.tw),   icon: '🔧' },
    { x: 420, y: 50,  label: p.action.replace(/_/g,' ').slice(0,13), sub: Math.round(p.acw*100)+'%', c: riskColor(p.acw), icon: '⚡' },
    { x: 530, y: 120, label: p.system.slice(0,12),           sub: Math.round(p.sw*100)+'%',   c: riskColor(p.sw),   icon: '🗄️' },
  ]
  const W = 100, H = 42
  const edges = [[0,1],[1,2],[2,3],[3,4]]
  const midX = (nodes[3].x + W + nodes[4].x) / 2
  const midY = (nodes[3].y + H/2 + nodes[4].y + H/2) / 2
  return (
    <svg width="100%" viewBox="0 0 660 300" style={{ display:'block' }}>
      <defs>
        <marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
          <path d="M2 1L8 5L2 9" fill="none" stroke="#B4B2A9" strokeWidth="1.5" strokeLinecap="round"/>
        </marker>
      </defs>
      {edges.map(([a,b]) => {
        const na=nodes[a], nb=nodes[b]
        return <line key={`${a}-${b}`} x1={na.x+W} y1={na.y+H/2} x2={nb.x} y2={nb.y+H/2} stroke="#B4B2A9" strokeWidth="1" strokeDasharray={blocked?'4 3':'none'} markerEnd="url(#arr)"/>
      })}
      {blocked && <>
        <circle cx={midX} cy={midY} r={12} fill="#FCEBEB" stroke="#F7C1C1" strokeWidth="0.5"/>
        <text x={midX} y={midY+5} textAnchor="middle" fontSize="13">🛑</text>
      </>}
      {nodes.map((n,i) => (
        <g key={i}>
          <rect x={n.x} y={n.y} width={W} height={H} rx="8" fill={n.c+'1a'} stroke={n.c} strokeWidth="1"/>
          <text x={n.x+13} y={n.y+13} fontSize="11">{n.icon}</text>
          <text x={n.x+W/2} y={n.y+15} textAnchor="middle" dominantBaseline="central" fontSize="11" fontWeight="500" fill={n.c}>{n.label}</text>
          <text x={n.x+W/2} y={n.y+30} textAnchor="middle" dominantBaseline="central" fontSize="10" fill={n.c} opacity="0.8">{n.sub}</text>
        </g>
      ))}
      <rect x="240" y="200" width="160" height="36" rx="8" fill={riskColor(pr)+'1a'} stroke={riskColor(pr)} strokeWidth="0.5"/>
      <text x="320" y="213" textAnchor="middle" dominantBaseline="central" fontSize="11" fontWeight="500" fill={riskColor(pr)}>Propagated: {pr.toFixed(2)}</text>
      <text x="320" y="229" textAnchor="middle" dominantBaseline="central" fontSize="10" fill={riskColor(pr)} opacity="0.85">→ {p.status==='blocked'?'BLOCKED':p.status==='approval'?'NEEDS APPROVAL':'ALLOWED'}</text>
    </svg>
  )
}

export default RiskGraph
