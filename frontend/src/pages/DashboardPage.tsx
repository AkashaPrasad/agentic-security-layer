// ---------------------------------------------------------------------------
// DashboardPage — AI Security Hub (scan any endpoint, attest on Monad)
// ---------------------------------------------------------------------------

import { useState } from 'react'
import Box from '@mui/material/Box'
import Grid from '@mui/material/Grid'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Divider from '@mui/material/Divider'
import Chip from '@mui/material/Chip'
import VerifiedIcon from '@mui/icons-material/Verified'
import GppBadOutlinedIcon from '@mui/icons-material/GppBadOutlined'
import SecurityOutlinedIcon from '@mui/icons-material/SecurityOutlined'
import { useQuery } from '@tanstack/react-query'
import AgentScanForm from '@/components/agentshield/AgentScanForm'
import ScanProgress from '@/components/agentshield/ScanProgress'
import AttestationWriter from '@/components/agentshield/AttestationWriter'
import TpiScoreBadge from '@/components/agentshield/TpiScoreBadge'
import WalletConnect from '@/components/wallet/WalletConnect'
import { getAllAttestations } from '@/services/agentshieldService'
import type { ScanResponse, VerifyRecord } from '@/services/agentshieldService'
import { MONAD_EXPLORER } from '@/lib/monad'

function StatCard({ label, value, color }: { label: string; value: string | number; color?: string }) {
  return (
    <Paper
      variant="outlined"
      sx={{ p: 2, borderRadius: '10px', textAlign: 'center', flex: 1 }}
    >
      <Typography sx={{ fontSize: '1.5rem', fontWeight: 700, color: color ?? 'text.primary', lineHeight: 1 }}>
        {value}
      </Typography>
      <Typography sx={{ fontSize: '0.72rem', color: 'text.secondary', mt: 0.5 }}>
        {label}
      </Typography>
    </Paper>
  )
}

