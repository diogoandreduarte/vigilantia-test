# GetCompanyUrl

Script independente da análise RGPD da Vigilantia. Recebe os dados de uma empresa em JSON (por parâmetro, sem ficheiros) e devolve o site oficial, alguns dados de contacto e informação de DNS/WHOIS do domínio.

Usa pesquisa web (DuckDuckGo), o registo público de empresas Racius.com, e consultas WHOIS diretas.

## Preparar o ambiente (Windows / PowerShell)

Se já correste o `bat\setup.bat` da Vigilantia antes, o ambiente já está pronto — passa à secção seguinte.

Caso contrário, a partir da pasta `vigilantia-main` (`C:\code\vigilantia_diogo`):

```powershell
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
```

Isto instala tudo o que este script precisa (`requests` e `beautifulsoup4`, já incluídos nas dependências da Vigilantia) — não é preciso nenhuma instalação extra específica para o `get_company_url.py`.

Para confirmar que está tudo bem (com o venv já ativado — vês `(.venv)` no início da linha da consola):

```powershell
python scripts\get_company_url.py '{\"company_name\": \"Galp\", \"country\": \"Portugal\"}'
```

## Como executar

A partir da pasta `vigilantia-main`, com o venv ativado:

```powershell
cd C:\code\vigilantia_diogo
python scripts\get_company_url.py '<json com dados da empresa>'
```

Nota sobre aspas no PowerShell: envolve sempre o JSON todo em aspas simples `'...'`, com as aspas internas escapadas com barra invertida (`\"`), como nos exemplos abaixo. Isto é diferente do `cmd.exe` — no PowerShell, aspas simples definem uma string literal, e o `\"` lá dentro é interpretado corretamente ao chamar o `python.exe`.

Alternativa mais segura para nomes com carateres especiais (evita escapar aspas à mão):

```powershell
$json = '{"company_name": "Galp", "country": "Portugal"}'
python scripts\get_company_url.py $json
```

### Campos aceites no JSON de input

| Campo | Obrigatório | Para que serve |
|---|---|---|
| `company_name` | Sim | Nome da empresa a pesquisar |
| `legal_name` | Não | Nome legal completo (ex: "Acme Unipessoal, Lda.") — melhora a precisão da pesquisa e permite validar os dados do Racius |
| `country` | Não | País — ajuda a pesquisa a ser mais específica |
| `address` | Não | Morada conhecida — também usada para validar resultados |

### Exemplo mínimo

```powershell
python scripts\get_company_url.py '{\"company_name\": \"Feedzai\", \"country\": \"Portugal\"}'
```

### Exemplo completo (recomendado para dados fiáveis)

```powershell
python scripts\get_company_url.py '{\"company_name\": \"Feedzai\", \"legal_name\": \"Feedzai - Consultadoria e Inovação Tecnológica, S.A.\", \"country\": \"Portugal\", \"address\": \"Coimbra\"}'
```

## PCM
No caso da PCM é um caso especial, visto que o nome legal da empresa é "Higher Functions" sendo PCM apenas uma marca

```powershell
python scripts\get_company_url.py '{\"company_name\": \"Higher Functions\",  \"country\": \"Portugal\", \"address\": \"fundao\"}'
```

## Exemplos de output

### Cenário 1 — só o nome, sem `legal_name`/`address`

O site é sempre encontrado, mas o Racius (para NIF/morada) só é usado com um aviso: os dados aparecem mas com `"registry_verified": false` e uma nota a explicar porquê.

```powershell
python scripts\get_company_url.py '{\"company_name\": \"Feedzai\", \"country\": \"Portugal\"}'
```

```json
{
  "company_name": "Feedzai",
  "query_used": "Feedzai Portugal official website",
  "url": "https://www.feedzai.com/",
  "domain": "feedzai.com",
  "confidence": "high",
  "nif": "508771862",
  "email": "not available",
  "postal_code": "3030-199 Coimbra",
  "address": "Edifício do Instituto Pedro Nunes, Rua Pedro Nunes - Ipn, 3030-199 Coimbra",
  "registry_verified": false,
  "note": "Dados de nif, postal_code e address não foram confirmados automaticamente (podem existir subsidiárias ou empresas com nome semelhante) — validar manualmente antes de usar.",
  "nameservers": [
    "mary.ns.cloudflare.com",
    "pablo.ns.cloudflare.com"
  ]
}
```

