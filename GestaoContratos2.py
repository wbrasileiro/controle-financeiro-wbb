import os
import flet as ft
import flet_charts as fch
import pandas as pd


# Função para carregar os dados do CSV
def carregar_dados():
    caminho_atual = os.path.dirname(__file__)
    caminho_csv = os.path.join(caminho_atual, "resultados.csv")
    return pd.read_csv(caminho_csv)


def main(page: ft.Page):
    # Configurações de simulador mobile
    page.window.width = 390
    page.window.height = 844
    page.window.resizable = False
    page.window.center()

    page.title = "Contratos Mobile"
    page.padding = 15
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = ft.Colors.WHITE

    # Converte os dados para pontos do gráfico
    def gerar_pontos_grafico(df):
        pontos = []
        for i, row in enumerate(df.itertuples()):
            pontos.append(fch.LineChartDataPoint(i, float(row.Contratos)))
        return pontos

    # Cria os rótulos de datas para o Eixo X
    def gerar_eixo_x(df):
        labels = []
        # Exibe no máximo 4 a 5 datas para caber na tela do celular
        passo = max(1, len(df) // 4)

        for i, row in enumerate(df.itertuples()):
            if i % passo == 0 or i == len(df) - 1:
                data_completa = str(getattr(row, "Data", i))

                # Trata a data para exibir apenas DD/MM (reduz tamanho)
                if "/" in data_completa:
                    partes = data_completa.split("/")
                    data_curta = (
                        f"{partes[0]}/{partes[1]}"
                        if len(partes) >= 2
                        else data_completa
                    )
                else:
                    data_curta = data_completa

                labels.append(
                    fch.ChartAxisLabel(
                        value=i,
                        label=ft.Container(
                            content=ft.Text(
                                data_curta,
                                size=9,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREY_700,
                            ),
                            margin=ft.Margin(top=5),
                        ),
                    )
                )

        # Sem o parâmetro labels_size para evitar o erro
        return fch.ChartAxis(labels=labels)

    # Função chamada ao alterar o Dropdown
    def mudou_periodo(e):
        num_dias = int(dropdown_dias.value.replace(" dias", ""))
        df_filtrado = carregar_dados().tail(num_dias)

        chart.data_series[0].points = gerar_pontos_grafico(df_filtrado)
        chart.bottom_axis = gerar_eixo_x(df_filtrado)
        page.update()

    # --- Componentes ---
    titulo = ft.Text("Análise de contratos", size=24, weight=ft.FontWeight.BOLD)

    link_portfolio = ft.Markdown(
        "Conheça meu portfólio [Clique"
        " aqui](https://sites.google.com/view/portfolio-de-evidencias-wbb?usp=sharing)"
    )

    dropdown_dias = ft.Dropdown(
        label="Escolha o período desejado",
        value="20 dias",
        options=[
            ft.dropdown.Option("5 dias"),
            ft.dropdown.Option("10 dias"),
            ft.dropdown.Option("20 dias"),
            ft.dropdown.Option("30 dias"),
        ],
        on_select=mudou_periodo,
        width=float("inf"),
    )

    df_inicial = carregar_dados().tail(20)

    chart = fch.LineChart(
        data_series=[
            fch.LineChartData(
                points=gerar_pontos_grafico(df_inicial),
                stroke_width=3,
                color=ft.Colors.BLUE,
                curved=True,
            )
        ],
        bottom_axis=gerar_eixo_x(df_inicial),
        border=ft.Border(
            bottom=ft.BorderSide(1, ft.Colors.GREY_300),
            left=ft.BorderSide(1, ft.Colors.GREY_300),
        ),
        expand=True,
        height=320,
    )

    page.add(
        ft.Column(
            [
                titulo,
                link_portfolio,
                ft.Divider(height=10, color=ft.Colors.TRANSPARENT),
                dropdown_dias,
                ft.Container(
                    content=chart,
                    margin=ft.Margin(top=20),
                    padding=ft.Padding(
                        left=10, right=20, top=0, bottom=10
                    ),  # Padding para evitar o corte do texto
                ),
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
    )


if __name__ == "__main__":
    ft.run(main)