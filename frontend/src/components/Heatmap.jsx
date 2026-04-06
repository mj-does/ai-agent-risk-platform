import React from 'react'
import { riskColor } from '../data'

const TOOLS = ['GitHub API','Terraform','GitHub Actions','Kubernetes','AWS CLI']
const ACTIONS = ['read_logs','list_prs','scale','delete_db','run_script','create_repo']
const VALS = {
  'GitHub API':     [0.18,0.09,0,0,0,0.3],
  'Terraform':      [0,0,0.6,0.95,0.7,0],
  'GitHub Actions': [0.2,0,0,0,0.87,0.4],
  'Kubernetes':     [0.2,0,0.65,0.8,0.7,0],
  'AWS CLI':        [0.15,0,0.5,0.9,0.75,0.3],
}

function Heatmap() {
  const cw=76, rh=32, ox=108, oy=50
  return (
    <svg width="100%" viewBox="0 0 580 240" style={{ display:'block' }}>
      {ACTIONS.map((a,j) => (
        <text key={a} x={ox+j*cw+38} y={oy-8} textAnchor="middle" fontSize="10" fill="#9c9a92">{a.replace('_',' ')}</text>
      ))}
      {TOOLS.map((t,i) => (
        <g key={t}>
          <text x={ox-6} y={oy+i*rh+16} textAnchor="end" dominantBaseline="central" fontSize="11" fill="#1a1a18">{t}</text>
          {VALS[t].map((v,j) => {
            const c = v===0?'#B4B2A9':riskColor(v)
            const alpha = v===0?0.12:Math.max(0.18,v*0.85)
            return (
              <g key={j}>
                <rect x={ox+j*cw+2} y={oy+i*rh+2} width={cw-4} height={rh-4} rx="5" fill={c} opacity={alpha}/>
                {v>0 && <text x={ox+j*cw+38} y={oy+i*rh+16} textAnchor="middle" dominantBaseline="central" fontSize="10" fontWeight="500" fill={c}>{Math.round(v*100)}%</text>}
              </g>
            )
          })}
        </g>
      ))}
    </svg>
  )
}

export default Heatmap
