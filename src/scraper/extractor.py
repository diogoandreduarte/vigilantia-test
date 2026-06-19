import re
from bs4 import BeautifulSoup

_PRIVACY_KEYWORDS = re.compile(
    r"privacidade|privacy|rgpd|gdpr|proteção de dados|data protection|"
    r"política de dados|tratamento de dados|consentimento",
    re.IGNORECASE,
)


def extract_links(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    return [a["href"] for a in soup.find_all("a", href=True)]


def extract_scripts(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    return [s["src"] for s in soup.find_all("script", src=True)]


def _form_has_privacy_notice(form_tag) -> bool:
    # Procura aviso de privacidade no container do formulário e nos seus vizinhos
    container = form_tag.parent or form_tag
    container_text = container.get_text(" ", strip=True)
    if _PRIVACY_KEYWORDS.search(container_text):
        return True
    # Checkbox de consentimento dentro do form
    for inp in form_tag.find_all("input", type=re.compile(r"checkbox", re.I)):
        label_text = ""
        if inp.get("id"):
            label = form_tag.find("label", attrs={"for": inp["id"]})
            if label:
                label_text = label.get_text()
        if _PRIVACY_KEYWORDS.search(label_text) or _PRIVACY_KEYWORDS.search(inp.get("name", "")):
            return True
    # Link para política dentro do form
    for a in form_tag.find_all("a", href=True):
        if _PRIVACY_KEYWORDS.search(a.get_text()) or _PRIVACY_KEYWORDS.search(a["href"]):
            return True
    return False


def _password_autocomplete_ok(form_tag) -> bool:
    for inp in form_tag.find_all("input", type=re.compile(r"password", re.I)):
        autocomplete = (inp.get("autocomplete") or "").lower()
        if autocomplete not in ("new-password", "current-password", "off"):
            return False
    return True


def extract_forms(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    forms = []
    for form in soup.find_all("form"):
        fields = [
            f.get("name") for f in form.find_all(["input", "textarea", "select"])
            if f.get("name")
        ]
        forms.append({
            "action": form.get("action"),
            "method": form.get("method", "GET").upper(),
            "fields": fields,
            "has_privacy_notice": _form_has_privacy_notice(form),
            "password_autocomplete_ok": _password_autocomplete_ok(form),
        })
    return forms


def find_privacy_policy_link(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")

    # Texto exato do link (score mais alto)
    exact_text = [
        "política de privacidade", "politica de privacidade",
        "privacy policy", "aviso de privacidade",
        "declaração de privacidade", "declaracao de privacidade",
        "aviso legal e privacidade",
    ]
    # href contém estes padrões (score alto)
    href_patterns = [
        "politica-de-privacidade", "politica_de_privacidade",
        "privacy-policy", "privacypolicy", "privacy_policy",
        "aviso-privacidade", "aviso-legal",
    ]
    # Fallback: qualquer link com menção genérica
    fallback_text = ["privacidade", "privacy"]
    fallback_href = ["privacidade", "privacy", "cookies", "protecao-de-dados", "rgpd", "gdpr"]
    fallback_text_secondary = ["cookies", "termos", "terms", "proteção de dados", "protecao de dados"]

    # 1. Texto do link corresponde exatamente
    for a in soup.find_all("a", href=True):
        if a.get_text(strip=True).lower() in exact_text:
            return a["href"]

    # 2. Texto contém frase específica
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True).lower()
        if any(kw in text for kw in exact_text):
            return a["href"]

    # 3. href contém padrão específico
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        if any(p in href for p in href_patterns):
            return a["href"]

    # 4. Texto ou href com menção genérica a privacidade
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True).lower()
        href = a["href"].lower()
        if any(kw in text for kw in fallback_text) or any(kw in href for kw in fallback_href):
            return a["href"]

    # 5. Último recurso: cookies/termos
    for a in soup.find_all("a", href=True):
        text = a.get_text(strip=True).lower()
        if any(kw in text for kw in fallback_text_secondary):
            return a["href"]

    return None


def extract_page_language(html: str) -> str:
    """Extrai idioma do atributo lang da tag <html>."""
    soup = BeautifulSoup(html, "html.parser")
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        return html_tag["lang"].split("-")[0].lower()
    return "unknown"
