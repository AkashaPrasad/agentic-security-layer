import { useAccount, useConnect, useDisconnect } from 'wagmi'
import { injected } from 'wagmi/connectors'
import Button from '@mui/material/Button'
import Chip from '@mui/material/Chip'
import AccountBalanceWalletOutlinedIcon from '@mui/icons-material/AccountBalanceWalletOutlined'
import Tooltip from '@mui/material/Tooltip'

export default function WalletConnect() {
  const { address, isConnected } = useAccount()
  const { connect, isPending } = useConnect()
  const { disconnect } = useDisconnect()

  if (isConnected && address) {
    return (
      <Tooltip title="Click to disconnect">
        <Chip
          label={`${address.slice(0, 6)}…${address.slice(-4)}`}
          size="small"
          icon={<AccountBalanceWalletOutlinedIcon sx={{ fontSize: '14px !important' }} />}
          onClick={() => disconnect()}
          sx={{
            bgcolor: '#534AB7',
            color: '#fff',
            fontFamily: 'monospace',
            fontSize: '0.7rem',
            cursor: 'pointer',
            '&:hover': { bgcolor: '#4239a0' },
          }}
        />
      </Tooltip>
    )
  }

  return (
    <Button
      size="small"
      variant="outlined"
      startIcon={<AccountBalanceWalletOutlinedIcon sx={{ fontSize: 14 }} />}
      onClick={() => connect({ connector: injected() })}
      disabled={isPending}
      sx={{
        fontSize: '0.75rem',
        borderColor: '#534AB7',
        color: '#534AB7',
        height: 28,
        textTransform: 'none',
        '&:hover': { borderColor: '#4239a0', bgcolor: 'rgba(83,74,183,0.06)' },
      }}
    >
      {isPending ? 'Connecting…' : 'Connect Wallet'}
    </Button>
  )
}