### Cenário 2 — com `legal_name`, dados validados

Quando o `legal_name` (ou `address`) fornecido bate certo com a página do Racius, os dados ficam marcados como confirmados (`"registry_verified": true`) e a nota confirma a origem em vez de avisar.

```powershell
python scripts\get_company_url.py '{\"company_name\": \"Ageas Portugal\", \"legal_name\": \"Ageas Portugal - Companhia de Seguros, S.A.\", \"country\": \"Portugal\"}'
```

```json
{
  "company_name": "Ageas Portugal",
  "query_used": "Ageas Portugal Portugal official website",
  "url": "https://www.ageas.pt/particulares/",
  "domain": "ageas.pt",
  "confidence": "high",
  "nif": "503454109",
  "email": "not available",
  "postal_code": "1990-278 Lisboa",
  "address": "Praça Principe Perfeito, Nº 2, 1990-278 Lisboa",
  "registry_verified": true,
  "note": "Dados de nif, postal_code e address confirmados através do Racius.com (bateram certo com o legal_name/address fornecidos).",
  "nameservers": [
    "ns1.ageas.pt",
    "ns2.ageas.pt"
  ]
}
```

### Cenário 3 — site encontrado mas sem dados extra disponíveis

Quando nem o site oficial nem o Racius têm NIF/morada disponíveis (ou não há dados suficientes para validar em segurança), os campos ficam `"not available"` em vez de arriscar mostrar informação errada. O site (`url`, `domain`, `confidence`) é sempre devolvido quando a pesquisa encontra um candidato.

```json
{
  "company_name": "Sonae",
  "query_used": "Sonae Portugal official website",
  "url": "https://www.sonae.pt/en/",
  "domain": "sonae.pt",
  "confidence": "high",
  "nif": "not available",
  "email": "not available",
  "postal_code": "not available",
  "address": "not available",
  "registry_verified": null,
  "note": "not available",
  "nameservers": [
    "amy.ns.cloudflare.com",
    "rudy.ns.cloudflare.com"
  ]
}
```

## Como ler o output

| Campo | Significado |
|---|---|
| `url`, `domain` | Site oficial encontrado |
| `confidence` | `high` = nome da empresa está no domínio; `medium` = só a morada bateu certo; `low` = pouca confiança, verificar manualmente |
| `nif`, `email`, `postal_code`, `address` | Extraídos do site oficial e, se faltarem, do Racius.com |
| `registry_verified` | `true` = dados do Racius confirmados; `false` = dados do Racius **não confirmados**, podem ser de outra empresa; `null` = Racius nem foi consultado |
| `note` | Explica a origem/fiabilidade dos dados: confirma quando `registry_verified: true`, avisa quando `false`, indica que vieram do site oficial quando `null` com dados, ou `"not available"` quando não há nada a assinalar |
| `nameservers` | Servidores de DNS do domínio, via WHOIS |

**Regra prática:** sempre que `registry_verified` for `false`, tratar `nif`, `postal_code` e `address` como não confirmados e validar manualmente antes de usar os dados.

## Limitações conhecidas

- **Sites que carregam conteúdo via JavaScript** (React, Vue, etc.): o script só lê o HTML inicial do servidor, por isso pode não encontrar links/texto que só aparecem depois do JavaScript correr.
- **Domínios `.pt`**: o WHOIS devolve menos informação do que em domínios `.com` (limitação do próprio registo DNS.pt, não do script).
- **Nomes curtos ou genéricos** (siglas, nomes comuns): maior risco de o Racius devolver a empresa errada — é precisamente para isto que serve o `registry_verified`.
- **Rate-limit do DuckDuckGo**: pesquisas a mais em pouco tempo podem levar a resultados vazios temporariamente — esperar 1-2 minutos resolve.
