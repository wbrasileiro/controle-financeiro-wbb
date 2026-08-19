from nicegui import ui
import plotly.graph_objects as go

ui.dark_mode().enable()

# --- DADOS E FUNÇÕES DE INTERAÇÃO ---
dados_periodo = {
    'Últimos 5 dias': {'datas': ['26/05', '27/05', '28/05', '29/05', '30/05'], 'valores': [130, 152, 115, 120, 127]},
    'Últimos 10 dias': {'datas': [f'Dia {i}' for i in range(1, 11)], 'valores': [100 + (i * 3) for i in range(1, 11)]},
    'Últimos 15 dias': {'datas': [f'Dia {i}' for i in range(1, 16)], 'valores': [100 + (i * 3) for i in range(1, 16)]},
    'Últimos 20 dias': {'datas': [f'Dia {i}' for i in range(1, 21)], 'valores': [100 + (i * 3) for i in range(1, 21)]},
    'Últimos 30 dias': {'datas': [f'D{i}' for i in range(1, 31)], 'valores': [90 + (i * 2) for i in range(1, 31)]}
}

def exportar_dados():
    ui.notify('Relatório exportado com sucesso!', type='positive', icon='download')

def atualizar_grafico(e):
    novo_periodo = e.value
    dados = dados_periodo[novo_periodo]
    
    # Atualiza a figura do Plotly
    fig.data[0].x = dados['datas']
    fig.data[0].y = dados['valores']
    
    # Notifica o NiceGUI para redesenhar o elemento na tela
    plot_element.update()
    ui.notify(f'Filtro aplicado: {novo_periodo}', type='info')

# --- BARRA LATERAL ---
with ui.left_drawer(value=True).classes('bg-slate-900 border-r border-slate-800 p-4'):
    ui.label('ANÁLISE DE CONTRATOS').classes('text-xs font-bold tracking-wider text-slate-400 mb-6')
    
    with ui.column().classes('w-full gap-2'):
        ui.button('Dashboard', icon='dashboard', on_click=lambda: ui.notify('Você já está no Dashboard')).props('flat align=left').classes('w-full text-blue-400 bg-slate-800/50')
        ui.button('Contratos', icon='description', on_click=lambda: ui.notify('Navegando para Contratos...')).props('flat align=left').classes('w-full text-slate-400')
        ui.button('Relatórios', icon='bar_chart', on_click=lambda: ui.notify('Navegando para Relatórios...')).props('flat align=left').classes('w-full text-slate-400')
        ui.button('Configurações', icon='settings', on_click=lambda: ui.notify('Navegando para Configurações...')).props('flat align=left').classes('w-full text-slate-400')

# --- CABEÇALHO ---
with ui.header().classes('bg-slate-900 border-b border-slate-800 text-white items-center justify-between px-6 py-3'):
    ui.label('Painel de Gestão').classes('text-lg font-semibold')
    with ui.row().classes('items-center gap-4'):
        ui.avatar('person', color='blue-6', text_color='white')

# --- CONTEÚDO PRINCIPAL ---
with ui.column().classes('w-full p-6 bg-slate-950 gap-6 max-w-7xl mx-auto'):
    
    # SEÇÃO DE FILTROS (Com os eventos on_change e on_click vinculados)
    with ui.row().classes('w-full items-center justify-between bg-slate-900 p-4 rounded-xl border border-slate-800'):
        ui.label('Filtros de Análise').classes('text-md font-medium text-slate-300')
        
        with ui.row().classes('gap-4 items-center'):
            ui.select(
                options=['Últimos 5 dias', 'Últimos 10 dias', 'Últimos 15 dias', 'Últimos 20 dias', 'Últimos 30 dias'], 
                value='Últimos 5 dias',
                on_change=atualizar_grafico
            ).props('outlined dense dark').classes('w-48 bg-slate-800 rounded-lg')
            
            ui.button('Exportar', icon='download', on_click=exportar_dados).props('outline color=blue dense').classes('px-3')

    # SEÇÃO DE MÉTRICAS
    with ui.grid(columns=3).classes('w-full gap-4'):
        with ui.card().classes('bg-slate-900 border border-slate-800 p-4 rounded-xl'):
            ui.label('Total de Contratos').classes('text-xs text-slate-400 font-medium')
            ui.label('667').classes('text-2xl font-bold text-white mt-1')
            ui.label('+12% em relação à semana passada').classes('text-xs text-emerald-400 mt-2')
            
        with ui.card().classes('bg-slate-900 border border-slate-800 p-4 rounded-xl'):
            ui.label('Média Diária').classes('text-xs text-slate-400 font-medium')
            ui.label('133.4').classes('text-2xl font-bold text-white mt-1')
            ui.label('Estável').classes('text-xs text-blue-400 mt-2')

        with ui.card().classes('bg-slate-900 border border-slate-800 p-4 rounded-xl'):
            ui.label('Taxa de Aprovação').classes('text-xs text-slate-400 font-medium')
            ui.label('94.2%').classes('text-2xl font-bold text-white mt-1')
            ui.label('+2.1% este mês').classes('text-xs text-emerald-400 mt-2')

    # SEÇÃO DO GRÁFICO
    with ui.card().classes('w-full bg-slate-900 border border-slate-800 p-4 rounded-xl gap-2'):
        ui.label('Evolução de Contratos Analisados').classes('text-sm font-semibold text-slate-200')
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dados_periodo['Últimos 5 dias']['datas'], 
            y=dados_periodo['Últimos 5 dias']['valores'], 
            mode='lines+markers',
            line=dict(color='#60A5FA', width=3),
            marker=dict(size=8, color='#3B82F6')
        ))
        
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis=dict(showgrid=True, gridcolor='#1E293B', color='#94A3B8'),
            yaxis=dict(showgrid=True, gridcolor='#1E293B', color='#94A3B8'),
            height=320
        )
        
        plot_element = ui.plotly(fig).classes('w-full h-80')

import os

# Substitua o ui.run() final por este bloco:
ui.run(
    title='Análise de Contratos',
    host='0.0.0.0', # Permite acesso externo no servidor
    port=int(os.environ.get('PORT', 8080)), # Captura a porta da nuvem ou usa 8080 localmente
    reload=False
)