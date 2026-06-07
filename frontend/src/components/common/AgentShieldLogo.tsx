import Box from '@mui/material/Box';
import type { SxProps, Theme } from '@mui/material/styles';

interface AgentShieldLogoProps {
    size?: number;
    sx?: SxProps<Theme>;
}

export default function AgentShieldLogo({ size = 24, sx }: AgentShieldLogoProps) {
    return (
        <Box
            sx={{
                width: size,
                height: size,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                ...sx,
            }}
        >
            <svg
                width={size}
                height={size}
                viewBox="0 0 32 32"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
            >
                <path
                    d="M16 2L4 7v9c0 6.627 5.148 11.8 12 13 6.852-1.2 12-6.373 12-13V7L16 2z"
                    fill="#534AB7"
                />
                <path
                    d="M16 5L6.5 9.25V16c0 5.2 4.05 9.35 9.5 10.3C21.45 25.35 25.5 21.2 25.5 16V9.25L16 5z"
                    fill="#6B62D4"
                />
                <path
                    d="M11 16.5l3.5 3.5 6.5-7"
                    stroke="white"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                />
            </svg>
        </Box>
    );
}