export default function DashboardPage() {
  const [scanResult, setScanResult] = useState<ScanResponse | null>(null)

  const { data: attestations = [] } = useQuery<VerifyRecord[]>({
    queryKey: ['agentshield', 'all'],
    queryFn: getAllAttestations,
    refetchInterval: 10_000,
  })

  const totalScanned = attestations.length
  const certified = attestations.filter((a) => a.is_certified).length
  const killSwitched = attestations.filter((a) => (a as any).kill_switch_active).length
  const avgTpi = totalScanned
    ? Math.round(attestations.reduce((s, a) => s + a.tpi_score, 0) / totalScanned)
    : 0

  const recent = [...attestations].slice(0, 5)

  return (
    <Box>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', mb: 3, flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 0.5 }}>
            <SecurityOutlinedIcon sx={{ color: '#534AB7', fontSize: 26 }} />
            <Typography variant="h5" sx={{ fontWeight: 700, letterSpacing: '-0.02em' }}>
              AI Security Hub
            </Typography>
          </Box>
          <Typography color="text.secondary" sx={{ fontSize: '0.875rem' }}>
            Red-team scan any AI agent or model endpoint · OWASP LLM Top 10 · On-chain attestation via Monad
          </Typography>
        </Box>
        <WalletConnect />
      </Box>

      {/* Stats bar */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3, flexWrap: 'wrap' }}>
        <StatCard label="Total Scanned" value={totalScanned} />
        <StatCard label="Avg TPI Score" value={`${avgTpi}/100`} color="#534AB7" />
        <StatCard label="Certified (≥80)" value={certified} color="#22c55e" />
        <StatCard label="Kill Switches Active" value={killSwitched} color={killSwitched > 0 ? '#ef4444' : 'text.primary'} />
      </Box>

      {/* Main two-column layout */}
      <Grid container spacing={3}>
        {/* Left — Scan form */}
        <Grid size={{ xs: 12, md: 5 }}>
          <Paper variant="outlined" sx={{ p: 3, borderRadius: '12px' }}>
            <Typography sx={{ fontWeight: 600, mb: 0.5, fontSize: '0.9rem' }}>
              Scan AI Endpoint
            </Typography>
            <Typography sx={{ fontSize: '0.75rem', color: 'text.secondary', mb: 2 }}>
              Runs 5 OWASP-weighted adversarial tests. Pays 0.10 USDC via x402 on Monad Testnet.
            </Typography>
            <AgentScanForm onScanComplete={setScanResult} />
          </Paper>

          {/* OWASP legend */}
          <Paper variant="outlined" sx={{ p: 2, borderRadius: '12px', mt: 2 }}>
            <Typography sx={{ fontWeight: 600, fontSize: '0.8rem', mb: 1.5 }}>OWASP LLM Weight Map</Typography>
            {[
              { cat: 'LLM01', label: 'Prompt Injection', weight: 55, color: '#ef4444' },
              { cat: 'LLM02', label: 'Insecure Output Handling', weight: 20, color: '#f59e0b' },
              { cat: 'LLM06', label: 'Sensitive Info Disclosure', weight: 15, color: '#8b5cf6' },
              { cat: 'LLM01*', label: 'Multilingual Injection', weight: 10, color: '#06b6d4' },
            ].map((row) => (
              <Box key={row.cat} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 0.75 }}>
                <Chip label={row.cat} size="small" sx={{ fontSize: '0.6rem', height: 16, bgcolor: `${row.color}20`, color: row.color, borderColor: `${row.color}40`, border: '1px solid' }} />
                <Typography sx={{ fontSize: '0.75rem', flex: 1, color: 'text.secondary' }}>{row.label}</Typography>
                <Typography sx={{ fontSize: '0.72rem', fontWeight: 600 }}>{row.weight}%</Typography>
              </Box>
            ))}
          </Paper>
        </Grid>

        {/* Right — Results */}
        <Grid size={{ xs: 12, md: 7 }}>
          {scanResult ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <Paper variant="outlined" sx={{ p: 3, borderRadius: '12px' }}>
                <Typography sx={{ fontWeight: 600, mb: 2, fontSize: '0.9rem' }}>Scan Results</Typography>
                <ScanProgress scanResult={scanResult} isLoading={false} />
              </Paper>
              <Paper variant="outlined" sx={{ p: 3, borderRadius: '12px' }}>
                <Typography sx={{ fontWeight: 600, mb: 2, fontSize: '0.9rem' }}>Write Security Passport</Typography>
                <AttestationWriter scanResult={scanResult} />
              </Paper>
            </Box>
          ) : (
            <Paper
              variant="outlined"
              sx={{
                p: 4,
                borderRadius: '12px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                minHeight: 220,
                bgcolor: (t) => t.palette.mode === 'dark' ? 'rgba(83,74,183,0.04)' : 'rgba(83,74,183,0.02)',
                borderStyle: 'dashed',
              }}
            >
              <SecurityOutlinedIcon sx={{ fontSize: 40, color: '#534AB7', opacity: 0.4, mb: 1.5 }} />
              <Typography sx={{ color: 'text.secondary', fontSize: '0.875rem', textAlign: 'center' }}>
                Submit an AI agent or model endpoint URL to run a red-team scan.<br />
                Results and on-chain attestation appear here.
              </Typography>
            </Paper>
          )}
        </Grid>
      </Grid>

      {/* Recent attestations */}
      {recent.length > 0 && (
        <Box sx={{ mt: 4 }}>
          <Typography sx={{ fontWeight: 600, fontSize: '0.9rem', mb: 1.5 }}>Recent Attestations</Typography>
          <Paper variant="outlined" sx={{ borderRadius: '12px', overflow: 'hidden' }}>
            {recent.map((a, i) => (
              <Box key={`${a.agent_id}-${a.timestamp}`}>
                {i > 0 && <Divider />}
                <Box
                  sx={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 2,
                    px: 2.5,
                    py: 1.25,
                    '&:hover': { bgcolor: 'action.hover' },
                    flexWrap: 'wrap',
                  }}
                >
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography sx={{ fontFamily: 'monospace', fontSize: '0.8rem', fontWeight: 600, color: 'text.primary' }}>
                      {a.agent_id}
                    </Typography>
                    <Typography sx={{ fontSize: '0.7rem', color: 'text.secondary', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {a.agent_endpoint}
                    </Typography>
                  </Box>
                  <TpiScoreBadge score={a.tpi_score} />
                  {(a as any).kill_switch_active ? (
                    <Chip icon={<GppBadOutlinedIcon sx={{ fontSize: 14 }} />} label="Paused" size="small" sx={{ fontSize: '0.68rem', bgcolor: '#ef444420', color: '#ef4444' }} />
                  ) : a.is_certified ? (
                    <Chip icon={<VerifiedIcon sx={{ fontSize: 14 }} />} label="Certified" size="small" sx={{ fontSize: '0.68rem', bgcolor: '#22c55e20', color: '#22c55e' }} />
                  ) : null}
                  <Typography sx={{ fontSize: '0.7rem', color: 'text.disabled', minWidth: 100, textAlign: 'right' }}>
                    {new Date(a.timestamp).toLocaleTimeString()}
                  </Typography>
                  {a.tx_hash && (
                    <Typography
                      component="a"
                      href={`${MONAD_EXPLORER}/tx/${a.tx_hash}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      sx={{ fontSize: '0.68rem', color: '#534AB7', textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}
                    >
                      MonadVision ↗
                    </Typography>
                  )}
                </Box>
              </Box>
            ))}
          </Paper>
        </Box>
      )}
    </Box>
  )
}
