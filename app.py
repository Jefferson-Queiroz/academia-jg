import logging
app = Flask(__name__)
app.secret_key = 'academia_jg_secret'

# LOGS PARA PRODUÇÃO (Render)
logging.basicConfig(level=logging.INFO)

logging.basicConfig(level=logging.INFO)
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask import flash
import sqlite3
from datetime import date, timedelta
from whatsapp import enviar_whatsapp
import json


def gerar_link_whatsapp(telefone, mensagem):
    if not telefone:
        return None

    telefone = telefone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    mensagem = mensagem.replace(" ", "%20")

    return f"https://wa.me/55{telefone}?text={mensagem}"



app = Flask(__name__)
app.secret_key = 'academia_jg_secret'

# --- BANCO DE DADOS ---
def get_db():
    conn = sqlite3.connect('academia.db')
    conn.row_factory = sqlite3.Row
    return conn




def init_db():
    print("✅ init_db EXECUTADO")
    conn = sqlite3.connect('academia.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS funcionarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS alunos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        cpf TEXT,
        telefone TEXT,
        plano TEXT,
        data_pagamento DATE,
        data_vencimento DATE,
        status TEXT
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        aluno_id INTEGER,
        data_pagamento DATE,
        valor REAL,
        plano TEXT,
        FOREIGN KEY (aluno_id) REFERENCES alunos(id)
    )
    ''')

    # cria admin padrão
    cursor.execute("""
        INSERT OR IGNORE INTO funcionarios (usuario, senha)
        VALUES (?, ?)
    """, ('admin', generate_password_hash('123')))

    conn.commit()
    conn.close()



# --- LOGIN ---
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']

        conn = get_db()
        user = conn.execute(
            'SELECT * FROM funcionarios WHERE usuario = ?',
            (usuario,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user['senha'], senha):
            session['usuario'] = usuario
            return redirect(url_for('dashboard'))

        flash('Usuário ou senha inválidos', 'erro')

    return render_template('login.html')



# --- DASHBOARD ---
@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    atualizar_status_vencidos()

    hoje = date.today().isoformat()
    conn = get_db()

    total_alunos = conn.execute(
        'SELECT COUNT(*) FROM alunos'
    ).fetchone()[0]

    ativos = conn.execute(
        'SELECT COUNT(*) FROM alunos WHERE status = "Ativo"'
    ).fetchone()[0]

    atrasados = conn.execute(
        'SELECT COUNT(*) FROM alunos WHERE status = "Vencido"'
    ).fetchone()[0]

    vencem_hoje = conn.execute(
        'SELECT COUNT(*) FROM alunos WHERE data_vencimento = ?',
        (hoje,)
    ).fetchone()[0]

    conn.close()

    return render_template(
        'dashboard.html',
        total=total_alunos,
        ativos=ativos,
        atrasados=atrasados,
        vencem_hoje=vencem_hoje
    )


# --- FINANCEIRO ---
@app.route('/financeiro')
def financeiro():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    atualizar_status_vencidos()

    hoje = date.today().isoformat()
    conn = get_db()

    # Vencendo hoje
    vencendo = conn.execute("""
        SELECT * FROM alunos
        WHERE data_vencimento = ?
    """, (hoje,)).fetchall()

    # Em atraso
    atrasados = conn.execute("""
        SELECT * FROM alunos
        WHERE status = 'Vencido'
    """).fetchall()

    conn.close()

    def montar_lista(alunos):
        lista = []
        for a in alunos:
            msg = f"Olá {a['nome']}, sua mensalidade está pendente. Entre em contato para regularizar."
            lista.append(dict(a) | {
                "whatsapp": gerar_link_whatsapp(a['telefone'], msg)
            })
        return lista

    return render_template(
        'financeiro.html',
        vencendo=montar_lista(vencendo),
        atrasados=montar_lista(atrasados)
    )




# --- PAGAR MENSALIDADE ---
@app.route('/pagar/<int:id>', methods=['GET', 'POST'])
def pagar(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    aluno = conn.execute(
        'SELECT * FROM alunos WHERE id = ?',
        (id,)
    ).fetchone()

    if request.method == 'POST':
        valor = float(request.form['valor'])
        hoje = date.today()
        nova_data = hoje + timedelta(days=30)
        try:
            conn.execute('''
            INSERT INTO pagamentos (aluno_id, data_pagamento, valor, plano)
            VALUES (?, ?, ?, ?)
            ''', (
            aluno['id'],
            hoje.isoformat(),
            valor,
            aluno['plano']
        ))

        conn.execute('''
            UPDATE alunos
            SET data_pagamento = ?, data_vencimento = ?, status = 'Ativo'
            WHERE id = ?
        ''', (hoje.isoformat(), nova_data.isoformat(), id))

        conn.commit()
        conn.close()
        return redirect(url_for('financeiro'))
    
    except Exception as e:
        conn.rollback()
        app.logger.error(f"Erro ao cadastrar aluno: {e}")
        flash("Erro ao salvar aluno. Tente novamente.", "danger")
        return redirect(url_for('alunos'))
    finally:
        conn.close()

    return render_template('pagar.html', aluno=aluno)



# --- CADASTRO DE ALUNOS ---
from datetime import date, timedelta

@app.route('/alunos', methods=['GET', 'POST'])
def alunos():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    if request.method == 'POST':
        try:
            hoje = date.today()
            vencimento = hoje + timedelta(days=30)
            valor = float(request.form['valor'])

            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO alunos (nome, cpf, telefone, plano, data_pagamento, data_vencimento, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                request.form['nome'],
                request.form['cpf'],
                request.form['telefone'],
                request.form['plano'],
                hoje.isoformat(),
                vencimento.isoformat(),
                'Ativo'
            ))

            aluno_id = cursor.lastrowid

            cursor.execute('''
                INSERT INTO pagamentos (aluno_id, data_pagamento, valor, plano)
                VALUES (?, ?, ?, ?)
            ''', (
                aluno_id,
                hoje.isoformat(),
                valor,
                request.form['plano']
            ))

            conn.commit()
            return redirect(url_for('lista_alunos'))

        except Exception as e:
            conn.rollback()
            app.logger.error(f"❌ Erro ao cadastrar aluno: {e}")
            flash("Erro ao cadastrar aluno. Verifique os dados.", "danger")
            return redirect(url_for('alunos'))

        finally:
            conn.close()
            
        app.logger.info("📌 Tentando cadastrar aluno")

    conn.close()
    return render_template('alunos.html')

# --- ALUNOS/LISTA ---
@app.route('/alunos/lista')
def lista_alunos():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    busca = request.args.get('busca')

    if busca:
        alunos = conn.execute(
            "SELECT * FROM alunos WHERE nome LIKE ? ORDER BY nome",
            (f"%{busca}%",)
        ).fetchall()
    else:
        alunos = conn.execute(
            "SELECT * FROM alunos ORDER BY nome"
        ).fetchall()

    conn.close()

    alunos_formatados = []

    for a in alunos:
        telefone = a['telefone'] or ''
        whatsapp = (
            "https://wa.me/55" +
            telefone.replace("(", "").replace(")", "")
                    .replace("-", "").replace(" ", "")
        )

        alunos_formatados.append({
            'id': a['id'],
            'nome': a['nome'],
            'telefone': telefone,
            'plano': a['plano'],
            'status': a['status'],
            'whatsapp': whatsapp
        })

    return render_template(
        'lista_alunos.html',
        alunos=alunos_formatados
    )




# --- PAGAMENTOS ---
@app.route('/pagamentos')
def pagamentos():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    pagamentos = conn.execute('''
        SELECT pagamentos.*, alunos.nome
        FROM pagamentos
        JOIN alunos ON pagamentos.aluno_id = alunos.id
        ORDER BY data_pagamento DESC
    ''').fetchall()
    conn.close()

    return render_template('pagamentos.html', pagamentos=pagamentos)

# --- ATUALIZAR STATUS VENCIDOS ---
def atualizar_status_vencidos():
    hoje = date.today().isoformat()
    conn = get_db()

    # alunos vencidos
    conn.execute("""
        UPDATE alunos
        SET status = 'Vencido'
        WHERE data_vencimento < ?
    """, (hoje,))

    # alunos ativos
    conn.execute("""
        UPDATE alunos
        SET status = 'Ativo'
        WHERE data_vencimento >= ?
    """, (hoje,))

    conn.commit()
    conn.close()


# --- RELATÓRIO ---
@app.route('/relatorio', methods=['GET', 'POST'])
def relatorio():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    mes = request.form.get('mes')

    if mes:
        pagamentos = conn.execute('''
            SELECT pagamentos.*, alunos.nome
            FROM pagamentos
            JOIN alunos ON pagamentos.aluno_id = alunos.id
            WHERE strftime('%Y-%m', pagamentos.data_pagamento) = ?
        ''', (mes,)).fetchall()

        total = conn.execute('''
            SELECT SUM(valor)
            FROM pagamentos
            WHERE strftime('%Y-%m', pagamentos.data_pagamento) = ?
        ''', (mes,)).fetchone()[0]
    else:
        pagamentos = []
        total = 0

    conn.close()

    return render_template(
        'relatorio.html',
        pagamentos=pagamentos,
        total=total or 0,
        mes=mes
    )

# --- GRáFICO ---
@app.route('/grafico')
def grafico():
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    cur = conn.cursor()

    # Faturamento agrupado por mês
    cur.execute("""
        SELECT 
            strftime('%Y-%m', data_pagamento) AS mes,
            SUM(valor) AS total
        FROM pagamentos
        GROUP BY mes
        ORDER BY mes
    """)
    dados = cur.fetchall()

    conn.close()

    # Transformar em listas (JSON-friendly)
    meses = [linha['mes'] for linha in dados]
    totais = [linha['total'] for linha in dados]

    return render_template(
        'grafico.html',
        meses=meses,
        totais=totais
    )


from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from flask import send_file
import os


from flask import send_file
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import io

# --- RELATÓRIO_PDF
@app.route('/relatorio/pdf/<mes>')
def relatorio_pdf(mes):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conn = get_db()
    pagamentos = conn.execute('''
        SELECT pagamentos.*, alunos.nome
        FROM pagamentos
        JOIN alunos ON pagamentos.aluno_id = alunos.id
        WHERE strftime('%Y-%m', pagamentos.data_pagamento) = ?
    ''', (mes,)).fetchall()

    total = conn.execute('''
        SELECT SUM(valor)
        FROM pagamentos
        WHERE strftime('%Y-%m', data_pagamento) = ?
    ''', (mes,)).fetchone()[0] or 0

    conn.close()

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, f"Relatório Financeiro - {mes}")

    y -= 30
    pdf.setFont("Helvetica", 10)

    for p in pagamentos:
        linha = f"{p['data_pagamento']} - {p['nome']} - R$ {p['valor']:.2f}"
        pdf.drawString(50, y, linha)
        y -= 20
        if y < 50:
            pdf.showPage()
            y = height - 50

    y -= 20
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, f"TOTAL: R$ {total:.2f}")

    pdf.save()
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"relatorio_{mes}.pdf",
        mimetype='application/pdf'
    )

# ---EDITAR ALUNO---
@app.route('/alunos/editar/<int:id>', methods=['GET', 'POST'])
def editar_aluno(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))

    conn = get_db()

    if request.method == 'POST':
        try:
        conn.execute('''
            UPDATE alunos
            SET nome=?, cpf=?, telefone=?, plano=?, data_pagamento=?, data_vencimento=?
            WHERE id=?
        ''', (
            request.form['nome'],
            request.form['cpf'],
            request.form['telefone'],
            request.form['plano'],
            request.form['data_pagamento'],
            request.form['data_vencimento'],
            id
        ))
        conn.commit()
        conn.close()
        return redirect(url_for('lista_alunos'))
    
    except Exception as e:
    conn.rollback()
    app.logger.error(f"Erro ao cadastrar aluno: {e}")
    flash("Erro ao salvar aluno. Verifique os dados.", "danger")
    return redirect(url_for('alunos'))

    finally:
    conn.close()


    aluno = conn.execute(
        'SELECT * FROM alunos WHERE id=?', (id,)
    ).fetchone()
    conn.close()

    return render_template('editar_aluno.html', aluno=aluno)


# --- REMOVER ALUNO ---
@app.route('/alunos/excluir/<int:id>')
def excluir_aluno(id):
    if 'usuario' not in session:
        return redirect(url_for('login'))
try:
    conn = get_db()
    conn.execute('DELETE FROM alunos WHERE id=?', (id,))
    conn.commit()
    conn.close()

    return redirect(url_for('lista_alunos'))

except Exception as e:
    conn.rollback()
    app.logger.error(f"Erro ao cadastrar aluno: {e}")
    flash("Erro ao salvar aluno. Verifique os dados.", "danger")
    return redirect(url_for('alunos'))

finally:
    conn.close()

# --- LOGOUT ---
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- temporary: debug admin users ---
@app.route('/debug_admin')
def debug_admin():
    conn = get_db()
    usuarios = conn.execute(
        "SELECT id, usuario, senha FROM funcionarios"
    ).fetchall()
    conn.close()

    return str([dict(u) for u in usuarios])

# --RESET ADMIN ---
@app.route('/reset_admin')
def reset_admin():
    from werkzeug.security import generate_password_hash
    conn = get_db()
    conn.execute(
        "UPDATE funcionarios SET senha = ? WHERE usuario = ?",
        (generate_password_hash("123"), "admin")
    )
    conn.commit()
    conn.close()
    return "Senha do admin redefinida para 123"

# --- BACKUP DO BANCO DE DADOS ---
import os
import shutil
from datetime import datetime

def backup_banco():
    if not os.path.exists("backup"):
        os.makedirs("backup")

    data = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nome_backup = f"backup/academia_{data}.db"

    if os.path.exists("academia.db"):
        shutil.copy("academia.db", nome_backup)
        print(f"✅ Backup criado: {nome_backup}")

    # manter apenas os 7 backups mais recentes
    backups = sorted(
        [f for f in os.listdir("backup") if f.endswith(".db")]
    )

    if len(backups) > 7:
        antigos = backups[:-7]
        for arquivo in antigos:
            os.remove(os.path.join("backup", arquivo))
            print(f"🗑 Backup antigo removido: {arquivo}")


# --- ROTA PARA CRIAR BACKUP MANUALMENTE ---            
@app.route('/backup_manual')
def backup_manual():
    backup_banco()
    return "Backup criado com sucesso"


@app.errorhandler(500)
def erro_500(e):
    return render_template(
        "erro.html",
        titulo="Erro interno",
        mensagem="Ocorreu um erro inesperado. Nossa equipe já foi notificada."
    ), 500

@app.errorhandler(404)
def erro_404(e):
    return render_template(
        "erro.html",
        titulo="Página não encontrada",
        mensagem="O endereço acessado não existe."
    ), 404
    
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"🔥 ERRO GLOBAL: {e}", exc_info=True)
    return "Erro interno no servidor. Verifique os logs.", 500


if __name__ == "__main__":
    init_db()
    backup_banco()
    app.run()



