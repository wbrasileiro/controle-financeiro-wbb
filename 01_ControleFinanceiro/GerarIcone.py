import os
from PIL import Image, ImageDraw, ImageFont

def gerar_icone_app():
    # Tamanho de alta resolução para ícone PWA/Web
    size = 512
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # 1. Criar fundo quadrado com cantos arredondados (estilo iOS/Android moderno)
    radius = 110
    
    # Desenhar gradiente de fundo (Azul moderno para Roxo)
    for y in range(size):
        # Interpolação de cor
        r = int(37 + (124 - 37) * (y / size))
        g = int(99 + (58 - 99) * (y / size))
        b = int(235 + (237 - 235) * (y / size))
        draw.line([(0, y), (size, y)], fill=(r, g, b, 255))

    # Máscara de cantos arredondados
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, size, size], radius=radius, fill=255)
    
    # Aplica os cantos arredondados
    app_icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    app_icon.paste(image, (0, 0), mask)
    draw_icon = ImageDraw.Draw(app_icon)

    # 2. Desenhar elemento gráfico no centro (Carteira/Símbolo Financeiro)
    # Símbolo estilizado: Círculo central com brilho e barra de crescimento
    center = size // 2
    
    # Círculo interno translúcido
    draw_icon.ellipse(
        [center - 160, center - 160, center + 160, center + 160],
        fill=(255, 255, 255, 35)
    )

    # Barras de crescimento / Carteira estilizada
    # Barra 1
    draw_icon.rounded_rectangle([center - 100, center + 20, center - 50, center + 100], radius=12, fill=(255, 255, 255, 220))
    # Barra 2
    draw_icon.rounded_rectangle([center - 30, center - 30, center + 20, center + 100], radius=12, fill=(255, 255, 255, 240))
    # Barra 3 (Mais alta)
    draw_icon.rounded_rectangle([center + 40, center - 90, center + 90, center + 100], radius=12, fill=(255, 255, 255, 255))
    
    # Seta de tendência de alta (subindo)
    draw_icon.polygon([
        (center + 65, center - 130),
        (center + 110, center - 85),
        (center + 80, center - 85),
        (center + 40, center - 125)
    ], fill=(52, 211, 153, 255)) # Verde esmeralda moderno

    # 3. Salvar arquivos
    os.makedirs("static", exist_ok=True)
    
    # Favicon padrão da aba
    app_icon.resize((64, 64), Image.Resampling.LANCZOS).save("favicon.ico", format="ICO")
    # Ícone PNG de alta resolução para PWA e telas de download
    app_icon.save("static/icon-512.png", format="PNG")
    app_icon.resize((192, 192), Image.Resampling.LANCZOS).save("static/icon-192.png", format="PNG")

    print("✅ Ícones gerados com sucesso na pasta do seu projeto!")

if __name__ == "__main__":
    gerar_icone_app()