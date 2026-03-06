# Project Name: MediCore - Central de Conhecimento e Operações Hospitalares


## 0. Instruções Gerais
Ativar o ambiente virtual: venv\Scripts\activate
Instalar dependências com proxy: pip install --proxy http://hcl:hcl@192.168.1.3:3128

## 1. Visão do Produto
Desenvolvimento de uma plataforma centralizada para gestão de conhecimento (POPs), padronização de processos e onboarding de novos funcionários em setores hospitalares (inicialmente Ala/Secretaria).
O sistema foca em alta confiabilidade, auditoria de leitura e suporte via Chat, com arquitetura preparada para futura integração com Inteligência Artificial (RAG).

**Objetivo Principal:** Eliminar ruído de comunicação, garantir que procedimentos sejam seguidos e agilizar o treinamento de novos colaboradores.

---

## 2. Stack Tecnológica

### Backend (API REST)
*   **Linguagem:** Python 3.11+
*   **Framework:** FastAPI (Async)
*   **ORM:** SQLAlchemy 2.0 (Async)
*   **Validação:** Pydantic v2
*   **Real-time:** WebSockets (Nativo FastAPI)
*   **Task Queue (Futuro):** Celery + Redis (para processamento de embeddings IA)

### Banco de Dados
*   **SGBD:** PostgreSQL 15+
*   **Extensões:**
    *   `pgvector` (Preparação para IA/Busca Semântica)
    *   `pg_trgm` (Busca textual eficiente)
*   **Migrations:** Alembic

### Frontend (SPA)
*   **Framework:** React 18+ com TypeScript
*   **Build Tool:** Vite
*   **State Management:** TanStack Query (React Query) + Zustand
*   **UI Library:** Mantine UI ou Material UI (Foco em interfaces administrativas limpas)
*   **Editor de Texto:** Tiptap ou Quill (Rich Text com suporte a output JSON/Markdown)

### Infraestrutura
*   **Containerização:** Docker & Docker Compose

---

## 3. Requisitos Funcionais

### Módulo 1: Gestão de Conhecimento (POPs)
*   **Criação Centralizada (RBAC):** Apenas usuários com perfil `Gestor/Admin` podem criar, editar e arquivar Procedimentos Operacionais Padrão (POPs).
*   **Versionamento de Documentos:**
    *   Todo `UPDATE` em um POP gera uma nova `Version`.
    *   O histórico de versões deve ser acessível.
    *   Capacidade de reverter para versões anteriores.
*   **Leitura e Aceite (Compliance):**
    *   Usuários `Colaboradores` têm acesso de leitura.
    *   **Botão "Li e Estou Ciente":** Registra data, hora e versão do documento lido (Auditoria).
*   **Busca:** Pesquisa Full-Text pelo título e conteúdo do procedimento.

### Módulo 2: Onboarding & Trilhas
*   **Playlists de Treinamento:** Agrupamento de POPs em uma ordem lógica (ex: "Dia 1 - Admissão").
*   **Barra de Progresso:** Visualização de quantos % do treinamento o funcionário completou.

### Módulo 3: Chat & Suporte (Escalável para IA)
*   **Fase 1 (Atual):** Chat via WebSockets entre Colaborador e Gestor (Ticket/Dúvida em tempo real).
*   **Fase 2 (Futuro):** Bot de IA que intercepta a pergunta, busca nos embeddings dos POPs e sugere a resposta antes de acionar o humano.

---

## 4. Arquitetura de Software

Adotaremos uma **Arquitetura Modular (Modular Monolith)**. O código será organizado por *Domínios de Negócio* e não apenas por camadas técnicas.

### Estrutura de Diretórios Sugerida

```text
medicore-backend/
├── app/
│   ├── core/                   # Configs globais, Security, Middleware, Logs
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py         # Configuração do AsyncSession
│   │
│   ├── modules/                # Módulos de Negócio (Domínios)
│   │   ├── auth/               # Login, Users, Permissions
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   └── models.py
│   │   │
│   │   ├── knowledge_base/     # Gestão dos POPs e Leituras
│   │   │   ├── router.py
│   │   │   ├── schemas.py      # Pydantic Models (CreateSOP, ReadSOP)
│   │   │   ├── service.py      # Regra de Negócio (Versioning logic)
│   │   │   └── models.py       # SQLAlchemy Models (SOP, SOPVersion)
│   │   │
│   │   └── chat/               # WebSockets e Histórico
│   │       ├── router.py       # WS Endpoints
│   │       ├── manager.py      # Connection Manager (WebSockets)
│   │       └── models.py
│   │
│   └── main.py                 # Entrypoint (App init)
│
├── alembic/                    # Migrações de Banco
├── tests/                      # Testes (Pytest)
├── requirements.txt
└── docker-compose.yml

---

## 5. Próximos Passos (Roadmap Atual)

### ✅ Fase 1: Telas de Autenticação no Frontend (Concluída)
1. ~~Tela de Login~~
2. ~~Tela de Cadastro~~
3. ~~Tela de Recuperação de Senha (ForgotPassword + ResetPassword)~~

### ✅ Fase 2: Testes de Autenticação no Backend (Concluída)
1. ~~Testes para a rota de Login~~
2. ~~Testes para a rota de Cadastro~~
3. ~~Testes para a rota de Recuperação de Senha~~

### ✅ Fase 3: Testes de Casos de Uso no Frontend (Concluída)
1. ~~Testes automatizados para a Tela de Login (5 testes)~~
2. ~~Testes automatizados para a Tela de Cadastro (5 testes)~~
3. ~~Testes automatizados para a Tela de Recuperação de Senha (4 testes)~~

### ✅ Fase 4: Planos de Saúde (Convênios) e POPs (Concluída)
1. **Backend:**
    - Modelo `HealthPlan` (Nome, Logo, Ativo) vinculado ao `SOP`.
    - Migração unificada e compatível com SQLite (`current_timestamp`).
    - API: Listagem de convênios, detalhes e filtragem de POPs por convênio.
    - Script de Seed: 8 convênios cadastrados com protocolos específicos.
2. **Frontend:**
    - Tela de Listagem de Convênios (Grid de Cards com logos).
    - Tela de Detalhes do Convênio (Lista de POPs relacionados).
    - Navegação via Sidebar integrada.
3. **Verificação:**
    - Testes de backend para rotas de `health-plans` (4 testes passando).

### 🚀 Próximas Fases (Propostas)

#### ✅ Fase 5: Infraestrutura e Preparação para Deploy (Concluída)
1. **Dockerização:**
    - Criado `Dockerfile` multi-stage para o Frontend (Vite + Nginx).
    - Atualizado `Dockerfile` do Backend com `curl` e suporte a comandos de produção.
    - `docker-compose.yml` agora inclui o frontend e healthchecks para os serviços.
2. **Dependências:**
    - `requirements.txt` atualizado com `gunicorn` e ferramentas de teste (`pytest`, `httpx`).
3. **Monitoramento:**
    - Implementado endpoint `/health` no backend para validação automática de status.

#### 🔄 Fase 6: Onboarding & Trilhas (A Iniciar)
1. **Backend:** WebSocket manager e modelo de mensagens.
2. **Frontend:** Interface de chat flutuante ou página dedicada.


