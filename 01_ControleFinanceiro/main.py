import os
import re
import threading
import smtplib
import logging

import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from nicegui import app, ui
from supabase import create_client, Client
from dotenv import load_dotenv

# Silencia avisos inofensivos de desconexão de socket no terminal
logging.getLogger("asyncio").setLevel(logging.CRITICAL)

def formatar_br(valor) -> str:
    try:
        val = float(valor or 0)
        return f"{val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ValueError, TypeError):
        return "0,00"

# Carrega as variáveis do arquivo .env
load_dotenv()

# --- CONFIGURAÇÕES ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://mpqkefsjclczhhjhirgt.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

ADMIN_EMAIL = "w.batista.brasileiro@gmail.com"
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASS = os.getenv("GMAIL_APP_PASS")

MESES_NOMES = {
    1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
    7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
}

MESES_SIGLAS = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']


def email_valido(email_str: str) -> bool:
    return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email_str.strip()))

def obter_hora_brasilia():
    return datetime.now(ZoneInfo("America/Sao_Paulo"))

def _enviar_email_worker(solicitante_email, dispositivo, localizacao):
    try:
        data_hora_br = obter_hora_brasilia().strftime('%d/%m/%Y às %H:%M:%S')
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Controle Financeiro - Solicitação de acesso: {solicitante_email}"
        msg["From"] = f"Controle Financeiro <{GMAIL_USER}>"
        msg["To"] = ADMIN_EMAIL

        corpo_html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; padding: 20px; color: #333;">
            <h2 style="color: #1e40af;">🔔 Nova Solicitação de Acesso</h2>
            <ul>
              <li><b>E-mail:</b> {solicitante_email}</li>
              <li><b>Data/Hora:</b> {data_hora_br}</li>
              <li><b>Localização:</b> {localizacao}</li>
              <li><b>Dispositivo:</b> {dispositivo}</li>
            </ul>
          </body>
        </html>
        """
        msg.attach(MIMEText(corpo_html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASS)
            server.sendmail(GMAIL_USER, ADMIN_EMAIL, msg.as_string())
    except Exception as e:
        print(f"❌ Erro e-mail: {e}")

def enviar_notificacao_email(solicitante_email, dispositivo, localizacao):
    threading.Thread(target=_enviar_email_worker, args=(solicitante_email, dispositivo, localizacao), daemon=True).start()

# --- HELPER DE VALIDAÇÃO DE OCORRÊNCIA MENSAL ---
def receita_ocorre_no_mes_ano(rec: dict, mes: int, ano: int) -> bool:
    ano_ini = int(rec.get('ano_inicio') or 2025)
    ano_fim = int(rec.get('ano_fim') or 2200)
    meses_str = str(rec.get('meses') or '')

    if not (ano_ini <= ano <= ano_fim):
        return False
        
    # Garante correspondência exata do mês (ex: ".11.")
    return f".{mes}." in meses_str


# --- MENU DRAWER & CABEÇALHO ---
def menu_drawer():
    user_email = app.storage.user.get('email', '')

    with ui.left_drawer(value=False).classes('bg-slate-50 text-slate-800 p-0 flex flex-col justify-between w-64 border-r border-slate-200 shadow-lg') as drawer:

        # Função auxiliar para fechar o menu e navegar para a rota
        def navegar(rota):
            drawer.hide()
            ui.navigate.to(rota)

        # --- TOPO: LOGO & EMAIL ---
        with ui.column().classes('w-full p-5 border-b border-slate-200 gap-1 bg-white'):
            with ui.row().classes('items-center gap-2'):
                ui.icon('account_balance_wallet', size='28px').classes('text-blue-600')
                ui.label('Menu').classes('text-xl font-bold tracking-wide text-slate-900')
            ui.label(user_email if user_email else 'Minha Conta').classes('text-xs text-slate-500 truncate max-w-full font-medium')

        # --- CORPO: NAVEGAÇÃO ---
        with ui.column().classes('w-full p-4 gap-5 flex-1 overflow-y-auto'):

            # --- SEÇÃO 1: EXECUÇÃO ---
            with ui.column().classes('w-full gap-1'):
                ui.label('MONITORAMENTO').classes('text-[10px] font-bold tracking-wider text-slate-400 uppercase px-3 mb-1')

                # Saúde Financeira
                ui.button(
                    'Saúde Financeira',
                    icon='insights',
                    on_click=lambda: navegar('/')
                ).props('flat no-caps align=left').classes(
                    'w-full text-slate-700 hover:text-blue-700 hover:bg-blue-50 rounded-lg py-2.5 px-3 transition-all text-sm font-medium'
                )

                # Pagamentos do Mês
                ui.button(
                    'Pagamentos do Mês',
                    icon='payments',
                    on_click=lambda: navegar('/planejar')
                ).props('flat no-caps align=left').classes(
                    'w-full text-slate-700 hover:text-blue-700 hover:bg-blue-50 rounded-lg py-2.5 px-3 transition-all text-sm font-medium'
                )

            ui.separator().classes('bg-slate-200/80 my-1')

            # --- SEÇÃO 2: PLANEJAMENTO ---
            with ui.column().classes('w-full gap-1'):
                ui.label('PLANEJAMENTO').classes('text-[10px] font-bold tracking-wider text-slate-400 uppercase px-3 mb-1')

                # Planejar Receitas
                ui.button(
                    'Planejar Receitas',
                    icon='savings',
                    on_click=lambda: navegar('/receitas')
                ).props('flat no-caps align=left').classes(
                    'w-full text-slate-700 hover:text-blue-700 hover:bg-blue-50 rounded-lg py-2.5 px-3 transition-all text-sm font-medium'
                )

                # Planejar Despesas
                ui.button(
                    'Planejar Despesas',
                    icon='receipt_long',
                    on_click=lambda: navegar('/despesas')
                ).props('flat no-caps align=left').classes(
                    'w-full text-slate-700 hover:text-blue-700 hover:bg-blue-50 rounded-lg py-2.5 px-3 transition-all text-sm font-medium'
                )

            # --- SEÇÃO ADMIN (SE APLICÁVEL) ---
            if user_email == ADMIN_EMAIL:
                ui.separator().classes('bg-slate-200/80 my-1')
                with ui.column().classes('w-full gap-1'):
                    ui.label('ADMINISTRAÇÃO').classes('text-[10px] font-bold tracking-wider text-amber-600 uppercase px-3 mb-1')
                    ui.button(
                        'Manutenção (Admin)',
                        icon='admin_panel_settings',
                        on_click=lambda: navegar('/admin')
                    ).props('flat no-caps align=left').classes(
                        'w-full text-amber-800 hover:bg-amber-50 rounded-lg py-2.5 px-3 transition-all text-sm font-medium'
                    )

        # --- RODAPÉ: SAIR ---
        with ui.column().classes('w-full p-4 border-t border-slate-200 bg-white'):
            ui.button(
                'Sair da Conta',
                icon='logout',
                on_click=lambda: (drawer.hide(), app.storage.user.clear(), ui.navigate.to('/login'))
            ).props('flat no-caps align=left').classes(
                'w-full text-red-600 hover:bg-red-50 rounded-lg py-2.5 px-3 transition-all text-sm font-medium'
            )

            # Texto discreto de autoria
            ui.label('Desenvolvido por: Wellington Batista Brasileiro').classes(
                'text-[12px] text-slate-400 font-normal px-2 leading-tight tracking-tight text-center w-full'
            )            

    return drawer

def cabecalho_app(drawer):
    user_email = app.storage.user.get('email', 'Usuário')
    with ui.header().classes('bg-blue-900 text-white justify-between items-center p-3 w-full'):
        ui.button(icon='menu', on_click=drawer.toggle).props('flat color=white')
        ui.label('💰 Controle Financeiro').classes('text-base sm:text-lg font-bold truncate')
        ui.label(user_email.split('@')[0]).classes('text-xs bg-blue-700 px-2 py-1 rounded')


# --- LOGIN ---
@ui.page('/login')
def login_page():
    def abrir_modal_solicitacao():
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-sm p-4'):
            ui.label('Solicitar Acesso').classes('text-xl font-bold text-gray-800 mb-2')
            solicita_email = ui.input('E-mail').props('outlined').classes('w-full mb-2')
            solicita_senha = ui.input('Senha desejada', password=True, password_toggle_button=True).props('outlined').classes('w-full mb-4')

            async def processar_solicitacao():
                email_txt = (solicita_email.value or "").strip().lower()
                senha_txt = (solicita_senha.value or "").strip()

                if not email_valido(email_txt) or not senha_txt:
                    ui.notify('Preencha os campos corretamente!', color='warning')
                    return

                # Captura dados antes de fechar a tela
                user_agent = str(ui.context.client.environ.get('HTTP_USER_AGENT', 'Dispositivo Móvel'))[:150]
                loc_text = "Não informada"

                try:
                    ip_cliente = ui.context.client.environ.get('REMOTE_ADDR', '')
                    ip_data = requests.get(f'https://ipapi.co/{ip_cliente}/json/', timeout=2).json()
                    loc_text = f"{ip_data.get('city')}, {ip_data.get('region')}"
                except:
                    pass

                ui.notify('Processando solicitação...', color='info')
                dialog.close()

                try:
                    supabase.table('solicitacoes_acesso').insert({
                        'created_at': obter_hora_brasilia().isoformat(),
                        'email': email_txt,
                        'senha_temporaria': senha_txt,
                        'dispositivo': user_agent,
                        'localizacao': loc_text
                    }).execute()
                except Exception as e:
                    print(f"Erro ao salvar no banco: {e}")

                try:
                    enviar_notificacao_email(email_txt, user_agent, loc_text)
                    ui.notify('Solicitação enviada com sucesso!', color='positive')
                except Exception as e:
                    print(f"Erro ao enviar e-mail: {e}")
                    ui.notify('Solicitação registrada no banco!', color='positive')

            ui.button('ENVIAR SOLICITAÇÃO', on_click=processar_solicitacao).classes('w-full bg-blue-600 text-white font-bold mb-2')
            ui.button('CANCELAR', on_click=dialog.close).props('flat').classes('w-full text-gray-600')
        
        dialog.open()

    with ui.card().classes('w-11/12 max-w-sm absolute-center p-6 shadow-xl rounded-xl'):
        ui.label('Controle Financeiro').classes('text-2xl font-bold text-blue-800 text-center w-full mb-4')
        email = ui.input('E-mail').props('outlined').classes('w-full mb-2')
        password = ui.input('Senha', password=True, password_toggle_button=True).props('outlined').classes('w-full mb-4')

        def try_login():
            email_val = email.value.strip().lower() if email.value else ""
            pwd_val = password.value.strip() if password.value else ""

            res = supabase.table('perfis_usuarios').select("*").eq('email', email_val).execute()
            users = res.data or []

            if users and users[0].get('senha') == pwd_val:
                if not users[0].get('ativo', True):
                    ui.notify('Usuário inativo! Fale com o administrador.', color='negative')
                    return
                app.storage.user['user_id'] = users[0]['id']
                app.storage.user['email'] = users[0]['email']
                ui.navigate.to('/')
            else:
                ui.notify('E-mail ou senha incorretos!', color='negative')

        ui.button('ENTRAR', on_click=try_login).classes('w-full bg-blue-600 text-white font-bold mb-3')
        ui.separator().classes('my-2')
        ui.button('SOLICITAR ACESSO', on_click=abrir_modal_solicitacao).props('flat dense').classes('w-full text-blue-500 font-medium text-xs mt-2')

# --- RECEITAS ---
@ui.page('/receitas')
def receitas_page():
    if not app.storage.user.get('user_id'):
        ui.navigate.to('/login')
        return

    drawer = menu_drawer()
    cabecalho_app(drawer)
    user_id = app.storage.user.get('user_id')

    # Busca dinâmica de contas no Supabase
    contas_res = supabase.table('dim_contas').select("*").order('nome').execute()
    contas_opts = {c['id']: c['nome'] for c in (contas_res.data or [])}

    with ui.column().classes('w-full max-w-5xl mx-auto p-3 sm:p-4 gap-4'):
        ui.label('💵 Planejar Receitas').classes('text-xl sm:text-2xl font-bold text-green-800')

        # --- FORMULÁRIO DE NOVA RECEITA ---
        with ui.card().classes('w-full p-4 border border-green-200 rounded-lg shadow-sm bg-green-50'):
            ui.label('Nova Receita').classes('text-lg font-bold text-green-900 mb-2')
            with ui.column().classes('w-full sm:flex-row gap-3 items-stretch sm:items-center'):
                desc = ui.input('Descrição').props('outlined bg-white').classes('w-full sm:flex-1')
                valor = ui.number('Valor (R$)', format='%.2f').props('outlined bg-white').classes('w-full sm:w-36')
                conta_sel = ui.select(options=contas_opts, label='Conta / Ação').props('outlined bg-white').classes('w-full sm:w-48')

            ui.label('Meses em que a receita ocorre:').classes('text-sm font-bold text-gray-700 mt-2')
            
            meses_checks = {}
            with ui.row().classes('w-full gap-2 wrap bg-white p-2 border rounded'):
                for m_num, m_nome in MESES_NOMES.items():
                    meses_checks[m_num] = ui.checkbox(m_nome, value=True)

            with ui.row().classes('w-full gap-3 items-center mt-2'):
                ano_ini = ui.number('Ano Início', value=2025, format='%d').props('outlined bg-white').classes('w-full sm:w-32')
                ano_fim = ui.number('Ano Fim', value=2200, format='%d').props('outlined bg-white').classes('w-full sm:w-32')

            def salvar_receita():
                if not desc.value or not valor.value or not conta_sel.value:
                    ui.notify('Preencha os campos obrigatórios!', color='warning')
                    return

                meses_str = "." + ".".join([str(m) for m, chk in meses_checks.items() if chk.value]) + "."

                supabase.table('fato_receitas').insert({
                    'user_id': user_id,
                    'descricao': desc.value.strip(),
                    'valor': float(valor.value),
                    'conta_id': conta_sel.value,
                    'meses': meses_str,
                    'ano_inicio': int(ano_ini.value or 2025),
                    'ano_fim': int(ano_fim.value or 2200)
                }).execute()
                ui.notify('Receita salva!', color='positive')
                ui.navigate.reload()

            ui.button('Salvar Receita', on_click=salvar_receita, icon='add').classes('w-full sm:w-auto bg-green-700 text-white font-bold mt-2')

        # --- MODAL DE CONFIRMAÇÃO DE EDIÇÃO ---
        with ui.dialog() as confirm_edit_dialog, ui.card().classes('p-6 gap-4'):
            ui.label('Confirmar Alteração').classes('text-lg font-bold text-slate-800')
            ui.label('Deseja realmente salvar as alterações feitas nesta receita?')
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Cancelar', on_click=confirm_edit_dialog.close).props('flat color=grey')
                def executar_atualizacao():
                    try:
                        meses_str = "." + ".".join([str(m) for m, chk in edit_meses_checks.items() if chk.value]) + "."

                        supabase.table('fato_receitas').update({
                            'descricao': edit_desc.value.strip(),
                            'valor': float(edit_val.value),
                            'conta_id': edit_conta.value,
                            'meses': meses_str,
                            'ano_inicio': int(edit_ano_ini.value or 2025),
                            'ano_fim': int(edit_ano_fim.value or 2200)
                        }).eq('id', edit_id.value).execute()

                        ui.notify('Receita atualizada com sucesso!', color='positive')
                        confirm_edit_dialog.close()
                        modal_editar.close()
                        ui.navigate.reload()
                    except Exception as err:
                        ui.notify(f'Erro ao atualizar: {err}', color='negative')
                ui.button('Confirmar', on_click=executar_atualizacao).props('color=primary unelevated')

        # --- MODAL DE EDIÇÃO ---
        with ui.dialog() as modal_editar, ui.card().classes('w-full max-w-2xl p-6 gap-4'):
            ui.label('Editar Receita').classes('text-xl font-bold text-slate-800')
            
            edit_id = ui.input().classes('hidden')
            edit_desc = ui.input('Descrição').props('outlined bg-white').classes('w-full')
            
            with ui.row().classes('w-full gap-2'):
                edit_val = ui.number('Valor (R$)', format='%.2f').props('outlined bg-white').classes('flex-1')
                edit_conta = ui.select(options=contas_opts, label='Conta / Ação').props('outlined bg-white').classes('flex-1')

            ui.label('Meses em que a receita ocorre:').classes('text-sm font-bold text-gray-700 mt-2')
            edit_meses_checks = {}
            with ui.row().classes('w-full gap-2 wrap bg-white p-2 border rounded'):
                for m_num, m_nome in MESES_NOMES.items():
                    edit_meses_checks[m_num] = ui.checkbox(m_nome)

            with ui.row().classes('w-full gap-2 mt-2'):
                edit_ano_ini = ui.number('Ano Início', format='%d').props('outlined bg-white').classes('flex-1')
                edit_ano_fim = ui.number('Ano Fim', format='%d').props('outlined bg-white').classes('flex-1')

            def validar_e_confirmar_edicao():
                if not edit_desc.value or edit_val.value is None or not edit_conta.value:
                    ui.notify('Preencha todos os campos!', color='warning')
                    return
                confirm_edit_dialog.open()

            with ui.row().classes('w-full justify-end gap-2 mt-2'):
                ui.button('CANCELAR', on_click=modal_editar.close).props('flat color=grey')
                ui.button('SALVAR ALTERAÇÕES', on_click=validar_e_confirmar_edicao).props('color=primary unelevated')

        # --- MODAL DE CONFIRMAÇÃO DE EXCLUSÃO ---
        item_para_deletar = {'id': None}
        with ui.dialog() as confirm_delete_dialog, ui.card().classes('p-6 gap-4'):
            ui.label('Confirmar Exclusão').classes('text-lg font-bold text-red-700')
            ui.label('Tem certeza que deseja excluir esta receita? Esta ação não pode ser desfeita.')
            with ui.row().classes('w-full justify-end gap-2'):
                ui.button('Cancelar', on_click=confirm_delete_dialog.close).props('flat color=grey')
                def executar_exclusao():
                    if item_para_deletar['id']:
                        supabase.table('fato_receitas').delete().eq('id', item_para_deletar['id']).execute()
                        ui.notify('Receita removida!', color='negative')
                        confirm_delete_dialog.close()
                        ui.navigate.reload()
                ui.button('Excluir', on_click=executar_exclusao).props('color=red unelevated')

        # --- CARREGAMENTO DAS LINHAS DA TABELA ---
        res_receitas = supabase.table('fato_receitas').select("*, dim_contas(nome)").eq('user_id', user_id).order('created_at', desc=True).execute()
        receitas_raw = res_receitas.data or []
        
        rows = [{
            'id': r['id'],
            'descricao': r['descricao'],
            'valor': f"R$ {formatar_br(r['valor'])}",
            'valor_raw': r['valor'],
            'conta_id': r.get('conta_id'),
            'conta': r['dim_contas']['nome'] if r.get('dim_contas') else 'N/A',
            'meses': r.get('meses', 'Todos')
        } for r in receitas_raw]

        cols = [
            {'name': 'descricao', 'label': 'Descrição', 'field': 'descricao', 'align': 'left'},
            {'name': 'conta', 'label': 'Conta / Ação', 'field': 'conta', 'align': 'left'},
            {'name': 'meses', 'label': 'Meses', 'field': 'meses', 'align': 'center'},
            {'name': 'valor', 'label': 'Valor', 'field': 'valor', 'align': 'right'},
            {'name': 'id', 'label': 'Ações', 'field': 'id', 'align': 'center'}
        ]

        grid = ui.table(columns=cols, rows=rows, row_key='id').classes('w-full mt-4')
        grid.props('no-data-label="Nenhuma receita cadastrada"')
        
        grid.add_slot('body-cell-id', '''
            <q-td :props="props">
                <q-btn icon="edit" size="sm" color="primary" flat @click="$parent.$emit('editar', props.row)" />
                <q-btn icon="delete" size="sm" color="red" flat @click="$parent.$emit('deletar', props.row)" />
            </q-td>
        ''')

        def abrir_edicao_grid(msg):
            row = msg.args
            r_id = row['id']
            rec_orig = next((r for r in receitas_raw if str(r['id']) == str(r_id)), None)

            if rec_orig:
                edit_id.value = str(rec_orig['id'])
                edit_desc.value = rec_orig.get('descricao', '')
                edit_val.value = rec_orig.get('valor', 0.0)
                edit_conta.value = rec_orig.get('conta_id')
                edit_ano_ini.value = rec_orig.get('ano_inicio', 2025)
                edit_ano_fim.value = rec_orig.get('ano_fim', 2200)

                m_str = rec_orig.get('meses', '')
                for m_num, chk in edit_meses_checks.items():
                    chk.value = f".{m_num}." in m_str

                modal_editar.open()

        def solicitar_delecao(msg):
            item_para_deletar['id'] = msg.args['id']
            confirm_delete_dialog.open()

        grid.on('editar', abrir_edicao_grid)
        grid.on('deletar', solicitar_delecao)

# --- DESPESAS (CADASTRO PREVISTO) ---
@ui.page('/despesas')
def despesas_page():
    if not app.storage.user.get('user_id'):
        ui.navigate.to('/login')
        return

    drawer = menu_drawer()
    cabecalho_app(drawer)
    user_id = app.storage.user.get('user_id')

    # Opções do Banco de Dados
    contas_res = supabase.table('dim_contas').select("*").order('nome').execute()
    contas_opts = {c['id']: c['nome'] for c in (contas_res.data or [])}

    pgtos_res = supabase.table('dim_formas_pgto').select("*").order('nome').execute()
    pgtos_opts = {p['id']: p['nome'] for p in (pgtos_res.data or [])}

    # Nome exato da tabela no Supabase: dim_categorias
    cat_res = supabase.table('dim_categorias').select("*").order('nome').execute()
    cat_opts = {cat['id']: cat['nome'] for cat in (cat_res.data or [])}

    rec_res = supabase.table('fato_receitas').select("*").eq('user_id', user_id).execute()
    rec_opts = {r['id']: f"{r['descricao']} (R$ {formatar_br(r['valor'])})" for r in (rec_res.data or [])}

    with ui.column().classes('w-full max-w-6xl mx-auto p-3 sm:p-4 gap-4'):
        ui.label('🛒 Planejar despesas').classes('text-xl sm:text-2xl font-bold text-red-800')

        with ui.card().classes('w-full p-4 border border-red-200 rounded-lg shadow-sm bg-white border-slate-200'):
            ui.label('Cadastrar Nova Despesa').classes('text-lg font-bold text-red-900 mb-2')
            
            with ui.column().classes('w-full sm:flex-row gap-3 items-stretch sm:items-center'):
                desc = ui.input('Descrição da Despesa').props('outlined bg-white').classes('w-full sm:flex-2')
                valor = ui.number('Valor (R$)', format='%.2f').props('outlined bg-white').classes('w-full sm:w-32')
                dia_limite = ui.input('Dia do Vencimento').props('outlined bg-white').classes('w-full sm:w-40')

            with ui.column().classes('w-full sm:flex-row gap-3 items-stretch sm:items-center mt-2'):
                cat_sel = ui.select(options=cat_opts, label='Categoria').props('outlined bg-white').classes('w-full sm:flex-1')
                conta_sel = ui.select(options=contas_opts, label='Fonte de pagamento').props('outlined bg-white').classes('w-full sm:flex-1')
                pgto_sel = ui.select(options=pgtos_opts, label='Forma de Pagamento').props('outlined bg-white').classes('w-full sm:flex-1')
                rec_sel = ui.select(options=rec_opts, label='Receita utilizada para o pagamento').props('outlined bg-white').classes('w-full sm:flex-1')

            ui.label('Meses em que a despesa ocorre:').classes('text-sm font-bold text-gray-700 mt-2')
            
            meses_checks = {}
            with ui.row().classes('w-full gap-2 wrap bg-white p-2 border rounded'):
                for m_num, m_nome in MESES_NOMES.items():
                    meses_checks[m_num] = ui.checkbox(m_nome, value=True)

            with ui.row().classes('w-full gap-3 items-center mt-2'):
                ano_ini = ui.number('Ano Início', value=2025, format='%d').props('outlined bg-white').classes('w-full sm:w-32')
                ano_fim = ui.number('Ano Fim', value=2200, format='%d').props('outlined bg-white').classes('w-full sm:w-32')

            def salvar_despesa():
                if not desc.value or not valor.value or not conta_sel.value or not rec_sel.value:
                    ui.notify('Preencha descrição, valor, conta e receita de origem!', color='warning')
                    return
                
                meses_str = "." + ".".join([str(m) for m, chk in meses_checks.items() if chk.value]) + "."

                supabase.table('fato_despesas').insert({
                    'user_id': user_id,
                    'descricao': desc.value.strip(),
                    'valor': float(valor.value),
                    'dia_limite': dia_limite.value.strip() if dia_limite.value else 'Indefinido',
                    'categoria_id': cat_sel.value,
                    'conta_id': conta_sel.value,
                    'forma_pgto_id': pgto_sel.value,
                    'receita_id': rec_sel.value,
                    'meses': meses_str,
                    'ano_inicio': int(ano_ini.value or 2025),
                    'ano_fim': int(ano_fim.value or 2200)
                }).execute()

                ui.notify('Despesa cadastrada!', color='positive')
                ui.navigate.reload()

            ui.button('Salvar Despesa', on_click=salvar_despesa, icon='add').classes('w-full sm:w-auto bg-red-700 text-white font-bold mt-3')

        res_desp = supabase.table('fato_despesas').select("*, dim_categorias(nome), dim_contas(nome), dim_formas_pgto(nome), fato_receitas(descricao)").eq('user_id', user_id).order('created_at', desc=True).execute()
        despesas_raw = res_desp.data or []

        rows = [{
            'id': d['id'],
            'descricao': d['descricao'],
            'categoria': d['dim_categorias']['nome'] if d.get('dim_categorias') else 'Sem Categoria',
            'conta': d['dim_contas']['nome'] if d.get('dim_contas') else 'N/A',
            'forma_pgto': d['dim_formas_pgto']['nome'] if d.get('dim_formas_pgto') else 'N/A',
            'receita': d['fato_receitas']['descricao'] if d.get('fato_receitas') else 'N/A',
            'dia_limite': d.get('dia_limite', '-'),
            'meses': d.get('meses', 'Todos'),
            'valor': f"R$ {formatar_br(d['valor'])}"
        } for d in despesas_raw]

        cols = [
            {'name': 'descricao', 'label': 'Descrição', 'field': 'descricao', 'align': 'left'},
            {'name': 'categoria', 'label': 'Categoria', 'field': 'categoria', 'align': 'left'},
            {'name': 'conta', 'label': 'Ação/Conta', 'field': 'conta', 'align': 'left'},
            {'name': 'forma_pgto', 'label': 'Forma Pgto', 'field': 'forma_pgto', 'align': 'left'},
            {'name': 'receita', 'label': 'Saldada por', 'field': 'receita', 'align': 'left'},
            {'name': 'dia_limite', 'label': 'Dia Limite', 'field': 'dia_limite', 'align': 'center'},
            {'name': 'meses', 'label': 'Meses', 'field': 'meses', 'align': 'center'},
            {'name': 'valor', 'label': 'Valor', 'field': 'valor', 'align': 'right'},
            {'name': 'id', 'label': 'Ações', 'field': 'id', 'align': 'center'}
        ]

        grid = ui.table(columns=cols, rows=rows, row_key='id').classes('w-full mt-4')
        grid.props('no-data-label="Nenhuma despesa cadastrada"')
        grid.add_slot('body-cell-id', '''
            <q-td :props="props">
                <q-btn icon="edit" size="sm" color="blue" flat @click="$parent.$emit('editar', props.row)" />
                <q-btn icon="delete" size="sm" color="red" flat @click="$parent.$emit('deletar', props.row)" />
            </q-td>
        ''')

        # --- DIÁLOGO DE EDIÇÃO DE DESPESA ---
        dialog_edit = ui.dialog()
        with dialog_edit, ui.card().classes('w-full max-w-2xl p-4'):
            ui.label('✏️ Editar Despesa').classes('text-lg font-bold text-blue-900 mb-2')
            
            edit_id = ui.input().classes('hidden')
            edit_desc = ui.input('Descrição').props('outlined bg-white').classes('w-full')
            
            with ui.row().classes('w-full gap-2'):
                edit_valor = ui.number('Valor (R$)', format='%.2f').props('outlined bg-white').classes('flex-1')
                edit_dia = ui.input('Dia do Vencimento').props('outlined bg-white').classes('flex-1')

            with ui.column().classes('w-full gap-2 mt-2'):
                edit_cat = ui.select(options=cat_opts, label='Categoria').props('outlined bg-white').classes('w-full')
                edit_conta = ui.select(options=contas_opts, label='Fonte de pagamento').props('outlined bg-white').classes('w-full')
                edit_pgto = ui.select(options=pgtos_opts, label='Forma de Pagamento').props('outlined bg-white').classes('w-full')
                edit_rec = ui.select(options=rec_opts, label='Receita utilizada').props('outlined bg-white').classes('w-full')

            ui.label('Meses em que a despesa ocorre:').classes('text-sm font-bold text-gray-700 mt-2')
            edit_meses_checks = {}
            with ui.row().classes('w-full gap-2 wrap bg-white p-2 border rounded'):
                for m_num, m_nome in MESES_NOMES.items():
                    edit_meses_checks[m_num] = ui.checkbox(m_nome)

            with ui.row().classes('w-full gap-2 mt-2'):
                edit_ano_ini = ui.number('Ano Início', format='%d').props('outlined bg-white').classes('flex-1')
                edit_ano_fim = ui.number('Ano Fim', format='%d').props('outlined bg-white').classes('flex-1')

            def salvar_edicao():
                if not edit_desc.value or not edit_valor.value or not edit_conta.value or not edit_rec.value:
                    ui.notify('Preencha os campos obrigatórios!', color='warning')
                    return

                meses_str = "." + ".".join([str(m) for m, chk in edit_meses_checks.items() if chk.value]) + "."

                try:
                    supabase.table('fato_despesas').update({
                        'descricao': edit_desc.value.strip(),
                        'valor': float(edit_valor.value),
                        'dia_limite': edit_dia.value.strip() if edit_dia.value else 'Indefinido',
                        'categoria_id': edit_cat.value,
                        'conta_id': edit_conta.value,
                        'forma_pgto_id': edit_pgto.value,
                        'receita_id': edit_rec.value,
                        'meses': meses_str,
                        'ano_inicio': int(edit_ano_ini.value or 2025),
                        'ano_fim': int(edit_ano_fim.value or 2200)
                    }).eq('id', str(edit_id.value)).execute()

                    ui.notify('Despesa atualizada com sucesso!', color='positive')
                    dialog_edit.close()
                    ui.navigate.reload()
                except Exception as e:
                    ui.notify(f'Erro ao atualizar: {e}', color='negative')

            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('Cancelar', on_click=dialog_edit.close).props('flat color=gray')
                ui.button('Salvar Alterações', on_click=salvar_edicao, icon='save').classes('bg-blue-700 text-white font-bold')

        def abrir_edicao(msg):
            d_id = msg.args['id']
            desp_orig = next((d for d in despesas_raw if str(d['id']) == str(d_id)), None)
            
            if desp_orig:
                edit_id.value = str(desp_orig['id'])
                edit_desc.value = desp_orig.get('descricao', '')
                edit_valor.value = desp_orig.get('valor', 0.0)
                edit_dia.value = desp_orig.get('dia_limite', '')
                edit_cat.value = desp_orig.get('categoria_id')
                edit_conta.value = desp_orig.get('conta_id')
                edit_pgto.value = desp_orig.get('forma_pgto_id')
                edit_rec.value = desp_orig.get('receita_id')
                edit_ano_ini.value = desp_orig.get('ano_inicio', 2025)
                edit_ano_fim.value = desp_orig.get('ano_fim', 2200)

                m_str = desp_orig.get('meses', '')
                for m_num, chk in edit_meses_checks.items():
                    chk.value = f".{m_num}." in m_str

                dialog_edit.open()

        def deletar_despesa(msg):
            supabase.table('fato_despesas').delete().eq('id', str(msg.args['id'])).execute()
            ui.notify('Despesa removida!', color='negative')
            ui.navigate.reload()

        grid.on('editar', abrir_edicao)
        grid.on('deletar', deletar_despesa)


from datetime import datetime

# --- TELA DE PLANEJAMENTO / FILTRO MENSAL ---
@ui.page('/planejar')
def planejar_page():
    if not app.storage.user.get('user_id'):
        ui.navigate.to('/login')
        return

    drawer = menu_drawer()
    cabecalho_app(drawer)
    user_id = app.storage.user.get('user_id')

    rec_res = supabase.table('fato_receitas').select("*").eq('user_id', user_id).execute()
    receitas_lista = rec_res.data or []
    
    rec_opts = {'TODAS': 'Todas as Receitas'}
    rec_opts.update({r['id']: f"{r['descricao']} (R$ {formatar_br(r['valor'])})" for r in receitas_lista})

    mes_atual = datetime.now().month
    ano_atual = datetime.now().year

    with ui.column().classes('w-full max-w-5xl mx-auto p-2 sm:p-4 gap-4'):
        ui.label('📅 Pagamentos do mês').classes('text-xl sm:text-2xl font-bold text-purple-800')

        # Filtros Responsivos
        with ui.card().classes('w-full p-3 sm:p-4 border rounded-lg bg-purple-50 shadow-sm'):
            with ui.column().classes('w-full sm:flex-row gap-3 items-stretch sm:items-center'):
                sel_mes = ui.select(options=MESES_NOMES, value=mes_atual, label='Mês').props('outlined bg-white').classes('w-full sm:w-36')
                sel_ano = ui.number('Ano', value=ano_atual, format='%d').props('outlined bg-white').classes('w-full sm:w-36')
                
                # Select Múltiplo para Receitas
                sel_receita = ui.select(
                    options=rec_opts, 
                    value=['TODAS'], 
                    multiple=True, 
                    label='Filtrar por Receita'
                ).props('outlined bg-white use-chips clearable').classes('w-full sm:flex-1')

        # Áreas de Conteúdo
        container_lista = ui.column().classes('w-full gap-4')
        container_subtotais_acao = ui.column().classes('w-full mt-2')
        container_resumo = ui.column().classes('w-full sm:flex-row gap-3 mt-2')

        # Função de alternância isolada
        def alternar_pago(despesa_id, mes, ano, novo_status):
            try:
                if novo_status:
                    supabase.table('fato_despesas_pagas').upsert({
                        'user_id': user_id,
                        'despesa_id': despesa_id,
                        'mes': mes,
                        'ano': ano,
                        'pago': True
                    }, on_conflict='user_id,despesa_id,mes,ano').execute()
                else:
                    supabase.table('fato_despesas_pagas').delete()\
                        .eq('user_id', user_id)\
                        .eq('despesa_id', despesa_id)\
                        .eq('mes', mes)\
                        .eq('ano', ano).execute()
                
                atualizar_consulta()
            except Exception as ex:
                ui.notify(f"Erro ao atualizar status: {ex}", color='negative')

        def ao_mudar_receita(e=None):
            if hasattr(e, 'value'):
                valores = e.value or []
            elif isinstance(e, (list, tuple)):
                valores = list(e)
            else:
                valores = sel_receita.value or []

            if isinstance(valores, str):
                valores = [valores]

            if not valores:
                sel_receita.value = ['TODAS']
            elif 'TODAS' in valores and len(valores) > 1:
                if valores[-1] == 'TODAS':
                    sel_receita.value = ['TODAS']
                else:
                    sel_receita.value = [v for v in valores if v != 'TODAS']

            atualizar_consulta()

        def atualizar_consulta(e=None):
            container_lista.clear()
            container_subtotais_acao.clear()
            container_resumo.clear()

            m_val = sel_mes.value
            a_val = int(sel_ano.value or ano_atual)
            
            r_vals = sel_receita.value or ['TODAS']
            if not isinstance(r_vals, list):
                r_vals = [r_vals]

            # Consulta com o nome exato da tabela de categorias (dim_categorias)
            query = supabase.table('fato_despesas').select("*, dim_categorias(nome), dim_contas(nome), dim_formas_pgto(nome), fato_receitas(id, descricao, valor)").eq('user_id', user_id)
            res = query.execute()
            despesas_todas = res.data or []

            if 'TODAS' not in r_vals:
                r_vals_ids = [int(v) if str(v).isdigit() else v for v in r_vals]
                despesas_todas = [d for d in despesas_todas if d.get('receita_id') in r_vals_ids]

            pagas_res = supabase.table('fato_despesas_pagas').select('despesa_id').eq('user_id', user_id).eq('mes', m_val).eq('ano', a_val).execute()
            ids_pagas = {p['despesa_id'] for p in (pagas_res.data or [])}

            str_mes_busca = f".{m_val}."
            despesas_filtradas = []
            for d in despesas_todas:
                m_str = d.get('meses', '')
                ano_i = d.get('ano_inicio', 2000)
                ano_f = d.get('ano_fim', 2200)

                if str_mes_busca in m_str and (ano_i <= a_val <= ano_f):
                    despesas_filtradas.append(d)

            total_desp = 0.0
            subtotais_acao = {}

            with container_lista:
                if not despesas_filtradas:
                    ui.label('Nenhuma despesa para este mês/filtro.').classes('text-gray-500 italic p-4 text-center w-full')
                else:
                    # 1. Agrupamento inicial por Categoria
                    categorias_agrupadas = {}
                    for d in despesas_filtradas:
                        cat_nome = d['dim_categorias']['nome'] if d.get('dim_categorias') else 'Sem Categoria'
                        if cat_nome not in categorias_agrupadas:
                            categorias_agrupadas[cat_nome] = []
                        categorias_agrupadas[cat_nome].append(d)

                    # 2. Separação: Categorias com múltiplos itens vs. Categorias com 1 único item
                    cats_com_varios = {}
                    cats_singulares_nomes = []
                    itens_singulares = []

                    for cat_nome in sorted(categorias_agrupadas.keys()):
                        itens = categorias_agrupadas[cat_nome]
                        if len(itens) > 1:
                            cats_com_varios[cat_nome] = itens
                        else:
                            cats_singulares_nomes.append(cat_nome)
                            itens_singulares.extend(itens)

                    # Função auxiliar para renderizar cada card de despesa
                    def renderizar_card_despesa(d):
                        nonlocal total_desp
                        d_id = d['id']
                        val = d['valor']
                        total_desp += val
                        esta_pago = d_id in ids_pagas

                        forma_p = d['dim_formas_pgto']['nome'] if d.get('dim_formas_pgto') else 'N/A'
                        conta_p = d['dim_contas']['nome'] if d.get('dim_contas') else 'N/A'
                        rec_p = d['fato_receitas']['descricao'] if d.get('fato_receitas') else 'N/A'
                        dia_l = d.get('dia_limite', '-')

                        subtotais_acao[conta_p] = subtotais_acao.get(conta_p, 0.0) + val

                        with ui.card().classes(f'w-full p-3 border rounded-lg shadow-sm {"bg-gray-100 opacity-60" if esta_pago else "bg-white"} transition-all'):
                            with ui.row().classes('w-full justify-between items-center flex-wrap gap-2'):
                                with ui.row().classes('items-center gap-2 flex-1 min-w-[180px]'):
                                    def make_handler(target_id=d_id):
                                        return lambda e: alternar_pago(target_id, m_val, a_val, e.value)

                                    ui.checkbox('', value=esta_pago, on_change=make_handler())
                                    
                                    with ui.column().classes('gap-0 flex-1 min-w-0'):
                                        ui.label(d['descricao']).classes(f'font-bold text-sm sm:text-base leading-tight break-words {"line-through text-gray-500" if esta_pago else "text-gray-800"}')
                                        ui.label(f"Venc: {dia_l} | {forma_p}").classes('text-xs text-gray-500 break-words')

                                with ui.column().classes('items-end gap-0 ml-auto text-right min-w-[120px]'):
                                    ui.label(f"R$ {formatar_br(val)}").classes(f'font-black text-sm sm:text-base {"line-through text-gray-400" if esta_pago else "text-red-700"}')
                                    ui.label(f"{conta_p} ({rec_p})").classes('text-xs text-purple-700 font-medium break-words max-w-[180px] text-right')

                    # 3. Renderiza primeiro as categorias com +1 item
                    for cat_nome, lista_cat in cats_com_varios.items():
                        lista_cat.sort(key=lambda x: x.get('descricao', '').lower())

                        with ui.column().classes('w-full gap-2'):
                            ui.label(f'🏷️ {cat_nome}').classes('text-base font-bold text-purple-900 border-b border-purple-200 pb-1 w-full mt-2')
                            for d in lista_cat:
                                renderizar_card_despesa(d)

                    # 4. Renderiza o grupo unificado de categorias com apenas 1 item
                    if itens_singulares:
                        itens_singulares.sort(key=lambda x: x.get('descricao', '').lower())
                        titulo_agrupado = " / ".join(cats_singulares_nomes)

                        with ui.column().classes('w-full gap-2'):
                            ui.label(f'🏷️ {titulo_agrupado}').classes('text-base font-bold text-purple-900 border-b border-purple-200 pb-1 w-full mt-2')
                            for d in itens_singulares:
                                renderizar_card_despesa(d)

            # --- SUBTOTAIS POR MEIO DE PAGAMENTO ---
            with container_subtotais_acao:
                if subtotais_acao:
                    ui.label('📌 Valores por meio de pagamento').classes('text-sm font-bold text-purple-900 mb-1')
                    with ui.row().classes('w-full gap-2 flex-wrap'):
                        for acao, total_acao in subtotais_acao.items():
                            with ui.card().classes('bg-purple-50 p-2.5 border border-purple-200 rounded-lg shadow-xs min-w-[140px] flex-1'):
                                ui.label(acao).classes('text-xs font-bold text-purple-900 truncate')
                                ui.label(f'R$ {formatar_br(total_acao)}').classes('text-base font-extrabold text-slate-800')

            # Resumo e Totais Gerais
            if 'TODAS' in r_vals:
                capital_total = sum([rec['valor'] for rec in receitas_lista])
            else:
                r_vals_ids = [int(v) if str(v).isdigit() else v for v in r_vals]
                capital_total = sum([rec['valor'] for rec in receitas_lista if rec['id'] in r_vals_ids])

            sobra = capital_total - total_desp

            with container_resumo:
                with ui.card().classes('w-full sm:flex-1 bg-purple-100 p-3 sm:p-4 border rounded-lg shadow-sm'):
                    ui.label('TOTAL RECEITA').classes('text-xs font-bold text-purple-900 uppercase')
                    ui.label(f'R$ {formatar_br(capital_total)}').classes('text-lg sm:text-xl font-bold text-purple-950')

                with ui.card().classes('w-full sm:flex-1 bg-red-100 p-3 sm:p-4 border rounded-lg shadow-sm'):
                    ui.label('TOTAL DESPESAS DO MÊS').classes('text-xs font-bold text-red-900 uppercase')
                    ui.label(f'R$ {formatar_br(total_desp)}').classes('text-lg sm:text-xl font-bold text-red-950')

                with ui.card().classes(f'w-full sm:flex-1 {"bg-green-100 border-green-300" if sobra >= 0 else "bg-amber-100 border-amber-300"} p-3 sm:p-4 border rounded-lg shadow-sm'):
                    ui.label('SALDO FINAL').classes('text-xs font-bold uppercase')
                    ui.label(f'R$ {formatar_br(sobra)}').classes(f'text-lg sm:text-xl font-bold {"text-green-950" if sobra >= 0 else "text-amber-950"}')

        sel_mes.on('update:model-value', atualizar_consulta)
        sel_ano.on('update:model-value', atualizar_consulta)
        sel_receita.on('update:model-value', ao_mudar_receita)

        atualizar_consulta()


def criar_gerenciador_dimensao(titulo: str, tabela_nome: str):
    with ui.card().classes('w-full p-4 border rounded-lg shadow-sm bg-amber-50 mb-4'):
        ui.label(f'🗂️ {titulo}').classes('text-lg font-bold text-amber-900 mb-2')
        
        container_itens = ui.column().classes('w-full gap-2')

        def carregar_itens():
            container_itens.clear()
            with container_itens:
                try:
                    res = supabase.table(tabela_nome).select("*").order('nome').execute()
                    dados = res.data or []
                    
                    with ui.row().classes('w-full gap-2 mb-3 items-center'):
                        novo_nome = ui.input(placeholder='Novo item...').classes('flex-1 bg-white')
                        
                        def salvar_novo():
                            if novo_nome.value.strip():
                                supabase.table(tabela_nome).insert({'nome': novo_nome.value.strip()}).execute()
                                ui.notify('Item adicionado!', color='positive')
                                carregar_itens()

                        ui.button('Adicionar', on_click=salvar_novo, icon='add').classes('bg-blue-600 text-white')

                    if not dados:
                        ui.label('Nenhum item cadastrado.').classes('text-gray-500 italic text-sm')
                    else:
                        for item in dados:
                            with ui.card().classes('w-full p-2 bg-white border flex-row justify-between items-center'):
                                ui.label(item.get('nome', 'Sem nome')).classes('font-medium text-sm')
                                
                                def deletar(item_id=item['id']):
                                    supabase.table(tabela_nome).delete().eq('id', item_id).execute()
                                    ui.notify('Item removido!', color='warning')
                                    carregar_itens()

                                ui.button(icon='delete', on_click=deletar).props('flat dense color=red')
                except Exception as e:
                    ui.label(f"Erro ao carregar dados: {e}").classes('text-red-500 text-sm')

        carregar_itens()

# --- ADMIN (manutenções de administrador) ---
@ui.page('/admin')
def admin_page():
    if not app.storage.user.get('user_id'):
        ui.navigate.to('/login')
        return

    if app.storage.user.get('email') != ADMIN_EMAIL:
        ui.notify('Acesso negado!', color='warning')
        ui.navigate.to('/')
        return

    drawer = menu_drawer()
    cabecalho_app(drawer)

    with ui.column().classes('w-full max-w-5xl mx-auto p-3 sm:p-4 gap-6'):
        ui.label('⚙️ Painel do Administrador').classes('text-xl sm:text-2xl font-bold text-slate-800')

        # ----------------------------------------------------------------------
        # 1. SOLICITANTES DE ACESSO
        # ----------------------------------------------------------------------
        with ui.card().classes('w-full p-4 border rounded-lg shadow-sm bg-blue-50'):
            ui.label('📋 Solicitantes de Acesso Pendentes').classes('text-lg sm:text-xl font-bold text-blue-900 mb-2')
            solic_res = supabase.table('solicitacoes_acesso').select("*").eq('status', 'PENDENTE').order('created_at', desc=True).execute()
            pedidos = solic_res.data or []

            if not pedidos:
                ui.label('Nenhuma solicitação pendente.').classes('text-gray-500 italic')
            else:
                for p in pedidos:
                    with ui.card().classes('w-full p-3 bg-white border mb-2'):
                        with ui.column().classes('sm:flex-row justify-between items-start sm:items-center w-full gap-2'):
                            with ui.column().classes('gap-0'):
                                ui.label(f"✉️ {p['email']}").classes('font-bold text-sm sm:text-base')
                                ui.label(f"📍 Localização: {p['localizacao']}").classes('text-xs text-gray-600')

                            with ui.row().classes('gap-2 w-full sm:w-auto'):
                                def aprovar(pedido=p):
                                    supabase.table('perfis_usuarios').upsert({'email': pedido['email'].lower(), 'senha': pedido['senha_temporaria'], 'ativo': True, 'role': 'USER'}, on_conflict='email').execute()
                                    supabase.table('solicitacoes_acesso').update({'status': 'APROVADO'}).eq('id', pedido['id']).execute()
                                    ui.notify(f"Acesso APROVADO!", color='positive')
                                    ui.navigate.reload()

                                def reprovar(pedido=p):
                                    supabase.table('solicitacoes_acesso').update({'status': 'REPROVADO'}).eq('id', pedido['id']).execute()
                                    ui.notify("Solicitação reprovada.", color='warning')
                                    ui.navigate.reload()

                                ui.button('Aprovar', on_click=aprovar, icon='check').classes('flex-1 sm:flex-none bg-green-600 text-white text-xs')
                                ui.button('Reprovar', on_click=reprovar, icon='close').classes('flex-1 sm:flex-none bg-red-600 text-white text-xs')

        # ----------------------------------------------------------------------
        # 2. CONTROLE DE USUÁRIOS DO APP
        # ----------------------------------------------------------------------
        with ui.card().classes('w-full p-4 border rounded-lg shadow-sm bg-slate-50'):
            ui.label('👥 Controle de Usuários do App').classes('text-lg sm:text-xl font-bold text-slate-800 mb-2')
            users_res = supabase.table('perfis_usuarios').select("*").order('created_at', desc=True).execute()

            for u in (users_res.data or []):
                is_active = u.get('ativo', True)
                with ui.card().classes(f'w-full p-3 bg-white border mb-2 {"border-l-8 border-l-green-500" if is_active else "border-l-8 border-l-red-500"}'):
                    with ui.row().classes('justify-between items-center w-full'):
                        ui.label(f"👤 {u['email']} | Status: {'🟢 ATIVO' if is_active else '🔴 INATIVO'}").classes('font-bold text-xs sm:text-sm')
                        if u['email'] != ADMIN_EMAIL:
                            def alternar_status(user=u):
                                supabase.table('perfis_usuarios').update({'ativo': not user.get('ativo', True)}).eq('id', user['id']).execute()
                                ui.navigate.reload()

                            ui.button('Inativar' if is_active else 'Ativar', on_click=alternar_status).classes(f'{"bg-red-600" if is_active else "bg-green-600"} text-white text-xs')

# --- 3. SEÇÃO DAS TABELAS DIMENSÃO ---
        criar_gerenciador_dimensao("1. Categorias de Despesas", "dim_categorias")
        criar_gerenciador_dimensao("2. Formas de Pagamento", "dim_formas_pgto")
        criar_gerenciador_dimensao("3. Contas / Ações", "dim_contas")               


from datetime import datetime

# --- SAÚDE FINANCEIRA / DASHBOARD (HOME) ---
@ui.page('/')
def home_page():
    if not app.storage.user.get('user_id'):
        ui.navigate.to('/login')
        return

    drawer = menu_drawer()
    cabecalho_app(drawer)
    user_id = app.storage.user.get('user_id')

    # Estado de privacidade e controle de ano
    modo_privado = {'ativo': True}
    ano_atual_ref = datetime.now().year

    # Buscar dados do Supabase
    rec_res = supabase.table('fato_receitas').select("*").eq('user_id', user_id).execute()
    receitas_lista = rec_res.data or []

    desp_res = supabase.table('fato_despesas').select("*, dim_categorias(nome)").eq('user_id', user_id).execute()
    despesas_lista = desp_res.data or []

    # Opções do filtro de receitas
    opts_receitas = {'todas': 'Todas as Receitas'}
    for r in receitas_lista:
        desc = r.get('descricao', 'Receita')
        val = float(r.get('valor', 0))
        opts_receitas[str(r['id'])] = f"{desc} (R$ {formatar_br(val)})"

    with ui.column().classes('w-full max-w-6xl mx-auto p-3 sm:p-4 gap-5'):
        
        # 1. BANNER TOPO COM PRIVACIDADE
        with ui.card().classes('w-full p-6 bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-900 text-white rounded-2xl shadow-xl flex flex-row justify-between items-center'):
            with ui.column().classes('gap-1'):
                ui.label('Saúde Financeira').classes('text-2xl sm:text-3xl font-black tracking-tight')
                ui.label('Gerencie suas metas e despesas com tranquilidade e privacidade.').classes('text-xs sm:text-sm text-slate-300')
            
            btn_privacidade = ui.button(
                icon='visibility_off', 
                on_click=lambda: alternar_privacidade()
            ).props('flat round color=white size=lg').classes('bg-white/10 hover:bg-white/20')

        # 2. AÇÕES RÁPIDAS
        ui.label('⚡ Ações Rápidas').classes('text-sm font-bold text-slate-700 tracking-wide uppercase mt-1')
        with ui.row().classes('w-full gap-4'):
            with ui.card().classes('flex-1 p-4 border border-slate-200 rounded-xl shadow-sm hover:shadow-md cursor-pointer items-center justify-center transition-all bg-white') \
                    .on('click', lambda: ui.navigate.to('/despesas')):
                ui.icon('shopping_cart', size='32px').classes('text-red-500 mb-1')
                ui.label('Nova Despesa').classes('text-sm font-bold text-slate-700')

            with ui.card().classes('flex-1 p-4 border border-slate-200 rounded-xl shadow-sm hover:shadow-md cursor-pointer items-center justify-center transition-all bg-white') \
                    .on('click', lambda: ui.navigate.to('/receitas')):
                ui.icon('attach_money', size='32px').classes('text-green-500 mb-1')
                ui.label('Nova Receita').classes('text-sm font-bold text-slate-700')

        # 3. BARRA DE FILTROS DO PERÍODO
        ui.label('📊 Visão Geral do Período').classes('text-sm font-bold text-slate-700 tracking-wide uppercase mt-2')
        with ui.card().classes('w-full p-4 border border-slate-200 rounded-xl shadow-sm bg-white'):
            with ui.row().classes('w-full gap-3 items-center flex-wrap sm:flex-nowrap'):
                f_ano_ini = ui.number('Ano Início', value=ano_atual_ref, format='%d').props('outlined bg-slate-50 dense').classes('w-full sm:w-32')
                f_ano_fim = ui.number('Ano Fim', value=ano_atual_ref, format='%d').props('outlined bg-slate-50 dense').classes('w-full sm:w-32')
                
                f_receitas = ui.select(
                    options=opts_receitas, 
                    value=['todas'], 
                    multiple=True, 
                    label='Filtrar por Receita'
                ).props('outlined bg-slate-50 dense use-chips clearable').classes('w-full flex-1')

        # 4. CARDS DE RESUMO (KPIs)
        with ui.row().classes('w-full gap-4'):
            with ui.card().classes('flex-1 p-4 bg-emerald-50/60 border border-emerald-200 rounded-xl shadow-sm'):
                ui.label('TOTAL RECEITAS (PERÍODO)').classes('text-[11px] font-bold text-emerald-700 tracking-wider')
                lbl_tot_rec = ui.label('R$ ••••••').classes('text-xl sm:text-2xl font-black text-emerald-950 mt-1')

            with ui.card().classes('flex-1 p-4 bg-rose-50/60 border border-rose-200 rounded-xl shadow-sm'):
                ui.label('TOTAL DESPESAS (PERÍODO)').classes('text-[11px] font-bold text-rose-700 tracking-wider')
                lbl_tot_desp = ui.label('R$ ••••••').classes('text-xl sm:text-2xl font-black text-rose-950 mt-1')

            with ui.card().classes('flex-1 p-4 bg-blue-50/60 border border-blue-200 rounded-xl shadow-sm'):
                ui.label('SALDO ACUMULADO').classes('text-[11px] font-bold text-blue-700 tracking-wider')
                lbl_tot_saldo = ui.label('R$ ••••••').classes('text-xl sm:text-2xl font-black text-blue-950 mt-1')

        # 5. GRÁFICOS
        with ui.card().classes('w-full p-4 border border-slate-200 rounded-xl shadow-sm bg-white'):
            ui.label('Despesas por Categoria').classes('text-lg font-bold text-slate-800 mb-2')
            chart_bar_cat = ui.echart({}).classes('w-full h-80')

        with ui.card().classes('w-full p-4 border border-slate-200 rounded-xl shadow-sm bg-white'):
            ui.label('Receitas X Despesas').classes('text-lg font-bold text-slate-800 mb-2')
            chart_cap_desp = ui.echart({}).classes('w-full h-80')

        with ui.card().classes('w-full p-4 border border-slate-200 rounded-xl shadow-sm bg-white'):
            ui.label('Saldo Mensal').classes('text-lg font-bold text-slate-800 mb-2')
            chart_saldo_mes = ui.echart({}).classes('w-full h-80')

        with ui.card().classes('w-full p-4 border border-slate-200 rounded-xl shadow-sm bg-white'):
            ui.label('Projeção - Saldo Acumulado').classes('text-lg font-bold text-slate-800 mb-2')
            chart_proj = ui.echart({}).classes('w-full h-80')

        # 6. LÓGICA DE RECALCULO E ATUALIZAÇÃO REATIVA
        def despesa_ocorre_no_mes_ano(d, m, ano):
            try:
                ano_d_ini = int(d.get('ano_inicio') or 2025)
                ano_d_fim = int(d.get('ano_fim') or 2200)
            except (ValueError, TypeError):
                ano_d_ini, ano_d_fim = 2025, 2200

            if not (ano_d_ini <= ano <= ano_d_fim):
                return False

            meses_raw = str(d.get('meses') or '')
            import re
            meses_list = [int(x) for x in re.findall(r'\d+', meses_raw)]
            return m in meses_list

        processando_selecao = {'ativo': False}

        def gerenciar_mudanca_receitas(e):
            if processando_selecao['ativo']:
                return

            val_atual = f_receitas.value or []
            if isinstance(val_atual, str):
                val_atual = [val_atual]

            novos_valores = list(val_atual)

            if 'todas' in novos_valores and len(novos_valores) > 1:
                if e.value and isinstance(e.value, list) and e.value[-1] == 'todas':
                    novos_valores = ['todas']
                else:
                    novos_valores = [v for v in novos_valores if v != 'todas']

            if not novos_valores:
                novos_valores = ['todas']

            if novos_valores != val_atual:
                processando_selecao['ativo'] = True
                f_receitas.set_value(novos_valores)
                processando_selecao['ativo'] = False

            atualizar_dashboard()

        def atualizar_dashboard():
            try:
                a_ini = int(f_ano_ini.value or ano_atual_ref)
                a_fim = int(f_ano_fim.value or ano_atual_ref)
            except (ValueError, TypeError):
                a_ini, a_fim = ano_atual_ref, ano_atual_ref

            if a_fim < a_ini:
                a_fim = a_ini

            rec_sel_raw = f_receitas.value or []
            if isinstance(rec_sel_raw, str):
                rec_sel_raw = [rec_sel_raw]

            ids_selecionados_str = [str(x) for x in rec_sel_raw if str(x) != 'todas' and x is not None]
            filtrar_especifico = len(ids_selecionados_str) > 0

            meses_labels = []
            totais_receitas_mes = []
            totais_despesas_mes = []
            saldos_mensais = []
            saldos_acumulados = []
            acumulado = 0.0

            despesas_por_categoria = {}

            for ano in range(a_ini, a_fim + 1):
                sufixo_ano = f"/{str(ano)[2:]}"
                for m in range(1, 13):
                    meses_labels.append(f"{MESES_NOMES[m]}{sufixo_ano}")

                    # 1. RECEITAS
                    recs_filtradas = [
                        r for r in receitas_lista
                        if receita_ocorre_no_mes_ano(r, m, ano) and 
                        (not filtrar_especifico or str(r.get('id')) in ids_selecionados_str)
                    ]
                    rec_mes = sum(float(r.get('valor', 0)) for r in recs_filtradas)

                    # 2. DESPESAS
                    desps_filtradas = []
                    for d in despesas_lista:
                        if despesa_ocorre_no_mes_ano(d, m, ano):
                            rec_id_despesa = d.get('receita_id')
                            rec_id_str = str(rec_id_despesa) if rec_id_despesa not in (None, '', 'None', 'null') else None

                            if filtrar_especifico:
                                if rec_id_str and rec_id_str in ids_selecionados_str:
                                    desps_filtradas.append(d)
                            else:
                                desps_filtradas.append(d)

                    desp_mes = sum(float(d.get('valor', 0)) for d in desps_filtradas)

                    for d in desps_filtradas:
                        cat_nome = d['dim_categorias']['nome'] if d.get('dim_categorias') else 'Sem Categoria'
                        val_d = float(d.get('valor', 0))
                        despesas_por_categoria[cat_nome] = despesas_por_categoria.get(cat_nome, 0.0) + val_d

                    totais_receitas_mes.append(rec_mes)
                    totais_despesas_mes.append(desp_mes)

                    saldo_mes = rec_mes - desp_mes
                    saldos_mensais.append(saldo_mes)

                    acumulado += saldo_mes
                    saldos_acumulados.append(acumulado)

            total_rec = sum(totais_receitas_mes)
            total_desp = sum(totais_despesas_mes)
            saldo_final = total_rec - total_desp

            priv_ativo = modo_privado['ativo']

            # Atualizar Rótulos dos Cards
            if priv_ativo:
                lbl_tot_rec.text = "R$ ••••••"
                lbl_tot_desp.text = "R$ ••••••"
                lbl_tot_saldo.text = "R$ ••••••"
            else:
                lbl_tot_rec.text = f"R$ {formatar_br(total_rec)}"
                lbl_tot_desp.text = f"R$ {formatar_br(total_desp)}"
                lbl_tot_saldo.text = f"R$ {formatar_br(saldo_final)}"

            # Expressões JavaScript formatadoras para o ECharts (o prefixo ':' avisa o NiceGUI para tratar como JS puro)
            js_formatter_eixo = "': (val) => \"R$ \" + Number(val).toLocaleString(\"pt-BR\", {minimumFractionDigits: 0, maximumFractionDigits: 0})'"
            js_formatter_label = "': (p) => \"R$ \" + Number(p.value).toLocaleString(\"pt-BR\", {minimumFractionDigits: 2, maximumFractionDigits: 2})'"

            # Dicionário dinâmico do eixo Y para alternar no modo de privacidade
            y_axis_config = {
                'type': 'value',
                'axisLabel': {'formatter': ' '} if priv_ativo else {':formatter': 'value => "R$ " + Number(value).toLocaleString("pt-BR")'}
            }

            tooltip_trigger = 'none' if priv_ativo else 'axis'

            # --- GRÁFICO 1: BARRAS HORIZONTAIS DE CATEGORIAS ---
            cat_ordenadas = sorted(despesas_por_categoria.items(), key=lambda x: x[1])
            cat_labels = [item[0] for item in cat_ordenadas if item[1] > 0]
            cat_valores = [round(item[1], 2) for item in cat_ordenadas if item[1] > 0]

            chart_bar_cat.options.clear()
            
            bar_series = {
                'name': 'Total Gasto',
                'type': 'bar',
                'data': cat_valores,
                'itemStyle': {
                    'color': '#8b5cf6',
                    'borderRadius': [0, 4, 4, 0]
                },
                'label': {
                    'show': not priv_ativo,
                    'position': 'right',
                    ':formatter': 'p => "R$ " + Number(p.value).toLocaleString("pt-BR", {minimumFractionDigits: 2, maximumFractionDigits: 2})'
                }
            }

            chart_bar_cat.options.update({
                'grid': {'left': '18%', 'right': '15%', 'bottom': '10%', 'top': '5%', 'containLabel': True},
                'tooltip': {
                    'show': not priv_ativo,
                    'trigger': 'axis',
                    'axisPointer': {'type': 'shadow'}
                },
                'xAxis': {
                    'type': 'value',
                    'axisLabel': {'formatter': ' '} if priv_ativo else {':formatter': 'v => "R$ " + Number(v).toLocaleString("pt-BR")'}
                },
                'yAxis': {
                    'type': 'category',
                    'data': cat_labels,
                    'axisLabel': {'fontSize': 12, 'color': '#334155'}
                },
                'series': [bar_series]
            })
            chart_bar_cat.update()

            # --- GRÁFICO 2: CAPITAL X DESPESAS ---
            chart_cap_desp.options.clear()
            chart_cap_desp.options.update({
                'grid': {'left': '10%', 'right': '5%', 'bottom': '15%', 'top': '10%'},
                'tooltip': {'show': not priv_ativo, 'trigger': tooltip_trigger},
                'legend': {'data': ['Despesas', 'Capital'], 'bottom': 0},
                'xAxis': {'type': 'category', 'data': meses_labels},
                'yAxis': y_axis_config,
                'series': [
                    {'name': 'Despesas', 'type': 'bar', 'data': [round(v, 2) for v in totais_despesas_mes], 'itemStyle': {'color': '#ef4444'}},
                    {'name': 'Capital', 'type': 'line', 'data': [round(v, 2) for v in totais_receitas_mes], 'itemStyle': {'color': '#3b82f6'}, 'lineStyle': {'type': 'dashed', 'width': 3}}
                ]
            })
            chart_cap_desp.update()

            # --- GRÁFICO 3: SALDO MENSAL (LÍQUIDO) ---
            chart_saldo_mes.options.clear()
            chart_saldo_mes.options.update({
                'grid': {'left': '10%', 'right': '5%', 'bottom': '10%', 'top': '15%'},
                'tooltip': {'show': not priv_ativo, 'trigger': tooltip_trigger},
                'xAxis': {'type': 'category', 'data': meses_labels},
                'yAxis': y_axis_config,
                'series': [{
                    'name': 'Saldo do Mês',
                    'type': 'line',
                    'smooth': True,
                    'symbolSize': 8,
                    'lineStyle': {'width': 3, 'color': '#0284c7'},
                    'itemStyle': {'color': '#0284c7'},
                    'areaStyle': {
                        'color': {
                            'type': 'linear',
                            'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                            'colorStops': [
                                {'offset': 0, 'color': 'rgba(2, 132, 199, 0.35)'},
                                {'offset': 1, 'color': 'rgba(2, 132, 199, 0.02)'}
                            ]
                        }
                    },
                    'label': {
                        'show': False
                    },
                    'data': [
                        {
                            'value': round(v, 2),
                            'itemStyle': {
                                'color': '#0284c7' if v >= 0 else '#ef4444'
                            }
                        }
                        for v in saldos_mensais
                    ]
                }]
            })
            chart_saldo_mes.update()

            # --- GRÁFICO 4: PROJEÇÃO - SALDO ACUMULADO ---
            chart_proj.options.clear()
            chart_proj.options.update({
                'grid': {'left': '10%', 'right': '5%', 'bottom': '10%', 'top': '10%'},
                'tooltip': {'show': not priv_ativo, 'trigger': tooltip_trigger},
                'xAxis': {'type': 'category', 'data': meses_labels},
                'yAxis': y_axis_config,
                'series': [{
                    'name': 'Saldo Acumulado',
                    'type': 'line',
                    'smooth': True,
                    'symbolSize': 6,
                    'lineStyle': {'width': 3, 'color': '#16a34a'},
                    'itemStyle': {'color': '#16a34a'},
                    'areaStyle': {
                        'color': {
                            'type': 'linear',
                            'x': 0, 'y': 0, 'x2': 0, 'y2': 1,
                            'colorStops': [
                                {'offset': 0, 'color': 'rgba(22, 163, 74, 0.35)'},
                                {'offset': 1, 'color': 'rgba(22, 163, 74, 0.02)'}
                            ]
                        }
                    },
                    'data': [round(v, 2) for v in saldos_acumulados]
                }]
            })
            chart_proj.update()

        def alternar_privacidade():
            modo_privado['ativo'] = not modo_privado['ativo']
            btn_privacidade.props(f"icon={'visibility_off' if modo_privado['ativo'] else 'visibility'}")
            atualizar_dashboard()

        # Gatilhos reativos
        f_ano_ini.on_value_change(lambda: atualizar_dashboard())
        f_ano_fim.on_value_change(lambda: atualizar_dashboard())
        f_receitas.on_value_change(gerenciar_mudanca_receitas)

        # Execução inicial
        atualizar_dashboard()

# Inicializa App NiceGUI
ui.run(title='Controle Financeiro', storage_secret='chave_secreta_super_segura_123')