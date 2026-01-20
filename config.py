🏋️ Sistema de Gestão de Academia – Academia JG

Sistema web desenvolvido em Python (Flask) para gerenciamento de alunos, financeiro e controle de mensalidades de uma academia.

O sistema permite acompanhar alunos ativos, vencimentos, atrasos, pagamentos, relatórios financeiros e comunicação via WhatsApp.

🚀 Funcionalidades
🔐 Autenticação

Login com usuário e senha

Usuário administrador padrão

Sessão protegida

👥 Gestão de Alunos

Cadastro de alunos

Listagem de alunos

Edição e exclusão

Busca por nome

Status automático: Ativo / Vencido

💰 Financeiro

Separação automática de:

Vencendo hoje

Em atraso

Botão de pagamento

Geração de link direto para WhatsApp

Atualização automática de status por data

📊 Dashboard

Total de alunos

Alunos ativos

Alunos em atraso

Alunos vencendo hoje

🧾 Pagamentos

Registro automático de pagamentos

Histórico de pagamentos

Associação com aluno

📄 Relatórios

Relatório mensal por período

Soma total do faturamento

Exportação de relatório em PDF

Gráfico de faturamento por mês

💾 Backup

Backup automático do banco de dados

Backup manual via rota

Mantém os 7 backups mais recentes

🛠️ Tecnologias Utilizadas

Python 3.10+

Flask

SQLite

Jinja2

Bootstrap 5

ReportLab (PDF)

WhatsApp Web API (link direto)

📁 Estrutura do Projeto
academia_jg/
│
├── app.py
├── academia.db
├── backup/
│   └── academia_YYYY-MM-DD_HH-MM-SS.db
│
├── templates/
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── alunos.html
│   ├── listar_alunos.html
│   ├── editar_aluno.html
│   ├── financeiro.html
│   ├── pagar.html
│   ├── pagamentos.html
│   ├── relatorio.html
│   ├── grafico.html
│   └── lista_alunos.html
│
└── static/
    └── (opcional para CSS/JS)

▶️ Como Executar o Projeto
1️⃣ Criar ambiente virtual (opcional)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

2️⃣ Instalar dependências
pip install flask werkzeug reportlab

3️⃣ Executar o sistema
python app.py

4️⃣ Acessar no navegador
http://127.0.0.1:5000

🔑 Usuário Padrão
Usuário	Senha
admin	123

⚠️ Recomenda-se alterar a senha após o primeiro acesso.

🔄 Rotas Principais

/ → Login

/dashboard → Dashboard

/alunos → Cadastro de alunos

/alunos/lista → Lista de alunos

/financeiro → Financeiro

/pagamentos → Histórico de pagamentos

/relatorio → Relatório mensal

/grafico → Gráfico financeiro

/backup_manual → Criar backup manual

📱 WhatsApp

O sistema gera automaticamente links para envio de mensagens via WhatsApp para alunos vencidos ou vencendo, usando o telefone cadastrado.

🧠 Regras de Negócio Importantes

O status do aluno é atualizado automaticamente com base na data de vencimento

Pagamentos renovam o plano por +30 dias

Dashboard, Financeiro e Lista de Alunos usam a mesma lógica de status

O banco de dados é inicializado automaticamente ao rodar o sistema

📌 Observações Finais

Este sistema foi desenvolvido com foco em:

Simplicidade

Estabilidade

Facilidade de manutenção

Uso prático em academias reais

Pronto para evolução futura:

Envio automático de mensagens

Controle de planos diferenciados

Multiusuários

Transformação em aplicativo (PWA)

👨‍💻 Autor

Projeto desenvolvido por Academia JG
Com apoio técnico em Python, Flask