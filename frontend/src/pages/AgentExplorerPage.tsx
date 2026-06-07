// ---------------------------------------------------------------------------
// AgentExplorerPage — Best-Agent Picker with kill switch controls
// Sorted by TPI score descending — highest-reputation agents first.
// ---------------------------------------------------------------------------

import { useState } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Paper from '@mui/material/Paper'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import Chip from '@mui/material/Chip'
import Button from '@mui/material/Button'
import IconButton from '@mui/material/IconButton'
import Tooltip from '@mui/material/Tooltip'
import Skeleton from '@mui/material/Skeleton'
import Alert from '@mui/material/Alert'
import OpenInNewIcon from '@mui/icons-material/OpenInNew'
import GppBadOutlinedIcon from '@mui/icons-material/GppBadOutlined'
import ShieldOutlinedIcon from '@mui/icons-material/ShieldOutlined'
import VerifiedIcon from '@mui/icons-material/Verified'
import EmojiEventsOutlinedIcon from '@mui/icons-material/EmojiEventsOutlined'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getAllAttestations, triggerKillSwitch } from '@/services/agentshieldService'
import type { VerifyRecord } from '@/services/agentshieldService'
import TpiScoreBadge from '@/components/agentshield/TpiScoreBadge'
import { MONAD_EXPLORER } from '@/lib/monad'

function OWASPBar({ breakdown }: { breakdown: Record<string, any> }) {
  const cats = Object.entries(breakdown)
  if (!cats.length) return null
  return (
    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
      {cats.map(([cat, val]) => (
        <Tooltip key={cat} title={`${val.label}: ${val.passed}/${val.total}`}>
          <Box
            sx={{
              width: 6,
              height: 6,
              borderRadius: '50%',
              bgcolor: val.passed === val.total ? '#22c55e' : val.passed > 0 ? '#f59e0b' : '#ef4444',
            }}
          />
        </Tooltip>
      ))}
    </Box>
  )
}

