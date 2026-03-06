import asyncio
import sys
import os

# Adiciona o diretório raiz ao path para permitir imports do app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from sqlalchemy import select, delete
from app.core.database import async_session_maker, Base, engine
from app.core.security import get_password_hash
from app.modules.auth.models import User, UserRole
from app.modules.knowledge_base.models import HealthPlan, SOP, SOPStatus, SOPVersion

async def seed_data():
    print("Iniciando semeadura de dados detalhada e limpa (Seed)...")
    async with async_session_maker() as db:
        # 1. Garantir que existe um usuário Admin/Gestor
        result = await db.execute(select(User).where(User.email == "admin@medicore.com"))
        admin = result.scalar_one_or_none()
        
        if not admin:
            print("Criando usuário admin...")
            admin = User(
                email="admin@medicore.com",
                hashed_password=get_password_hash("admin123"),
                full_name="Administrador do Sistema",
                role=UserRole.ADMIN,
                is_active=True
            )
            db.add(admin)
            await db.flush()
        
        # 2. Criar/Atualizar Planos de Saúde com logos corretos
        plans_data = [
            {"name": "UNIMED", "logo_path": "/img/unimed94.png"},
            {"name": "POSTAL SAUDE", "logo_path": "/img/postalsaude94.png"},
            {"name": "CASSI", "logo_path": "/img/cassi94.png"},
            {"name": "AMIL", "logo_path": "/img/abramge94.png"},
            {"name": "IPSEMG", "logo_path": "/img/ipsemg94.png"},
            {"name": "IPSM", "logo_path": "/img/ipsm94.png"},
            {"name": "PARTICULAR PP", "logo_path": "/img/plancel94.png"},
            {"name": "PARTICULAR TOTAL", "logo_path": "/img/plancel94.png"},
        ]
        
        created_plans = {}
        for plan_info in plans_data:
            result = await db.execute(select(HealthPlan).where(HealthPlan.name == plan_info["name"]))
            plan = result.scalar_one_or_none()
            if not plan:
                print(f"Criando plano: {plan_info['name']}...")
                plan = HealthPlan(name=plan_info["name"], logo_path=plan_info["logo_path"])
                db.add(plan)
            else:
                plan.logo_path = plan_info["logo_path"]
            await db.flush()
            created_plans[plan_info["name"]] = plan

        # 2.5 Limpeza PROATIVA de SOPs antigos para estes planos
        plan_ids = [p.id for p in created_plans.values()]
        print(f"Limpando SOPs antigos para os planos: {plan_ids}")
        
        # Primeiro pegamos todos os IDs dos SOPs vinculados a estes planos
        sop_ids_result = await db.execute(select(SOP.id).where(SOP.health_plan_id.in_(plan_ids)))
        sop_ids = sop_ids_result.scalars().all()
        
        if sop_ids:
            # Deletamos as versões primeiro (FK)
            await db.execute(delete(SOPVersion).where(SOPVersion.sop_id.in_(sop_ids)))
            # Deletamos os SOPs
            await db.execute(delete(SOP).where(SOP.id.in_(sop_ids)))
            await db.flush()
            print(f"Removidos {len(sop_ids)} SOPs antigos para garantir dados novos.")
        
        # 3. Criar POPs específicos baseados na documentação
        sops_to_create = [
            {
                "plan": "UNIMED",
                "title": "Protocolo Unimed: Autorização e Guia TISS",
                "content": """
                <h3>1. Requisitos de Autorização</h3>
                <ul>
                    <li><strong>Guia TISS:</strong> Deve ser obrigatoriamente assinada e carimbada pelo médico e pelo secretário (Ref: 4.1.6).</li>
                    <li><strong>Assinaturas:</strong> O paciente ou representante legal deve assinar a guia no campo indicado.</li>
                </ul>
                <h3>2. Exames e Internação</h3>
                <ul>
                    <li><strong>Alto Custo:</strong> Exames de alto custo e pedidos de internação devem ser autorizados via site oficial: <a href="https://unimed.com.br/autorizador" target="_blank">Unimed Autorizador</a> (Ref: 5.5.2).</li>
                </ul>
                """,
                "category": "Faturamento"
            },
            {
                "plan": "POSTAL SAUDE",
                "title": "Protocolo Postal Saúde: TISS e Autorizador",
                "content": """
                <h3>1. Requisitos de Autorização</h3>
                <p>Segue o padrão de Guia TISS devidamente assinada e carimbada (Ref: 5.5.1).</p>
                <h3>2. Procedimentos Complexos</h3>
                <p>Autorização obrigatória no site autorizador da operadora para exames de alto custo e internações (Ref: 5.5.2).</p>
                """,
                "category": "Faturamento"
            },
            {
                "plan": "CASSI",
                "title": "Protocolo CASSI: Fluxo de Autorização",
                "content": """
                <h3>1. Requisitos de Autorização</h3>
                <p>Guia TISS assinada e carimbada conforme normas (Ref: 5.5.1).</p>
                <h3>2. Autorizador Online</h3>
                <p>Utilizar o site autorizador da CASSI para procedimentos que exijam validação prévia (Ref: 5.5.2).</p>
                """,
                "category": "Faturamento"
            },
            {
                "plan": "AMIL",
                "title": "Protocolo AMIL: Elegibilidade e Autorização",
                "content": """
                <h3>1. Requisitos de Autorização</h3>
                <p>Padrão de convênios gerais com Guia TISS assinada e carimbada (Ref: 5.5.1).</p>
                <h3>2. Procedimentos Especiais</h3>
                <p>Sempre realizar a verificação de elegibilidade e autorização online para exames complexos via portal Amil.</p>
                """,
                "category": "Faturamento"
            },
            {
                "plan": "IPSEMG",
                "title": "Protocolo IPSEMG: Assinaturas e Códigos Críticos",
                "content": """
                <h3>1. Assinaturas OBRIGATÓRIAS</h3>
                <ul>
                    <li><strong>Por Extenso:</strong> A guia deve ser assinada por extenso pelo paciente ou responsável. Ex: <i>João da Silva Sauro</i> (não abreviar como J. Silva) (Ref: 2.1.1, 2.3.3).</li>
                    <li><strong>Responsável:</strong> Caso assinado por responsável, incluir CPF e vínculo de parentesco (Ref: 2.2.2).</li>
                </ul>
                <h3>2. Laudo de Consulta</h3>
                <p>Obrigatório carimbo e assinatura do médico com diagnóstico devidamente preenchido (Ref: 2.3).</p>
                <h3>3. Medicações (Prescrição)</h3>
                <ul>
                    <li><strong>Código 15005012:</strong> Soro < 500ml e < 8h.</li>
                    <li><strong>Código 15005013:</strong> Soro > 500ml e < 8h.</li>
                    <li><strong>Código 15005015:</strong> Atendimento > 8h.</li>
                </ul>
                <h3>4. Eletrocardiograma</h3>
                <p>Autorização via site e utilização do código <strong>40101010</strong> lançado manualmente (Ref: 4.5.3, 4.5.4).</p>
                """,
                "category": "IPSEMG"
            },
            {
                "plan": "IPSM",
                "title": "Protocolo IPSM: Guia de Autorização",
                "content": """
                <h3>1. Códigos de Autorização</h3>
                <p>Utilizar obrigatoriamente o código <strong>01010760</strong> para Guia de Autorização (Ref: 2.2.4).</p>
                <h3>2. Carimbos e Assinaturas</h3>
                <p>A guia deve ser carimbada e assinada seguindo rigorosamente as exigências específicas do IPSM (Ref: 5.4.1).</p>
                """,
                "category": "IPSM"
            },
            {
                "plan": "PARTICULAR PP",
                "title": "Protocolo Particular Plancel (PP): Códigos e Fluxo",
                "content": """
                <h3>1. Códigos de Atendimento</h3>
                <ul>
                    <li><strong>Padrão (Código 52):</strong> Particular Plancel como regra geral (Ref: 5.1.1).</li>
                    <li><strong>Urgência/Emergência (Código 17):</strong> Trocar o código em casos confirmados para custeio via convênio (Ref: 5.1.2).</li>
                    <li><strong>Sicoob (Código 58):</strong> Utilizar apenas para titulares (isento de cobrança final) (Ref: 5.1.4).</li>
                </ul>
                <h3>2. Pagamento</h3>
                <p>Conferência detalhada e recebimento do pagamento ao final de todo atendimento (Ref: 5.6.2).</p>
                """,
                "category": "Particular"
            },
            {
                "plan": "PARTICULAR TOTAL",
                "title": "Protocolo Particular Total: Saída e Plantão",
                "content": """
                <h3>1. Códigos e Processo</h3>
                <ul>
                    <li><strong>Códigos:</strong> Utilizar códigos <strong>52</strong> ou <strong>2</strong> (Ref: 5.6.1).</li>
                    <li><strong>Processo de Saída:</strong> Recebimento do pagamento ao final do atendimento e anexação da Nota Fiscal ao registro (Ref: 5.6.3).</li>
                </ul>
                <h3>2. Plantão Noturno</h3>
                <p>A Secretaria é responsável pelo recebimento, emissão de nota e entrega do protocolo para o caixa (Ref: 5.6.4).</p>
                """,
                "category": "Particular"
            }
        ]
        
        for sop_info in sops_to_create:
            plan = created_plans[sop_info["plan"]]
            print(f"Criando POP: {sop_info['title']}...")
            sop = SOP(
                title=sop_info["title"],
                category=sop_info["category"],
                status=SOPStatus.PUBLISHED,
                health_plan_id=plan.id,
                created_by_id=admin.id
            )
            db.add(sop)
            await db.flush()
            
            version = SOPVersion(
                sop_id=sop.id,
                version_number=1,
                content=sop_info["content"],
                change_summary="Especificação técnica detalhada",
                created_by_id=admin.id
            )
            db.add(version)

        await db.commit()
        print("Seed detalhado e limpo concluído com sucesso!")

if __name__ == "__main__":
    asyncio.run(seed_data())
