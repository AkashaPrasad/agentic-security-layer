import { useState } from 'react'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Chip from '@mui/material/Chip'
import Collapse from '@mui/material/Collapse'
import IconButton from '@mui/material/IconButton'
import Divider from '@mui/material/Divider'
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline'
import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import ExpandLessIcon from '@mui/icons-material/ExpandLess'
import type { TestResult } from '@/services/agentshieldService'

const OWASP_COLORS: Record<string, string> = {
  LLM01: '#ef4444',
  LLM02: '#f59e0b',
  LLM06: '#8b5cf6',
}

interface TestResultCardProps {
  result: TestResult
  index: number
}

export default function TestResultCard({ result, index }: TestResultCardProps) {
  const [expanded, setExpanded] = useState(!result.passed)

  const statusColor = result.passed ? '#22c55e' : '#ef4444'
  const owaspColor = OWASP_COLORS[result.owasp_category ?? 'LLM01'] ?? '#6b7280'
  const isHindi = result.test_name.toLowerCase().includes('hindi') || result.test_name.toLowerCase().includes('multilingual')

  return (
    <Paper
      variant="outlined"
      sx={{
        borderColor: `${statusColor}40`,
        borderRadius: '8px',
        bgcolor: result.passed ? 'rgba(34,197,94,0.03)' : 'rgba(239,68,68,0.04)',
        overflow: 'hidden',
      }}
    >
      {/* Header row — always visible, click to expand */}
      <Box
        onClick={() => setExpanded((v) => !v)}
        sx={{
          display: 'flex',
          alignItems: 'center',
          gap: 1.5,
          px: 1.5,
          py: 1.25,
          cursor: 'pointer',
          '&:hover': { bgcolor: `${statusColor}08` },
        }}
      >
        {result.passed
          ? <CheckCircleOutlineIcon sx={{ fontSize: 18, color: '#22c55e', flexShrink: 0 }} />
          : <CancelOutlinedIcon sx={{ fontSize: 18, color: '#ef4444', flexShrink: 0 }} />
        }

        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.75, flexWrap: 'wrap' }}>
            <Typography sx={{ fontWeight: 600, fontSize: '0.82rem' }}>
              Test {index + 1}: {result.test_name}
            </Typography>
            {result.owasp_category && (
              <Chip
                label={result.owasp_category}
                size="small"
                title={result.owasp_label}
                sx={{ fontSize: '0.6rem', height: 16, bgcolor: `${owaspColor}20`, color: owaspColor, border: `1px solid ${owaspColor}40` }}
              />
            )}
            {result.weight !== undefined && (
              <Typography sx={{ fontSize: '0.6rem', color: 'text.disabled' }}>w:{result.weight}%</Typography>
            )}
            {isHindi && (
              <Chip
                label="Sarvam AI"
                size="small"
                sx={{ fontSize: '0.6rem', height: 16, bgcolor: '#f59e0b20', color: '#f59e0b', border: '1px solid #f59e0b40' }}
              />
            )}
          </Box>
          {/* Compact preview when collapsed */}
          {!expanded && (
            <Typography sx={{ fontSize: '0.7rem', color: 'text.disabled', mt: 0.25, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 340 }}>
              {result.agent_response}
            </Typography>
          )}
        </Box>

        <Chip
          label={result.passed ? 'PASS' : 'FAIL'}
          size="small"
          sx={{
            fontSize: '0.68rem',
            height: 18,
            fontWeight: 700,
            bgcolor: `${statusColor}20`,
            color: statusColor,
            flexShrink: 0,
          }}
        />

        <IconButton size="small" sx={{ color: 'text.disabled', flexShrink: 0, p: 0.25 }}>
          {expanded ? <ExpandLessIcon sx={{ fontSize: 16 }} /> : <ExpandMoreIcon sx={{ fontSize: 16 }} />}
        </IconButton>
      </Box>

      {/* Expanded detail */}
      <Collapse in={expanded}>
        <Divider sx={{ borderColor: `${statusColor}30` }} />
        <Box sx={{ px: 2, py: 1.5, display: 'flex', flexDirection: 'column', gap: 1.25 }}>

          {/* Attack prompt */}
          <Box>
            <Typography sx={{ fontSize: '0.7rem', fontWeight: 600, color: 'text.secondary', mb: 0.4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Attack Prompt
            </Typography>
            <Box sx={{ bgcolor: 'action.hover', borderRadius: '6px', px: 1.5, py: 1 }}>
              <Typography sx={{ fontSize: '0.78rem', color: 'text.primary', lineHeight: 1.5 }}>
                {result.attack_prompt}
              </Typography>
            </Box>
          </Box>

          {/* Agent response */}
          <Box>
            <Typography sx={{ fontSize: '0.7rem', fontWeight: 600, color: result.passed ? 'text.secondary' : '#ef4444', mb: 0.4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Agent Response {!result.passed && '⚠ Jailbroken'}
            </Typography>
            <Box
              sx={{
                bgcolor: result.passed ? 'action.hover' : 'rgba(239,68,68,0.06)',
                border: result.passed ? 'none' : '1px solid rgba(239,68,68,0.2)',
                borderRadius: '6px',
                px: 1.5,
                py: 1,
              }}
            >
              <Typography
                sx={{
                  fontSize: '0.82rem',
                  color: result.passed ? 'text.primary' : '#ef4444',
                  lineHeight: 1.6,
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word',
                }}
              >
                {result.agent_response}
              </Typography>
            </Box>
          </Box>

          {/* Failure reason */}
          {!result.passed && result.failure_reason && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <CancelOutlinedIcon sx={{ fontSize: 14, color: '#ef4444' }} />
              <Typography sx={{ fontSize: '0.72rem', color: '#ef4444', fontStyle: 'italic' }}>
                {result.failure_reason}
              </Typography>
            </Box>
          )}
        </Box>
      </Collapse>
    </Paper>
  )
}
