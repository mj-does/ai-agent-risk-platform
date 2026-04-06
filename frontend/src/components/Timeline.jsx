import React from 'react'
import { riskColor } from '../data'

function Timeline({ prompts }) {
  return (
    <svg width="100%" viewBox="0 0 580 260" style={{ display:'block' }}>
      <line x1="28" y1="20" x2="28" y2="240" stroke="#D3D1C7" strokeWidth="0.5"/>
      {prompts.map((p,i) => {
        const y = 34 + i*42
        const c = riskColor(p.risk)
        return (
          <g key={p.id}>
            <circle cx="28" cy={y} r="5" fill={c}/>
            <line x1="33" y1={y} x2="55" y2={y} stroke={c} strokeWidth="0.5"/>
            <text x="60" y={y} dominantBaseline="central" fontSize="11" fill="#1a1a18">{p.text.slice(0,48)}…</text>
            <text x="490" y={y} dominantBaseline="central" fontSize="10" fill="#9c9a92">{p.time}</text>
            <text x="570" y={y} textAnchor="end" dominantBaseline="central" fontSize="10" fill={c} fontWeight="500">{p.status.toUpperCase()}</text>
          </g>
        )
      })}
    </svg>
  )
}

export default Timeline
