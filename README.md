# Opendce — Sistema de Declaração de Conteúdo Eletrônica (Modelo 99)

Sistema web desenvolvido em Python/FastAPI para emissão, assinatura digital e transmissão de **Declaração de Conteúdo Eletrônica (DC-e - Modelo 99)**, em conformidade com as normas do ENCAT e SEFAZ Virtual do Rio Grande do Sul (SVRS / PR).

---

## 🚀 Como Executar o Sistema

### 1. Pré-requisitos

- [uv](https://docs.astral.sh/uv/) instalado (`powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"` no Windows)
- Python 3.12+ (gerenciado automaticamente pelo `uv`)

### 2. Configurar o Ambiente

Certifique-se de que o arquivo `.env` existe (copiado de `.env.example`):

```bash
cp .env.example .env
```

### 3. Instalar Dependências e Migrar Banco de Dados

```bash
# Instala dependências
uv sync

# Aplica migrações do banco SQLite
uv run alembic upgrade head
```

### 4. Executar os Testes Automatizados

```bash
uv run pytest -v
```

### 5. Iniciar o Servidor de Desenvolvimento

```bash
uv run uvicorn app.main:app --reload --port 7777
```

Acesse no navegador:

- **Painel Web / Dashboard**: [http://localhost:7777/](http://localhost:7777/)
- **Documentação Interativa (Swagger/OpenAPI)**: [http://localhost:7777/docs](http://localhost:7777/docs)
- **Redoc**: [http://localhost:7777/redoc](http://localhost:7777/redoc)

---

## 🐳 Executando com Docker Compose

```bash
docker compose up --build -d
```

---

## 🔒 Certificado Digital e Schemas XSD

1. **Certificado A1 (ICP-Brasil)**:
   - Coloque o certificado `.pfx` em `certs/certificado.pfx`
   - Configure a senha em `DCE_CERT_PASSWORD` no `.env`
2. **Schema XSD**:
   - Coloque o arquivo `DCe_v1.00.xsd` em `schemas/DCe_v1.00.xsd`

---

## 📡 Endpoints Homologação (SVRS — Paraná)

| Serviço            | Endpoint                                                          |
| ------------------ | ----------------------------------------------------------------- |
| Status do Serviço  | `https://homologacao.dce.fazenda.pr.gov.br/dce/DCeStatusServico`  |
| Autorização        | `https://homologacao.dce.fazenda.pr.gov.br/dce/DCeAutorizacao`    |
| Consulta Protocolo | `https://homologacao.dce.fazenda.pr.gov.br/dce/DCeConsulta`       |
| Recepção Evento    | `https://homologacao.dce.fazenda.pr.gov.br/dce/DCeRecepcaoEvento` |
