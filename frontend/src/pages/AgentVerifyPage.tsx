import { useParams } from 'react-router-dom'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Paper from '@mui/material/Paper'
import Chip from '@mui/material/Chip'
import Button from '@mui/material/Button'
import Divider from '@mui/material/Divider'
import Tooltip from '@mui/material/Tooltip'
import OpenInNewIcon from '@mui/icons-material/OpenInNew'
import VerifiedIcon from '@mui/icons-material/Verified'
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline'
import GppBadOutlinedIcon from '@mui/icons-material/GppBadOutlined'
import { useQuery } from '@tanstack/react-query'
import { verifyAgent } from '@/services/agentshieldService'
import TpiGauge from '@/components/agentshield/TpiGauge'
import { MONAD_EXPLORER } from '@/lib/monad'

const OWASP_COLORS: Record<string, string> = {
  LLM01: '#ef4444',
  LLM02: '#f59e0b',
  LLM06: '#8b5cf6',
}

export default function AgentVerifyPage() {
  const { agentId } = useParams<{ agentId: string }>()

  const { data, isLoading } = useQuery({
    queryKey: ['agentshield', 'verify', agentId],
    queryFn: () => verifyAgent(agentId!),
    enabled: !!agentId,
  })

  if (isLoading) {
    return <Typography sx={{ p: 3, color: 'text.secondary' }}>Verifying agent…</Typography>
  }

  const owaspEntries = Object.entries(data?.owasp_breakdown ?? {})

  return (
    <Box sx={{ maxWidth: 620, mx: 'auto' }}>
      <Paper variant="outlined" sx={{ p: 4, borderRadius: '16px', textAlign: 'center' }}>
        <Box sx={{ mb: 2 }}>
          {data?.kill_switch_active ? (
            <GppBadOutlinedIcon sx={{ fontSize: 56, color: '#ef4444' }} />
          ) : data?.is_certified ? (
            <VerifiedIcon sx={{ fontSize: 56, color: '#22c55e' }} />
          ) : (
            <ErrorOutlineIcon sx={{ fontSize: 56, color: data?.is_verified ? '#f59e0b' : '#ef4444' }} />
          )}
        </Box>

        <Typography sx={{ fontWeight: 700, fontSize: '1.3rem', mb: 0.5 }}>
          {agentId}
        </Typography>
        <Typography color="text.secondary" sx={{ fontSize: '0.85rem', mb: 0.75 }}>
          AgentShield Security Attestation · Monad Testnet · OWASP LLM Top 10
        </Typography>

        {data?.kill_switch_active && (
          <Chip
            icon={<GppBadOutlinedIcon sx={{ fontSize: 14 }} />}
            label="Kill Switch Active — Agent Suspended"
            sx={{ bgcolor: '#ef444420', color: '#ef4444', fontWeight: 600, mb: 2 }}
          />
        )}

        {data?.tpi_score != null && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
            <TpiGauge score={data.tpi_score} size={160} />
          </Box>
        )}

        {!data?.is_verified && !data?.kill_switch_active && (
          <Chip label="Not Verified" sx={{ bgcolor: '#ef444420', color: '#ef4444' }} />
        )}

        {/* OWASP breakdown */}
        {owaspEntries.length > 0 && (
          <Box sx={{ mt: 2, mb: 1, textAlign: 'left' }}>
            <Typography sx={{ fontSize: '0.78rem', fontWeight: 600, mb: 1 }}>OWASP LLM Category Breakdown</Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.75 }}>
              {owaspEntries.map(([cat, val]: [string, any]) => {
                const color = OWASP_COLORS[cat] ?? '#6b7280'
                const score = val.total > 0 ? Math.round((val.passed / val.total) * 100) : 0
                return (
                  <Box key={cat} sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                    <Chip
                      label={cat}
                      size="small"
                      sx={{ fontSize: '0.6rem', height: 16, bgcolor: `${color}20`, color, border: `1px solid ${color}40`, minWidth: 42 }}
                    />
                    <Typography sx={{ fontSize: '0.75rem', flex: 1, color: 'text.secondary' }}>{val.label}</Typography>
                    <Tooltip title={`${val.passed}/${val.total} tests passed`}>
                      <Typography sx={{ fontSize: '0.72rem', fontWeight: 600, color: score === 100 ? '#22c55e' : score > 0 ? '#f59e0b' : '#ef4444' }}>
                        {score}%
                      </Typography>
                    </Tooltip>
                  </Box>
                )
              })}
            </Box>
          </Box>
        )}

        {data?.is_verified && (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.25, mt: 2, textAlign: 'left' }}>
            <Divider />
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <Typography sx={{ color: 'text.secondary', fontSize: '0.8rem', flexShrink: 0 }}>Result Hash</Typography>
              <Typography sx={{ fontFamily: 'monospace', fontSize: '0.68rem', wordBreak: 'break-all', textAlign: 'right', maxWidth: '58%', color: 'text.secondary' }}>
                {data.result_hash}
              </Typography>
            </Box>
            {data.tx_hash && (
              <>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography sx={{ color: 'text.secondary', fontSize: '0.8rem' }}>On-Chain TX</Typography>
                  <Button
                    size="small"
                    endIcon={<OpenInNewIcon sx={{ fontSize: 12 }} />}
                    onClick={() => window.open(`${MONAD_EXPLORER}/tx/${data.tx_hash}`, '_blank')}
                    sx={{ fontSize: '0.72rem', textTransform: 'none' }}
                  >
                    {data.tx_hash.slice(0, 10)}…{data.tx_hash.slice(-6)}
                  </Button>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography sx={{ color: 'text.secondary', fontSize: '0.8rem' }}>Attested</Typography>
                  <Typography sx={{ fontSize: '0.8rem' }}>
                    {data.timestamp ? new Date(data.timestamp).toLocaleString() : '—'}
                  </Typography>
                </Box>
              </>
            )}
          </Box>
        )}
      </Paper>
    </Box>
  )
}
