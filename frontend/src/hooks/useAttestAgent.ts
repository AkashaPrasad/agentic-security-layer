import { useState } from 'react'
import { useWriteContract } from 'wagmi'
import { parseAbi } from 'viem'
import { ERC8004_REPUTATION_REGISTRY } from '@/lib/erc8004'

const ABI = parseAbi([
  'function submitFeedback(uint256 agentId, uint256 value, bytes32[] tags, string feedbackURI, bytes32 contentHash) returns (uint256)',
])

export function useAttestAgent() {
  const { writeContractAsync, isPending } = useWriteContract()
  const [error, setError] = useState<string | null>(null)

  const attest = async (
    agentId: string,
    tpiScore: number,
    resultHash: string,
  ): Promise<string> => {
    setError(null)
    const agentIdNum = BigInt('0x' + Buffer.from(agentId).toString('hex').slice(0, 16))
    const tpiValue = BigInt(Math.round(tpiScore * 100))
    const contentHash = resultHash.startsWith('0x')
      ? (resultHash as `0x${string}`)
      : (`0x${resultHash.padEnd(64, '0')}` as `0x${string}`)
    const feedbackURI = `agentshield://attestation/${agentId}/${tpiScore}`

    const hash = await writeContractAsync({
      address: ERC8004_REPUTATION_REGISTRY as `0x${string}`,
      abi: ABI,
      functionName: 'submitFeedback',
      args: [agentIdNum, tpiValue, [], feedbackURI, contentHash],
    })

    return hash
  }

  return { attest, isPending, error }
}
