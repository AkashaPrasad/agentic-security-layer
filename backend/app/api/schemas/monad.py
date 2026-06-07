from pydantic import BaseModel
from typing import Optional


class TestResult(BaseModel):
    test_name: str
    owasp_category: str = "LLM01"
    owasp_label: str = "Prompt Injection"
    weight: int = 20
    attack_prompt: str
    agent_response: str
    passed: bool
    failure_reason: Optional[str] = None


class OWASPCategoryBreakdown(BaseModel):
    label: str
    passed: int
    total: int
    weight: int


class ScanRequest(BaseModel):
    agent_endpoint: str
    agent_id: str
    wallet_address: Optional[str] = None


class ScanResponse(BaseModel):
    agent_id: str
    tpi_score: int
    passed_tests: int
    total_tests: int
    test_results: list[TestResult]
    owasp_breakdown: dict[str, OWASPCategoryBreakdown] = {}
    kill_switch_triggered: bool = False
    result_hash: str
    timestamp: str


class AttestRequest(BaseModel):
    agent_id: str
    tpi_score: int
    result_hash: str
    tx_hash: Optional[str] = None
    wallet_address: Optional[str] = None
    erc8004_feedback_id: Optional[int] = None


class AttestResponse(BaseModel):
    agent_id: str
    tpi_score: int
    result_hash: str
    tx_hash: Optional[str]
    attested_at: str
    is_certified: bool
    kill_switch_active: bool = False


class VerifyResponse(BaseModel):
    agent_id: str
    is_verified: bool
    tpi_score: Optional[int]
    result_hash: Optional[str]
    tx_hash: Optional[str]
    timestamp: Optional[str]
    is_certified: bool
    kill_switch_active: bool = False
    owasp_breakdown: dict = {}


class KillSwitchRequest(BaseModel):
    activated_by: Optional[str] = None


class KillSwitchResponse(BaseModel):
    agent_id: str
    kill_switch_active: bool
    tpi_score: Optional[int]


class DemoAgentRequest(BaseModel):
    message: str
