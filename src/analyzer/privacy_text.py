"""
Análise NLP do texto da política de privacidade.
Usa spaCy quando disponível; cai para keyword matching simples caso contrário.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import re


@dataclass
class PolicyFeatures:
    language_detected: Optional[str] = None
    has_consent_terms: bool = False
    has_erasure_terms: bool = False
    has_controller_terms: bool = False
    has_dpo_terms: bool = False
    has_dpo_contact: bool = False
    has_access_right_terms: bool = False       # RGPD-15
    has_international_transfer_terms: bool = False  # RGPD-16
    has_retention_terms: bool = False          # RGPD-17
    missing_terms: List[str] = field(default_factory=list)


_KEYWORD_MAP = {
    "consent": ["consentimento", "consent", "autorização", "autorizo"],
    "erasure": ["apagamento", "esquecido", "erasure", "right to be forgotten", "direito ao apagamento"],
    "controller": ["responsável pelo tratamento", "data controller", "responsável", "controller", "entidade responsável"],
    "dpo": ["dpo", "encarregado de proteção", "encarregado de dados", "data protection officer", "encarregado"],
    "access": ["direito de acesso", "acesso aos dados", "right of access", "right to access", "aceder aos seus dados"],
    "international": ["transferências internacionais", "international transfers", "terceiros países", "third countries", "fora da união europeia", "outside the eu"],
    "retention": ["prazo de conservação", "período de conservação", "retention period", "conservados durante", "guardados por", "eliminados após", "deleted after"],
}

_DPO_CONTACT_PATTERN = re.compile(
    r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+|dpo@|privacidade@|gdpr@",
    re.IGNORECASE,
)


def _keyword_check(text_lower: str, keywords: List[str]) -> bool:
    return any(kw in text_lower for kw in keywords)


def _try_spacy_language(text: str) -> Optional[str]:
    try:
        import spacy
        for model in ("pt_core_news_sm", "en_core_web_sm"):
            try:
                nlp = spacy.load(model)
                _ = nlp(text[:500])
                return "pt" if model.startswith("pt") else "en"
            except OSError:
                continue
    except ImportError:
        pass
    return None


def _langdetect_language(text: str) -> Optional[str]:
    try:
        from langdetect import detect
        return detect(text)
    except Exception:
        return None


def analyze_policy(text: str, site_language: Optional[str] = None) -> PolicyFeatures:
    if not text or not text.strip():
        return PolicyFeatures(missing_terms=list(_KEYWORD_MAP.keys()))

    text_lower = text.lower()

    lang = _try_spacy_language(text) or _langdetect_language(text)

    has_consent = _keyword_check(text_lower, _KEYWORD_MAP["consent"])
    has_erasure = _keyword_check(text_lower, _KEYWORD_MAP["erasure"])
    has_controller = _keyword_check(text_lower, _KEYWORD_MAP["controller"])
    has_dpo = _keyword_check(text_lower, _KEYWORD_MAP["dpo"])
    has_dpo_contact = bool(_DPO_CONTACT_PATTERN.search(text))
    has_access = _keyword_check(text_lower, _KEYWORD_MAP["access"])
    has_international = _keyword_check(text_lower, _KEYWORD_MAP["international"])
    has_retention = _keyword_check(text_lower, _KEYWORD_MAP["retention"])

    missing = []
    if not has_consent:
        missing.append("consentimento")
    if not has_erasure:
        missing.append("direito ao apagamento")
    if not has_controller:
        missing.append("responsável pelo tratamento")
    if not has_dpo:
        missing.append("DPO / encarregado de proteção")
    if not has_access:
        missing.append("direito de acesso")
    if not has_international:
        missing.append("transferências internacionais")
    if not has_retention:
        missing.append("prazo de conservação")

    return PolicyFeatures(
        language_detected=lang,
        has_consent_terms=has_consent,
        has_erasure_terms=has_erasure,
        has_controller_terms=has_controller,
        has_dpo_terms=has_dpo,
        has_dpo_contact=has_dpo_contact,
        has_access_right_terms=has_access,
        has_international_transfer_terms=has_international,
        has_retention_terms=has_retention,
        missing_terms=missing,
    )
