import Chip from '@mui/material/Chip'

interface TpiScoreBadgeProps {
  score: number
  size?: 'small' | 'medium'
}

export default function TpiScoreBadge({ score, size = 'small' }: TpiScoreBadgeProps) {
  const color = score >= 80 ? '#22c55e' : score >= 50 ? '#f59e0b' : '#ef4444'
  const label = `${score}/100`

  return (
    <Chip
      label={label}
      size={size}
      sx={{
        bgcolor: `${color}20`,
        color,
        fontWeight: 700,
        fontSize: '0.75rem',
        border: `1px solid ${color}40`,
      }}
    />
  )
}
