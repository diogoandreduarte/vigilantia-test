from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from datetime import datetime

# ─────────────────────────────────────────
#  COOKIE — representa um cookie do site
# ─────────────────────────────────────────
class Cookie(BaseModel):
    name: str                  # nome do cookie (ex: "_ga", "session_id")
    domain: str                # domínio a que pertence (ex: ".google.com")
    path: str = "/"            # caminho no site (normalmente "/")
    secure: bool = False       # só viaja por HTTPS?
    httpOnly: bool = False     # inacessível ao JavaScript do browser?
    sameSite: Optional[str] = None  # proteção contra ataques CSRF

# ─────────────────────────────────────────
#  SCRIPT DE TERCEIROS — ex: Google Analytics, Facebook Pixel
# ─────────────────────────────────────────
class ThirdPartyScript(BaseModel):
    src: str                   # endereço do script externo
    category: str = "unknown"  # tipo: analytics, advertising, social, unknown

# ─────────────────────────────────────────
#  FORMULÁRIO — ex: formulário de contacto, login, newsletter
# ─────────────────────────────────────────
class Form(BaseModel):
    action: Optional[str] = None  # para onde envia os dados
    method: str = "GET"           # GET ou POST
    fields: List[str] = []        # nomes dos campos (ex: ["email", "password"])
    has_privacy_notice: bool = False  # tem aviso RGPD junto ao formulário?
    password_autocomplete_ok: bool = True  # campos password têm autocomplete="new-password"?

# ─────────────────────────────────────────
#  SITE DATA — o "contrato" principal
#  Este é o objeto que o João preenche e o Diogo consome
# ─────────────────────────────────────────
class SiteData(BaseModel):
    # Informação geral
    url: str                              # URL original fornecido pelo utilizador
    final_url: str                        # URL após redirecionamentos
    language: str = "unknown"            # idioma detectado (ex: "pt", "en")
    scraped_at: datetime = datetime.now() # data e hora da análise

    # Elementos recolhidos
    cookies: List[Cookie] = []
    third_party_scripts: List[ThirdPartyScript] = []
    forms: List[Form] = []

    # Política de privacidade
    privacy_policy_url: Optional[str] = None   # link para a política
    privacy_policy_text: Optional[str] = None  # texto da política (se encontrado)

    # Consentimento
    consent_banner_detected: bool = False  # existe banner de cookies?

    # Screenshot (opcional)
    screenshot_path: Optional[str] = None  # caminho para a imagem do site