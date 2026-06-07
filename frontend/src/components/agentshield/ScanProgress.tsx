import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import LinearProgress from '@mui/material/LinearProgress'
import Alert from '@mui/material/Alert'
import Chip from '@mui/material/Chip'
import Tooltip from '@mui/material/Tooltip'
import GppBadOutlinedIcon from '@mui/icons-material/GppBadOutlined'
import TestResultCard from './TestResultCard'
import TpiGauge from './TpiGauge'
import type { ScanResponse } from '@/services/agentshieldService'

const OWASP_COLORS: Record<string, string> = {
  LLM01: '#ef4444',
  LLM02: '#f59e0b',
  LLM06: '#8b5cf6',
}

interface ScanProgressProps {
  scanResult: ScanResponse
  isLoading: boolean
}

export default function ScanProgress({ scanResult, isLoading }: ScanProgressProps) {
  const owaspEntries = Object.entries(scanResult.owasp_breakdown ?? {})

  return (
    <Box>
      {isLoading && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            Running OWASP adversarial tests…
          </Typography>
          <LinearProgress sx={{ borderRadius: 4 }} />
        </Box>
      )}

      {!isLoading && scanResult.kill_switch_triggered && (
        <Alert
          icon={<GppBadOutlinedIcon fontSize="small" />}
          severity="error"
          sx={{ mb: 2, fontSize: '0.8rem' }}
        >
          Kill switch triggered — TPI below 50. Agent should be suspended from the Monad economy.
        </Alert>
      )}

      {!isLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
          <TpiGauge score={scanResult.tpi_score} size={140} />
        </Box>
      )}

      {/* OWASP breakdown */}
      {!isLoading && owaspEntries.length > 0 && (
        <Box sx={{ display: 'flex', gap: 0.75, flexWrap: 'wrap', mb: 2 }}>
          {owaspEntries.map(([cat, val]: [string, any]) => {
            const color = OWASP_COLORS[cat] ?? '#6b7280'
            const pct = val.total > 0 ? Math.round((val.passed / val.total) * 100) : 0
            return (
              <Tooltip key={cat} title={`${val.label}: ${val.passed}/${val.total} tests passed (weight ${val.weight}%)`}>
                <Chip
                  label={`${cat} ${pct}%`}
                  size="small"
                  sx={{
                    fontSize: '0.65rem',
                    height: 20,
                    bgcolor: `${color}20`,
                    color,
                    border: `1px solid ${color}40`,
                    cursor: 'default',
                  }}
                />
              </Tooltip>
            )
          })}
        </Box>
      )}

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        {scanResult.test_results.map((result, i) => (
          <TestResultCard key={i} result={result} index={i} />
        ))}
      </Box>

      {!isLoading && (
        <Box sx={{ mt: 2, p: 1.5, bgcolor: 'action.hover', borderRadius: '8px' }}>
          <Typography sx={{ fontSize: '0.68rem', color: 'text.secondary', fontFamily: 'monospace', wordBreak: 'break-all' }}>
            SHA-256 result hash (tamper-proof): {scanResult.result_hash}
          </Typography>
        </Box>
      )}
    </Box>
  )
}
