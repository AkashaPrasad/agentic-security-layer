import os
import httpx
from fastapi import HTTPException, Request

MONAD_FACILITATOR = os.getenv("MONAD_FACILITATOR_URL", "https://x402-facilitator.molandak.org")
PAY_TO_ADDRESS = os.getenv("PAY_TO_ADDRESS", "")
SCAN_PRICE_USDC = os.getenv("SCAN_PRICE_USDC", "0.10")
MONAD_NETWORK = "eip155:10143"

async def verify_x402_payment(request: Request) -> str:
    """Verify x402 payment header.

    Dev mode: when PAY_TO_ADDRESS is not set, skip all payment checks so
    local demos work without MetaMask or testnet USDC.
    """
    if not PAY_TO_ADDRESS:
        # Dev/demo mode — payment bypass active
        return request.headers.get("X-PAYMENT", "dev-mode-bypass")

    payment_header = request.headers.get("X-PAYMENT")
    if not payment_header:
        raise HTTPException(
            status_code=402,
            detail="Payment required. Send 0.10 USDC on Monad Testnet via X-PAYMENT header.",
            headers={"X-PAYMENT-REQUIRED": "true"},
        )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{MONAD_FACILITATOR}/verify",
                json={
                    "payment": payment_header,
                    "network": MONAD_NETWORK,
                    "amount": SCAN_PRICE_USDC,
                    "currency": "USDC",
                    "payTo": PAY_TO_ADDRESS,
                },
            )
            result = resp.json()
            if not result.get("valid"):
                raise HTTPException(status_code=402, detail="Invalid x402 payment: " + result.get("reason", "unknown"))
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=402, detail="Payment verification failed — facilitator unreachable")

    return payment_header

async def settle_x402_payment(payment_header: str) -> str | None:
    """Settle the x402 payment after successful scan."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{MONAD_FACILITATOR}/settle",
                json={"payment": payment_header, "network": MONAD_NETWORK},
            )
            return resp.json().get("txHash")
    except Exception:
        return None
