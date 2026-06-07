import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'

const TPI_COLORS = {
  certified: '#22c55e',
  warning: '#f59e0b',
  failed: '#ef4444',
}

function getTpiColor(score: number) {
  if (score >= 80) return TPI_COLORS.certified
  if (score >= 50) return TPI_COLORS.warning
  return TPI_COLORS.failed
}

function getTpiLabel(score: number) {
  if (score >= 80) return 'Certified'
  if (score >= 50) return 'Warning'
  return 'Failed'
}

interface TpiGaugeProps {
  score: number
  size?: number
}

export default function TpiGauge({ score, size = 120 }: TpiGaugeProps) {
  const color = getTpiColor(score)
  const label = getTpiLabel(score)
  const radius = (size - 12) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 0.5 }}>
      <Box sx={{ position: 'relative', width: size, height: size }}>
        <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
          <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="#e5e7eb" strokeWidth={10} />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={10}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
            style={{ transition: 'stroke-dashoffset 1s ease' }}
          />
        </svg>
        <Box
          sx={{
            position: 'absolute',
            inset: 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Typography sx={{ fontWeight: 700, fontSize: size * 0.22, color, lineHeight: 1 }}>
            {score}
          </Typography>
          <Typography sx={{ fontSize: size * 0.1, color: 'text.secondary' }}>TPI</Typography>
        </Box>
      </Box>
      <Typography sx={{ fontWeight: 600, fontSize: '0.8rem', color }}>
        {label}
      </Typography>
    </Box>
  )
}
