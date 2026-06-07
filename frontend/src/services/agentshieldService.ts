import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

export interface TestResult {
  test_name: string
  owasp_category: string
  owasp_label: string
  weight: number
  attack_prompt: string
  agent_response: string
  passed: boolean
  failure_reason?: string
}

export interface OWASPBreakdown {
  label: string
  passed: number
  total: number
  weight: number
}

export interface ScanResponse {
  agent_id: string
  tpi_score: number
  passed_tests: number
  total_tests: number
  test_results: TestResult[]
  owasp_breakdown: Record<string, OWASPBreakdown>
  kill_switch_triggered: boolean
  result_hash: string
  timestamp: string
}

export interface VerifyRecord {
  agent_id: string
  agent_endpoint: string
  tpi_score: number
  is_verified: boolean
  is_certified: boolean
  kill_switch_active: boolean
  result_hash: string
  tx_hash?: string
  owasp_breakdown: Record<string, OWASPBreakdown>
  timestamp: string
}

export async function scanAgent(params: {
  agentEndpoint: string
  agentId: string
  walletAddress?: string
  paymentHeader?: string
}): Promise<ScanResponse> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (params.paymentHeader) {
    headers['X-PAYMENT'] = params.paymentHeader
  }
  const { data } = await axios.post(
    `${BASE}/monad/scan`,
    {
      agent_endpoint: params.agentEndpoint,
      agent_id: params.agentId,
      wallet_address: params.walletAddress,
    },
    { headers }
  )
  return data
}

export async function attestAgent(params: {
  agentId: string
  tpiScore: number
  resultHash: string
  txHash: string
  walletAddress?: string
  erc8004FeedbackId?: number
}) {
  const { data } = await axios.post(`${BASE}/monad/attest`, {
    agent_id: params.agentId,
    tpi_score: params.tpiScore,
    result_hash: params.resultHash,
    tx_hash: params.txHash,
    wallet_address: params.walletAddress,
    erc8004_feedback_id: params.erc8004FeedbackId,
  })
  return data
}

export async function verifyAgent(agentId: string) {
  const { data } = await axios.get(`${BASE}/monad/verify/${agentId}`)
  return data
}

export async function getAllAttestations(): Promise<VerifyRecord[]> {
  const { data } = await axios.get(`${BASE}/monad/verify/all`)
  return data
}

export async function triggerKillSwitch(agentId: string, activate: boolean): Promise<void> {
  await axios.post(`${BASE}/monad/kill-switch/${agentId}?activate=${activate}`, {})
}
