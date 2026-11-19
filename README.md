# NexusCorp — Plataforma de Gestão de Reembolsos

API REST em Python com FastAPI, SQLAlchemy e banco relacional. SQLite é o padrão para execução local; também é possível configurar uma URL de banco compatível com SQLAlchemy, como MySQL.

## Requisitos
- Python 3.11 ou superior
- pip

## Instalação no Windows (PowerShell)
```powershell
py -m venv venv
.env\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python -m app.seed
uvicorn app.main:app --reload
```
Abra `http://127.0.0.1:8000/docs` para consultar e testar a documentação interativa.

## Primeiro acesso
- E-mail: `admin@nexuscorp.local`
- Senha: `TroqueEstaSenha123!`

A senha é apenas para inicialização local. Troque-a e substitua `JWT_SECRET_KEY` antes de qualquer uso real. O projeto não possui endpoint de troca de senha nesta versão; a troca deve ser feita administrativamente no banco ou implementada antes de produção.

## Configuração de banco
Edite `DATABASE_URL` no `.env`. Exemplo SQLite:
`sqlite:///./nexuscorp.db`

Exemplo MySQL (instale também o driver `pymysql` e use `mysql+pymysql://usuario:senha@localhost/nexuscorp`):
`mysql+pymysql://usuario:senha@localhost/nexuscorp`

## Fluxo rápido
1. Faça login em `/auth/login`.
2. Clique em Authorize no Swagger e informe `Bearer SEU_TOKEN`.
3. Admin cria departamentos em `/departments` e usuários em `/users`.
4. Colaborador cria em `/reimbursements`, depois chama `/submit`.
5. Gestor chama `/manager-decision` com observação iniciada por `APROVAR:` ou `RECUSAR:`.
6. Financeiro chama `/finance-decision` e, se aprovar, `/payment`.
7. Consulte `/history` para auditar as decisões.

## Testes
```powershell
pytest -q
```
O teste incluído verifica a presença dos oito cenários no roteiro de homologação. O documento `docs/HOMOLOGACAO.md` descreve os testes funcionais manuais e resultados esperados; execute-os na API para produzir evidências reais.

## Estrutura
- `app/`: API, modelos, schemas, autenticação e seed.
- `docs/DOCUMENTACAO_TECNICA.md`: documentação solicitada.
- `docs/HOMOLOGACAO.md`: roteiro dos oito cenários.
- `tests/`: testes automatizados básicos.

## Limitações desta primeira versão
Sem interface gráfica, upload de comprovantes ou pagamento bancário real, conforme o enunciado. O papel ADMIN é administrativo e não substitui os três perfis operacionais. A API usa histórico append-only na camada HTTP, mas um administrador do banco ainda pode alterar dados diretamente; em produção, restrinja credenciais do banco e considere auditoria imutável externa.
