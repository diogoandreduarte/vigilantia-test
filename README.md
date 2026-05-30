# Vigilantia

> Ferramenta de análise automática de websites com foco em conformidade RGPD e boas práticas de privacidade.

## Visão Geral

A **Vigilantia** é uma aplicação Python que recebe um URL, visita o website, recolhe dados relevantes e avalia automaticamente a conformidade com o RGPD. Gera relatórios HTML, PDF e JSON com as não-conformidades detetadas e recomendações de correção.

> **Nota:** a Vigilantia é uma ferramenta de apoio técnico e **não substitui uma auditoria jurídica profissional**.

---

## Funcionalidades

**Módulo de Scraping (João)**
- Recolha de HTML de páginas estáticas e dinâmicas (Playwright)
- Extração de cookies, scripts de terceiros, formulários e links
- Deteção de política de privacidade e banner de consentimento
- Classificação de scripts por categoria (analytics, advertising, social)

**Módulo Analisador RGPD (Diogo)**
- 14 regras RGPD verificadas automaticamente por categoria:
  - Consentimento, Cookies, Scripts de Terceiros, Formulários, Política de Privacidade
- Motor de regras configurável via `rules/gdpr_rules.yaml`
- Análise de texto da política de privacidade (NLP + keyword matching)
- Geração de relatórios HTML, PDF e JSON
- CLI completa com flags para todos os formatos de saída

---

## Tecnologias

| Biblioteca | Finalidade |
|---|---|
| `requests` + `BeautifulSoup4` | Scraping de páginas estáticas |
| `Playwright` | Navegação em páginas com JavaScript |
| `Pydantic` | Validação e estruturação dos dados |
| `PyYAML` | Carregamento das regras RGPD |
| `Jinja2` | Templates HTML para relatórios |
| `WeasyPrint` | Geração de PDF a partir de HTML |
| `langdetect` | Deteção de idioma da política de privacidade |
| `Typer` | Interface de linha de comandos |

---

## Estrutura do Projeto

```text
vigilantia/
├── src/
│   ├── scraper/
│   │   ├── fetcher.py           # HTTP estático
│   │   ├── playwright_fetcher.py# browser dinâmico
│   │   ├── extractor.py         # parsing HTML
│   │   └── collector.py         # orquestração do scraping
│   ├── analyzer/
│   │   ├── rule_engine.py       # motor de regras RGPD
│   │   ├── privacy_text.py      # análise NLP da política
│   │   └── reporter.py          # geração HTML/PDF/JSON
│   ├── models/
│   │   ├── site_data.py         # contrato de dados scraper→analyzer
│   │   └── finding.py           # schema de uma não-conformidade
│   └── cli.py                   # ponto de entrada CLI
├── rules/
│   └── gdpr_rules.yaml          # 14 regras RGPD configuráveis
├── templates/
│   └── report.html.j2           # template do relatório
├── tests/
│   ├── test_rule_engine.py
│   ├── test_reporter.py
│   └── test_cli.py
└── pyproject.toml
```

---

## Fluxo da Aplicação

```mermaid
flowchart TD
    A[Utilizador fornece URL] --> B[Scraper recolhe dados]
    B --> C[SiteData estruturado]
    C --> D[RuleEngine avalia 14 regras RGPD]
    D --> E[Lista de Findings pass/fail]
    E --> F1[Relatório HTML]
    E --> F2[Relatório PDF]
    E --> F3[Resultado JSON]
```

---

## Instalação

```bash
git clone https://github.com/user/vigilantia.git
cd vigilantia
py -3.14 -m venv .venv        # Windows (requer Python 3.14)
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

---

## Utilização da CLI

```bash
python -m src.cli --help
```

A CLI tem dois comandos: `analyze` e `serve`.

### analyze — analisar um site

```
Usage: python -m src.cli analyze [OPTIONS] URL

Options:
  -o, --output PATH    Guardar resultado JSON neste ficheiro
  --html PATH          Gerar relatório HTML neste ficheiro
  --pdf PATH           Gerar relatório PDF neste ficheiro
  -r, --rules PATH     Ficheiro de regras YAML  [default: rules/gdpr_rules.yaml]
  -q, --quiet          Mostrar apenas não-conformidades
  --no-history         Não atualizar o histórico do dashboard
```

### serve — abrir o dashboard localmente

```
Usage: python -m src.cli serve [OPTIONS]

Options:
  -p, --port INT       Porta do servidor  [default: 8080]
  --no-browser         Não abrir o browser automaticamente
```

### Exemplos

Análise rápida (atualiza o dashboard automaticamente se `docs/data/` existir):
```bash
python -m src.cli analyze https://exemplo.com
```

Gerar relatório HTML e guardar JSON:
```bash
python -m src.cli analyze https://exemplo.com --html relatorio.html --output resultado.json
```

Modo silencioso sem atualizar o dashboard:
```bash
python -m src.cli analyze https://exemplo.com --quiet --no-history
```

Abrir o dashboard localmente:
```bash
python -m src.cli serve
# → abre automaticamente http://localhost:8080
```

---

## Dashboard Local

O dashboard (`docs/index.html`) usa `fetch()` e não funciona diretamente com `file://`. É necessário um servidor HTTP.