export default function AgentExplorerPage() {
  const queryClient = useQueryClient()
  const [killError, setKillError] = useState<string | null>(null)

  const { data: attestations = [], isLoading } = useQuery<VerifyRecord[]>({
    queryKey: ['agentshield', 'all'],
    queryFn: getAllAttestations,
    refetchInterval: 8_000,
  })

  const killMutation = useMutation({
    mutationFn: ({ agentId, activate }: { agentId: string; activate: boolean }) =>
      triggerKillSwitch(agentId, activate),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['agentshield', 'all'] })
      setKillError(null)
    },
    onError: () => setKillError('Kill switch failed — agent not found or DB error'),
  })

  const topAgent = attestations.find((a) => !a.kill_switch_active && a.tpi_score >= 80)

  return (
    <Box>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h5" sx={{ fontWeight: 700, letterSpacing: '-0.02em' }}>
            Agent Explorer
          </Typography>
          <Typography color="text.secondary" sx={{ fontSize: '0.875rem' }}>
            Reputation-sorted registry · query before hiring any agent on Monad
          </Typography>
        </Box>
        {topAgent && (
          <Chip
            icon={<EmojiEventsOutlinedIcon sx={{ fontSize: 14 }} />}
            label={`Best Agent: ${topAgent.agent_id} (TPI ${topAgent.tpi_score})`}
            sx={{ bgcolor: '#22c55e20', color: '#22c55e', fontWeight: 600, fontSize: '0.78rem' }}
          />
        )}
      </Box>

      {killError && (
        <Alert severity="error" onClose={() => setKillError(null)} sx={{ mb: 2 }}>
          {killError}
        </Alert>
      )}

      <TableContainer component={Paper} variant="outlined" sx={{ borderRadius: '12px' }}>
        <Table size="small">
          <TableHead>
            <TableRow sx={{ '& th': { fontWeight: 600, fontSize: '0.78rem', bgcolor: 'action.hover' } }}>
              <TableCell>#</TableCell>
              <TableCell>Agent ID</TableCell>
              <TableCell>Endpoint</TableCell>
              <TableCell>TPI Score</TableCell>
              <TableCell>OWASP</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Scanned</TableCell>
              <TableCell>On-Chain</TableCell>
              <TableCell>Kill Switch</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading &&
              Array.from({ length: 4 }).map((_, i) => (
                <TableRow key={i}>
                  {Array.from({ length: 9 }).map((__, j) => (
                    <TableCell key={j}><Skeleton variant="text" width={60} /></TableCell>
                  ))}
                </TableRow>
              ))
            }
            {!isLoading && attestations.length === 0 && (
              <TableRow>
                <TableCell colSpan={9}>
                  <Typography sx={{ p: 2, color: 'text.secondary', fontSize: '0.8rem', textAlign: 'center' }}>
                    No agents scanned yet. Run a scan from the Security Hub.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
            {attestations.map((a, i) => (
              <TableRow
                key={`${a.agent_id}-${a.timestamp}`}
                hover
                sx={{ opacity: a.kill_switch_active ? 0.55 : 1 }}
              >
                <TableCell sx={{ fontSize: '0.72rem', color: 'text.disabled', fontWeight: 600 }}>
                  {i === 0 && !a.kill_switch_active ? '🥇' : i + 1}
                </TableCell>
                <TableCell sx={{ fontSize: '0.78rem', fontFamily: 'monospace', maxWidth: 120 }}>
                  <Box sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {a.agent_id}
                  </Box>
                </TableCell>
                <TableCell sx={{ fontSize: '0.72rem', color: 'text.secondary', maxWidth: 160 }}>
                  <Box sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {a.agent_endpoint}
                  </Box>
                </TableCell>
                <TableCell><TpiScoreBadge score={a.tpi_score} /></TableCell>
                <TableCell>
                  <OWASPBar breakdown={a.owasp_breakdown ?? {}} />
                </TableCell>
                <TableCell>
                  {a.kill_switch_active ? (
                    <Chip label="Paused" size="small" sx={{ fontSize: '0.65rem', bgcolor: '#ef444420', color: '#ef4444' }} />
                  ) : a.is_certified ? (
                    <Chip icon={<VerifiedIcon sx={{ fontSize: 12 }} />} label="Certified" size="small" sx={{ fontSize: '0.65rem', bgcolor: '#22c55e20', color: '#22c55e' }} />
                  ) : a.is_verified ? (
                    <Chip icon={<ShieldOutlinedIcon sx={{ fontSize: 12 }} />} label="Verified" size="small" sx={{ fontSize: '0.65rem', bgcolor: '#534AB720', color: '#534AB7' }} />
                  ) : (
                    <Chip label="Pending" size="small" sx={{ fontSize: '0.65rem', bgcolor: '#f59e0b20', color: '#f59e0b' }} />
                  )}
                </TableCell>
                <TableCell sx={{ fontSize: '0.7rem', color: 'text.secondary' }}>
                  {new Date(a.timestamp).toLocaleString()}
                </TableCell>
                <TableCell>
                  {a.tx_hash ? (
                    <Button
                      size="small"
                      endIcon={<OpenInNewIcon sx={{ fontSize: 10 }} />}
                      onClick={() => window.open(`${MONAD_EXPLORER}/tx/${a.tx_hash}`, '_blank')}
                      sx={{ fontSize: '0.65rem', textTransform: 'none', p: 0.5 }}
                    >
                      View
                    </Button>
                  ) : (
                    <Typography sx={{ fontSize: '0.68rem', color: 'text.disabled' }}>—</Typography>
                  )}
                </TableCell>
                <TableCell>
                  <Tooltip title={a.kill_switch_active ? 'Reactivate agent' : 'Suspend agent on-chain'}>
                    <IconButton
                      size="small"
                      disabled={killMutation.isPending}
                      onClick={() => killMutation.mutate({ agentId: a.agent_id, activate: !a.kill_switch_active })}
                      sx={{
                        color: a.kill_switch_active ? '#22c55e' : '#ef4444',
                        '&:hover': { bgcolor: a.kill_switch_active ? '#22c55e20' : '#ef444420' },
                      }}
                    >
                      <GppBadOutlinedIcon sx={{ fontSize: 16 }} />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Typography sx={{ fontSize: '0.72rem', color: 'text.disabled', mt: 1.5, textAlign: 'center' }}>
        Sorted by TPI score · OWASP dots: green = all passed, amber = partial, red = failed ·
        Kill switch writes a PAUSED record to ERC-8004 Reputation Registry on Monad
      </Typography>
    </Box>
  )
}
