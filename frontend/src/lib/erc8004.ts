export const ERC8004_IDENTITY_REGISTRY = '0x8004A169FB4a3325136EB29fA0ceB6D2e539a432' as const
export const ERC8004_REPUTATION_REGISTRY = '0x8004BAa17C55a88189AE136b182e5fdA19dE9b63' as const

export const REPUTATION_REGISTRY_ABI = [
  {
    name: 'submitFeedback',
    type: 'function',
    stateMutability: 'nonpayable',
    inputs: [
      { name: 'agentId', type: 'uint256' },
      { name: 'value', type: 'uint256' },
      { name: 'tags', type: 'bytes32[]' },
      { name: 'feedbackURI', type: 'string' },
      { name: 'contentHash', type: 'bytes32' },
    ],
    outputs: [{ name: 'feedbackId', type: 'uint256' }],
  },
  {
    name: 'getFeedback',
    type: 'function',
    stateMutability: 'view',
    inputs: [
      { name: 'agentId', type: 'uint256' },
      { name: 'feedbackId', type: 'uint256' },
    ],
    outputs: [
      { name: 'value', type: 'uint256' },
      { name: 'tags', type: 'bytes32[]' },
      { name: 'feedbackURI', type: 'string' },
      { name: 'contentHash', type: 'bytes32' },
      { name: 'timestamp', type: 'uint256' },
    ],
  },
] as const
