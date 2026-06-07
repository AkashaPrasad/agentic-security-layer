import { defineChain } from 'viem'

export const monadTestnet = defineChain({
  id: 10143,
  name: 'Monad Testnet',
  nativeCurrency: { name: 'MON', symbol: 'MON', decimals: 18 },
  rpcUrls: {
    default: { http: ['https://testnet-rpc.monad.xyz'] },
  },
  blockExplorers: {
    default: { name: 'MonadVision', url: 'https://monadvision.com' },
  },
  testnet: true,
})

export const MONAD_CHAIN_ID = 10143
export const MONAD_EXPLORER = 'https://monadvision.com'
export const MONAD_FAUCET = 'https://faucet.monad.xyz'
export const USDC_FAUCET = 'https://faucet.circle.com'
