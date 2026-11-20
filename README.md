# NexusCorp — Plataforma de Gestão de Reembolsos Corporativos

API REST desenvolvida em Python com FastAPI para gerenciamento de solicitações de reembolso corporativo.

O projeto implementa autenticação, controle de acesso por perfil, validação de regras de negócio, fluxo de aprovação e histórico de operações, utilizando banco de dados relacional.

## 🎓 Objetivo do Projeto

Este projeto foi desenvolvido como parte de uma atividade acadêmica da faculdade, com o objetivo de aplicar, na prática, os conhecimentos adquiridos em desenvolvimento de software, construção de APIs REST, autenticação, controle de acesso, banco de dados e testes de software.

A proposta também serviu como oportunidade de aprofundar conhecimentos em Python e FastAPI, simulando um cenário corporativo de gestão de reembolsos.

**Projeto com finalidade educacional e de aprendizado.**

## Tecnologias utilizadas

- Python
- FastAPI
- SQLAlchemy
- SQLite
- JWT (JSON Web Token)
- PBKDF2-HMAC-SHA256
- Pytest
- Swagger UI

## Funcionalidades

- Autenticação de usuários com JWT.
- Controle de acesso baseado em perfis.
- Cadastro e consulta de solicitações de reembolso.
- Edição e exclusão de solicitações somente enquanto estiverem em rascunho.
- Fluxo de aprovação dividido em etapas.
- Restrição de acesso conforme usuário e departamento.
- Registro do histórico de decisões e responsáveis.
- Validação das regras de negócio.
- Proteção contra tentativas de acesso não autorizado.

## Perfis de acesso

| Perfil | Responsabilidades |
|---|---|
| COLABORADOR | Cadastrar, consultar e gerenciar seus próprios reembolsos enquanto estiverem em rascunho. |
| GESTOR | Analisar solicitações dos colaboradores do próprio departamento. |
| FINANCEIRO | Realizar a aprovação financeira e registrar pagamentos. |
| ADMIN | Gerenciar departamentos e usuários. |

## Fluxo de aprovação

As solicitações seguem o seguinte fluxo:

`RASCUNHO` → `AGUARDANDO_GESTOR` → `AGUARDANDO_FINANCEIRO` → `APROVADA` → `PAGA`

Uma solicitação também pode receber o status `REJEITADA` quando recusada durante uma das etapas de análise.

## Segurança e regras de negócio

A aplicação implementa mecanismos para garantir a integridade das operações:

- Autenticação por tokens JWT.
- Armazenamento de senhas utilizando hash.
- Verificação de permissões conforme o perfil do usuário.
- Restrição de acesso às solicitações de outros colaboradores.
- Validação do departamento responsável pela análise.
- Impedimento de aprovação financeira fora da sequência estabelecida.
- Bloqueio de alterações após o envio da solicitação.
- Registro de histórico com responsável, etapa, decisão e data.
- Validação de informações obrigatórias e referências de comprovantes.

## Testes e homologação

Foram realizados testes funcionais manuais utilizando o Swagger UI para verificar oito cenários:

1. Bloqueio de acesso a solicitações de outros colaboradores.
2. Impedimento de aprovação por gestores de outros departamentos.
3. Rejeição de autenticação com senha incorreta.
4. Bloqueio de tentativas de elevação de privilégios.
5. Impedimento de aprovação financeira fora da sequência.
6. Bloqueio de alterações após o envio da solicitação.
7. Verificação do filtro de solicitações por departamento.
8. Verificação da integridade e disponibilidade do histórico de análise.

Também foi configurado um teste automatizado com Pytest para verificar se a aplicação pode ser importada corretamente.

## Como executar o projeto

### Requisitos

- Python 3.11 ou superior.
- pip.

### 1. Clonar o repositório

```bash
git clone https://github.com/mariajuliatrajano/NexusCorp-Plataforma-Reembolsos.git
```

Entre na pasta:

```bash
cd NexusCorp-Plataforma-Reembolsos
```

### 2. Criar o ambiente virtual

```powershell
python -m venv venv
```

Ative o ambiente no Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar as variáveis de ambiente

Crie o arquivo `.env` utilizando o modelo disponibilizado:

```powershell
Copy-Item .env.example .env
```

Configure as variáveis necessárias no arquivo `.env`, incluindo `ADMIN_INITIAL_PASSWORD` e uma chave JWT própria e segura.

**Importante:** não publique o arquivo `.env` no GitHub, pois ele contém informações privadas.

### 5. Inicializar o banco de dados

```bash
python -m app.seed
```

**Acesso inicial do administrador:**

- E-mail: `admin@nexuscorp.local`
- Senha: definida localmente pela variável `ADMIN_INITIAL_PASSWORD` no arquivo `.env`.

Cada pessoa deverá configurar sua própria senha antes de inicializar o projeto. Não compartilhe nem publique o conteúdo do arquivo `.env`.

### 6. Executar a aplicação

```bash
uvicorn app.main:app --reload
```

A API estará disponível em:

`http://127.0.0.1:8000`

### 7. Acessar a documentação interativa

Acesse:

`http://127.0.0.1:8000/docs`

O Swagger UI permite visualizar os endpoints, realizar autenticações e executar requisições para testar as funcionalidades da API.

Após realizar o login em `/auth/login`, copie o valor de `access_token` e informe-o no campo de autorização do Swagger.

### 8. Executar o teste automatizado

```bash
python -m pytest -q
```

## Estrutura do projeto

```text
nexuscorp_reembolsos/
│
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── security.py
│   └── seed.py
│
├── tests/
│   └── test_rules_outline.py
│
├── .env.example
├── .gitignore
├── README.md
└── requirements.txt
```

## Limitações da versão atual

- Não possui interface gráfica.
- Não possui upload de comprovantes.
- Não realiza integração bancária ou pagamentos reais.
- O histórico é protegido contra alterações pelas rotas HTTP, mas não contra alterações diretas no banco de dados.
- A troca de senha não possui endpoint implementado nesta versão.

---

**NexusCorp | Plataforma de Gestão de Reembolsos Corporativos**