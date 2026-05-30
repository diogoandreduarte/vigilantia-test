from pydantic import BaseModel
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    HIGH = "high"        # viola diretamente o RGPD
    MEDIUM = "medium"    # prática incorreta mas não crítica
    LOW = "low"          # sugestão de melhoria
    INFO = "info"        # informativo, sem violação


class FindingCategory(str, Enum):
    CONSENT = "consentimento"
    COOKIES = "cookies"
    THIRD_PARTY = "terceiros"
    FORMS = "formularios"
    POLICY = "politica"


class Finding(BaseModel):
    rule_id: str                        # ex: "RGPD-01"
    category: FindingCategory           # categoria da regra
    severity: Severity                  # gravidade: high, medium, low, info
    title: str                          # título curto da não-conformidade
    description: str                    # explicação do problema encontrado
    evidence: Optional[str] = None      # excerto ou valor concreto que triggou a regra
    recommendation: str                 # o que o site deve fazer para corrigir
    article: Optional[str] = None       # artigo do RGPD relacionado (ex: "Art. 7")
    passed: bool = False                # True se o site cumpre esta regra


if __name__ == "__main__":
    finding = Finding(
        rule_id="RGPD-01",
        category=FindingCategory.CONSENT,
        severity=Severity.HIGH,
        title="Banner de consentimento ausente",
        description="O site não apresenta banner de cookies.",
        recommendation="Adicionar banner de consentimento conforme Art. 7 RGPD.",
        article="Art. 7",
        passed=False,
    )
    print(finding)