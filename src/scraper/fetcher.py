import requests


def fetch_page(url: str) -> dict:
    """Fetcher estático via requests — usado como fallback para sites sem JavaScript."""
    try:
        session = requests.Session()
        response = session.get(
            url,
            timeout=15,
            headers={"User-Agent": "Vigilantia/1.0 (+academic project RGPD scanner)"},
        )
        response.raise_for_status()

        cookies = [
            {
                "name": c.name,
                "domain": c.domain or "",
                "path": c.path,
                "secure": c.secure,
                "httpOnly": False,
                "sameSite": None,
            }
            for c in session.cookies
        ]

        return {
            "html": response.text,
            "final_url": str(response.url),
            "cookies": cookies,
            "consent_banner_detected": False,
        }

    except requests.RequestException as e:
        raise Exception(f"Erro ao aceder ao site: {e}")
