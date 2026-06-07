export const MONAD_FACILITATOR = 'https://x402-facilitator.molandak.org'
export const MONAD_NETWORK = 'eip155:10143'
export const TESTNET_USDC = '0x534b2f3A21130d7a60830c2Df862319e593943A3' as const
export const SCAN_PRICE = '0.10'
export const SCAN_PRICE_DISPLAY = '0.10 USDC'
const _API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'
export const DEMO_AGENT_URL = `${_API_BASE}/demo-agent`
