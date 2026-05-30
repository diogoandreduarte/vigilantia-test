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

    priority_keywords = [
        "privacy policy", "política de privacidade",
        "politica de privacidade", "privacy", "privacidade",
    ]
    secondary_keywords = [
        "cookies", "termos", "terms",
        "proteção de dados", "protecao de dados",
    ]

    candidates = []
    for a in soup.find_all("a", href=True):
        link_text = a.get_text(strip=True).lower()
        href = a["href"].lower()
        for kw in priority_keywords:
            if kw in link_text or kw in href:
                return a["href"]
        for kw in secondary_keywords:
            if kw in link_text or kw in href:
                candidates.append(a["href"])

    return candidates[0] if candidates else None


def extract_page_language(html: str) -> str:
    """Extrai idioma do atributo lang da tag <html>."""
    soup = BeautifulSoup(html, "html.parser")
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        return html_tag["lang"].split("-")[0].lower()
    return "unknown"