### Arrancar o servidor

```bash
python -m src.cli serve
```

Abre automaticamente **http://localhost:8080** no browser. Para parar: `Ctrl+C`.

Porta alternativa:
```bash
python -m src.cli serve --port 9000
```

### Popular o dashboard com dados

Cada análise appenda automaticamente ao histórico se `docs/data/` existir:

```bash
python -m src.cli analyze https://sapo.pt --quiet
python -m src.cli analyze https://publico.pt --quiet
python -m src.cli analyze https://dn.pt --quiet
```

Os resultados ficam em `docs/data/<site>.json` e o dashboard atualiza ao recarregar a página.

### Adicionar um site ao manifest

Para que o dashboard carregue um novo site, adiciona o seu ficheiro a `docs/data/manifest.json`:

```json
["sapo_pt.json", "publico_pt.json", "dn_pt.json"]
```

> **Nota:** o manifest tem de ser atualizado manualmente sempre que se adiciona um novo site, tanto em execução local como no GitHub Actions.

### GitHub Pages

Quando o repositório estiver no GitHub, ativa o Pages em **Settings → Pages → Branch: main / Folder: /docs**. O dashboard fica disponível em `https://<username>.github.io/<repo>/` e é atualizado automaticamente pelo workflow `scan.yml`.

---

## Regras RGPD

As regras estão definidas em `rules/gdpr_rules.yaml` e podem ser editadas ou estendidas sem alterar código.

| ID | Categoria | Regra |
|----|-----------|-------|
| RGPD-01 | Consentimento | Banner de consentimento de cookies |
| RGPD-02 | Cookies | Cookies de terceiros sem consentimento |
| RGPD-03 | Cookies | Cookies de tracking sem flag Secure |
| RGPD-04 | Cookies | Cookies de sessão sem flag HttpOnly |
| RGPD-05 | Terceiros | Scripts de analytics sem consentimento |
| RGPD-06 | Terceiros | Scripts de publicidade sem consentimento |
| RGPD-07 | Formulários | Formulários sem aviso de privacidade |
| RGPD-08 | Formulários | Formulários com dados pessoais via GET |
| RGPD-09 | Política | Ausência de link para política de privacidade |
| RGPD-10 | Política | Política não menciona consentimento |
| RGPD-11 | Política | Política não menciona direito ao apagamento |
| RGPD-12 | Política | Política não identifica o responsável pelo tratamento |
| RGPD-13 | Política | Política não menciona contacto do DPO |
| RGPD-14 | Política | Idioma da política diferente do idioma do site |
| RGPD-15 | Política | Política não menciona direito de acesso aos dados |
| RGPD-16 | Política | Política não menciona transferências internacionais |
| RGPD-17 | Política | Política não indica prazo de conservação dos dados |
| RGPD-18 | Formulários | Campo de password sem autocomplete adequado |
| RGPD-19 | Terceiros | Google Analytics Universal sem anonimização de IP |

---

## Testes

```bash
python -m pytest tests/ -v
```

---

## Roadmap

- [x] Estrutura base do projeto
- [x] Scraping estático com `requests`
- [x] Scraping dinâmico com `Playwright`
- [x] Extração de cookies, scripts, formulários e links
- [x] Deteção de política de privacidade e banner de consentimento
- [x] Modelos de dados com Pydantic (`SiteData`, `Finding`)
- [x] 19 regras RGPD configuráveis em YAML
- [x] Motor de regras com avaliadores explícitos por regra
- [x] Análise NLP da política de privacidade
- [x] Geração de relatório HTML e PDF
- [x] CLI completa com Typer
- [x] Testes automáticos (rule engine, reporter, cli)
- [x] CI/CD com GitHub Actions (unit tests + scan semanal)
- [x] Dashboard GitHub Pages com resultados por site
- [x] DISCLAIMER.md (aviso legal obrigatório)
- [x] 5 regras RGPD adicionais (RGPD-15 a 19)
- [x] Gráfico de barras no relatório HTML
- [ ] Análise de múltiplas páginas por domínio
- [x] Dashboard web com histórico de análises ao longo do tempo

---

## Autores

- **João Rêgo** — módulo de scraping (`src/scraper/`, `src/models/site_data.py`)
- **Diogo Duarte** — módulo analisador RGPD (`src/analyzer/`, `src/models/finding.py`, `rules/`, `templates/`, `src/cli.py`)

---

## Aviso

Este projeto foi desenvolvido com fins académicos e de aprendizagem nas áreas de **cibersegurança**, **web scraping** e **privacidade digital**.
