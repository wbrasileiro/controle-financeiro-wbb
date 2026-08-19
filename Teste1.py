from datetime import datetime
from nicegui import ui

# Captura e formata a data/hora atual (exemplo: 15/08/2026 - 14:35)
agora = datetime.now().strftime('%d/%m/%Y - %H:%M')

ui.label('Teste label!')
ui.link('Clique em meu portfólio!', 'https://sites.google.com/view/portfolio-de-evidencias')

ui.chat_message(
    'Quem é vc?',
    name='WBB',
    stamp=agora,
    avatar='https://api.dicebear.com/7.x/bottts/svg?seed=WBB',
)

ui.chat_message(
    'Sou a Gildete, filha do Deusdete e Dna Maria lá de Eugênio Barros - MA.',
    name='Gil',
    stamp=agora,
    avatar='https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100',
)

ui.chat_message(
    'Qual o nome do seu cachorro?',
    name='WBB',
    stamp=agora,
    avatar='https://api.dicebear.com/7.x/bottts/svg?seed=WBB',
)

ui.chat_message(
    'Billy, ué.' \
    ' Sou a mãe do Vitor.',
    name='Gil',
    stamp=agora,
    avatar='https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100',
)

ui.chat_message(
    'Então vc é minha esposa. Kkkkk',
    name='WBB',
    stamp=agora,
    avatar='https://api.dicebear.com/7.x/bottts/svg?seed=WBB',
)

ui.run()
