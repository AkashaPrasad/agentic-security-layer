import React from 'react'
import { createConfig, WagmiProvider as BaseWagmiProvider, http } from 'wagmi'
import { injected } from 'wagmi/connectors'
import { monadTestnet } from '@/lib/monad'

export const wagmiConfig = createConfig({
  chains: [monadTestnet],
  connectors: [injected()],
  transports: {
    [monadTestnet.id]: http('https://testnet-rpc.monad.xyz'),
  },
})

export default function WagmiProvider({ children }: { children: React.ReactNode }) {
  return (
    <BaseWagmiProvider config={wagmiConfig}>
      {children}
    </BaseWagmiProvider>
  )
}
