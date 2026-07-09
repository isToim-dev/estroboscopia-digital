from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "figuras_estroboscopia"
OUT.mkdir(exist_ok=True)

# A4 portrait at 300 dpi.
W, H = 2480, 3508
MARGIN = 130

FONT_REGULAR = "C:/Windows/Fonts/arial.ttf"
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"


def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT_REGULAR, size)


PALETTE = {
    "ink": "#172033",
    "muted": "#516070",
    "bg": "#F7F9FC",
    "line": "#8BA0B6",
    "blue": "#DDEBFF",
    "blue_border": "#2E6DB4",
    "green": "#DFF5EA",
    "green_border": "#238052",
    "orange": "#FFF0D8",
    "orange_border": "#C06B14",
    "purple": "#EFE5FF",
    "purple_border": "#7153B8",
    "red": "#FFE3E3",
    "red_border": "#B84848",
    "gray": "#E9EEF5",
    "gray_border": "#697789",
    "yellow": "#FFF7C7",
    "yellow_border": "#A67C00",
}


def new_canvas(title, subtitle):
    img = Image.new("RGB", (W, H), PALETTE["bg"])
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, H], fill=PALETTE["bg"])
    d.text((MARGIN, 95), title, fill=PALETTE["ink"], font=font(66, True))
    if subtitle:
        d.text((MARGIN, 180), subtitle, fill=PALETTE["muted"], font=font(34))
    d.line([MARGIN, 245, W - MARGIN, 245], fill="#D5DEE9", width=3)
    return img, d


def wrap_text(draw, text, max_width, font_obj):
    lines = []
    for raw in text.split("\n"):
        words = raw.split()
        if not words:
            lines.append("")
            continue
        line = words[0]
        for word in words[1:]:
            trial = f"{line} {word}"
            if draw.textbbox((0, 0), trial, font=font_obj)[2] <= max_width:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def rounded_box(draw, xy, title, body="", fill="#FFFFFF", border="#000000",
                title_size=34, body_size=27, radius=34, width=5,
                center=False):
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=border, width=width)
    title_font = font(title_size, True)
    body_font = font(body_size)
    pad_x = 34
    pad_y = 26
    max_width = (x2 - x1) - 2 * pad_x
    y = y1 + pad_y
    title_lines = wrap_text(draw, title, max_width, title_font)
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        tx = x1 + ((x2 - x1 - (bbox[2] - bbox[0])) / 2 if center else pad_x)
        draw.text((tx, y), line, fill=PALETTE["ink"], font=title_font)
        y += title_size + 11
    if body:
        y += 10
        for line in wrap_text(draw, body, max_width, body_font):
            bbox = draw.textbbox((0, 0), line, font=body_font)
            tx = x1 + ((x2 - x1 - (bbox[2] - bbox[0])) / 2 if center else pad_x)
            draw.text((tx, y), line, fill=PALETTE["muted"], font=body_font)
            y += body_size + 12


def center(xy):
    x1, y1, x2, y2 = xy
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def edge_point(box, target):
    cx, cy = center(box)
    tx, ty = target
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    x1, y1, x2, y2 = box
    hw, hh = (x2 - x1) / 2, (y2 - y1) / 2
    scale = max(abs(dx) / hw, abs(dy) / hh)
    return cx + dx / scale, cy + dy / scale


def arrow(draw, start, end, color="#8BA0B6", width=6):
    draw.line([start, end], fill=color, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    head = 26
    left = (end[0] - head * math.cos(angle - math.pi / 6),
            end[1] - head * math.sin(angle - math.pi / 6))
    right = (end[0] - head * math.cos(angle + math.pi / 6),
             end[1] - head * math.sin(angle + math.pi / 6))
    draw.polygon([end, left, right], fill=color)


def connect(draw, box_a, box_b, color="#8BA0B6"):
    ca, cb = center(box_a), center(box_b)
    start = edge_point(box_a, cb)
    end = edge_point(box_b, ca)
    arrow(draw, start, end, color=color)


def footer(draw, text):
    draw.line([MARGIN, H - 135, W - MARGIN, H - 135], fill="#D5DEE9", width=3)
    draw.text((MARGIN, H - 105), text, fill=PALETTE["muted"], font=font(25))


def save(img, name):
    png = OUT / f"{name}.png"
    pdf = OUT / f"{name}.pdf"
    img.save(png, dpi=(300, 300))
    img.save(pdf, "PDF", resolution=300)
    return png, pdf


def mapa_geral():
    img, d = new_canvas(
        "Mapa mental 1 - Estroboscopia digital",
        "O método matemático é uma cadeia de transformação: vídeo, dados, modelo e interpretação.",
    )
    central = (720, 1260, 1760, 1780)
    rounded_box(d, central, "Método matemático central",
                "Converter uma sequência temporal de imagens em uma sequência de posições mensuráveis.",
                PALETTE["yellow"], PALETTE["yellow_border"], 45, 32, center=True)

    boxes = [
        ((170, 430, 850, 720), "1. Fenômeno filmado",
         "Movimento real projetado no plano da imagem.", PALETTE["blue"], PALETTE["blue_border"]),
        ((1020, 390, 1740, 710), "2. Amostragem temporal",
         "O vídeo vira frames; Δt = 1/FPS.", PALETTE["blue"], PALETTE["blue_border"]),
        ((1690, 780, 2320, 1090), "3. Calibração espacial",
         "Pixels são convertidos em unidade física por escala.", PALETTE["green"], PALETTE["green_border"]),
        ((1690, 1390, 2320, 1700), "4. Rastreamento",
         "A ferramenta estima o centro do objeto em cada frame.", PALETTE["orange"], PALETTE["orange_border"]),
        ((1470, 2110, 2220, 2430), "5. Série de dados",
         "Pares (t, x, y) organizam a trajetória observada.", PALETTE["green"], PALETTE["green_border"]),
        ((760, 2540, 1720, 2860), "6. Tratamento matemático",
         "Suavização, derivadas numéricas e ajuste de modelos.", PALETTE["purple"], PALETTE["purple_border"]),
        ((180, 2110, 880, 2430), "7. Imagem estroboscópica",
         "Sobreposição visual das posições sucessivas.", PALETTE["orange"], PALETTE["orange_border"]),
        ((170, 900, 850, 1210), "8. Interpretação didática",
         "Gráficos, função quadrática, vetores e erro experimental.", PALETTE["red"], PALETTE["red_border"]),
    ]
    for box, title, body, fill, border in boxes:
        rounded_box(d, box, title, body, fill, border)
        connect(d, central, box)

    footer(d, "Uso sugerido: abrir a seção do apêndice mostrando que a robustez está na cadeia matemática, não em uma biblioteca específica.")
    return save(img, "01_mapa_metodo_estroboscopia_digital_A4")


def mapa_blocos():
    img, d = new_canvas(
        "Mapa mental 2 - Blocos matemáticos do cálculo",
        "Cada bloco pode virar um módulo do código, com entrada, fórmula e saída verificável.",
    )
    boxes = [
        ((150, 420, 1080, 760), "A. Entrada do vídeo",
         "Entrada: arquivo de vídeo.\nSaída: frames I_i e FPS f_s.\nTempo: t_i = (i - i0)/f_s.",
         PALETTE["blue"], PALETTE["blue_border"]),
        ((1400, 420, 2330, 760), "B. Referencial e escala",
         "Entrada: origem O e distância real D_real.\nEscala: S = D_real / D_pixels.\nDefine a unidade de medida.",
         PALETTE["green"], PALETTE["green_border"]),
        ((150, 1030, 1080, 1390), "C. Conversão de coordenadas",
         "x = (p_x - p_x0)S\ny = -(p_y - p_y0)S\nO sinal inverte o eixo vertical da imagem.",
         PALETTE["green"], PALETTE["green_border"]),
        ((1400, 1030, 2330, 1390), "D. Centro do objeto",
         "Bounding box: (x_b, y_b, w, h)\nCentro: p_x = x_b + w/2\nCentro: p_y = y_b + h/2.",
         PALETTE["orange"], PALETTE["orange_border"]),
        ((150, 1640, 1080, 2020), "E. Série temporal",
         "Tabela: (frame, t, x, y).\nÉ a ponte entre imagem e cálculo.\nEste bloco deve ser auditável.",
         PALETTE["blue"], PALETTE["blue_border"]),
        ((1400, 1640, 2330, 2020), "F. Suavização",
         "Savitzky-Golay ajusta polinômios locais.\nReduz ruído antes de derivar.\nParâmetros: janela w e grau d.",
         PALETTE["purple"], PALETTE["purple_border"]),
        ((150, 2290, 1080, 2670), "G. Derivadas numéricas",
         "v_x ≈ dx/dt, v_y ≈ dy/dt\na_x ≈ d²x/dt², a_y ≈ d²y/dt².\nRuído cresce na segunda derivada.",
         PALETTE["purple"], PALETTE["purple_border"]),
        ((1400, 2290, 2330, 2670), "H. Modelagem",
         "Linear: S(t)=vt+S0.\nQuadrática: S(t)=at²+bt+c.\nAceleração estimada: A=2a.",
         PALETTE["red"], PALETTE["red_border"]),
    ]
    for box, title, body, fill, border in boxes:
        rounded_box(d, box, title, body, fill, border, body_size=28)
    for i in range(len(boxes) - 1):
        connect(d, boxes[i][0], boxes[i + 1][0])

    note = (520, 2920, 1960, 3180)
    rounded_box(d, note, "Ideia-chave para reorganizar o código",
                "Cada bloco deve receber dados claros, devolver dados claros e poder ser testado sem depender da interface Streamlit.",
                PALETTE["yellow"], PALETTE["yellow_border"], 40, 31, center=True)
    footer(d, "Uso sugerido: transformar esta prancha em roteiro para modularizar funções e trocar bibliotecas sem alterar o método.")
    return save(img, "02_mapa_blocos_matematicos_A4")


def mapa_limites():
    img, d = new_canvas(
        "Mapa mental 3 - Método robusto, ferramentas limitadas",
        "A falha de rastreamento não invalida a matemática; ela indica limite da implementação escolhida.",
    )
    central = (740, 1230, 1740, 1710)
    rounded_box(d, central, "Núcleo robusto",
                "A relação entre frames, coordenadas, escala, tempo, derivadas e modelo permanece válida.",
                PALETTE["yellow"], PALETTE["yellow_border"], 45, 32, center=True)

    left = [
        ((150, 430, 920, 740), "Pressupostos matemáticos",
         "Referencial definido, escala coerente, FPS conhecido, dados ordenados no tempo.",
         PALETTE["green"], PALETTE["green_border"]),
        ((150, 940, 920, 1250), "Validação dos dados",
         "Conferir trajetória, unidades, dispersão, R² e coerência física dos parâmetros.",
         PALETTE["green"], PALETTE["green_border"]),
        ((150, 1950, 920, 2260), "Erro experimental",
         "Perspectiva, calibração, baixa taxa de quadros, compressão e iluminação afetam a medição.",
         PALETTE["orange"], PALETTE["orange_border"]),
        ((150, 2460, 920, 2770), "Decisão didática",
         "Quando há erro, discute-se método científico, repetição e qualidade da coleta.",
         PALETTE["blue"], PALETTE["blue_border"]),
    ]
    right = [
        ((1560, 430, 2330, 740), "Limite do CSRT",
         "Pode falhar por oclusão, baixo contraste, objeto deformável ou saída da cena.",
         PALETTE["red"], PALETTE["red_border"]),
        ((1560, 940, 2330, 1250), "Limite de biblioteca",
         "Algumas funções existem apenas no OpenCV contrib; trocar pacote pode quebrar o app.",
         PALETTE["red"], PALETTE["red_border"]),
        ((1560, 1950, 2330, 2260), "Limite de interface",
         "Streamlit organiza o fluxo, mas não deve conter toda a lógica matemática misturada.",
         PALETTE["purple"], PALETTE["purple_border"]),
        ((1560, 2460, 2330, 2770), "Substituição possível",
         "Trocar rastreador ou biblioteca mantendo a tabela (t, x, y) como contrato do método.",
         PALETTE["blue"], PALETTE["blue_border"]),
    ]
    for group in (left, right):
        for box, title, body, fill, border in group:
            rounded_box(d, box, title, body, fill, border)
            connect(d, central, box)
    bottom = (560, 2960, 1920, 3210)
    rounded_box(d, bottom, "Formulação para a dissertação",
                "O método de estroboscopia digital é matematicamente robusto; as limitações observadas decorrem das condições experimentais e das ferramentas computacionais adotadas.",
                PALETTE["gray"], PALETTE["gray_border"], 39, 30, center=True)
    connect(d, central, bottom)
    footer(d, "Uso sugerido: responder à banca distinguindo problema de método, problema de medição e problema de implementação.")
    return save(img, "03_mapa_robustez_e_limitacoes_A4")


def mapa_modularizacao():
    img, d = new_canvas(
        "Mapa mental 4 - Modularização sugerida do software",
        "Organizar o código por contratos matemáticos facilita testes e troca de bibliotecas.",
    )
    central = (660, 1260, 1820, 1720)
    rounded_box(d, central, "Contrato comum",
                "Toda implementação deve produzir uma tabela limpa: frame, tempo, x, y, vx, vy, ax, ay.",
                PALETTE["yellow"], PALETTE["yellow_border"], 43, 31, center=True)

    modules = [
        ((160, 430, 990, 750), "video_io.py",
         "Lê vídeo, extrai FPS, frames e metadados.\nBibliotecas substituíveis: OpenCV, imageio, ffmpeg.",
         PALETTE["blue"], PALETTE["blue_border"]),
        ((1490, 430, 2320, 750), "calibracao.py",
         "Calcula escala, origem, unidade e homografia.\nSaída: transformações aplicáveis aos pontos.",
         PALETTE["green"], PALETTE["green_border"]),
        ((160, 980, 990, 1300), "rastreamento.py",
         "Recebe frames e devolve centros em pixels.\nCSRT é uma opção, não o método inteiro.",
         PALETTE["orange"], PALETTE["orange_border"]),
        ((1490, 980, 2320, 1300), "cinematica.py",
         "Converte pontos em série temporal.\nCalcula velocidade, aceleração e módulos vetoriais.",
         PALETTE["purple"], PALETTE["purple_border"]),
        ((160, 1960, 990, 2280), "modelagem.py",
         "Ajusta modelos lineares/quadráticos.\nCalcula R² e parâmetros físicos interpretáveis.",
         PALETTE["red"], PALETTE["red_border"]),
        ((1490, 1960, 2320, 2280), "visualizacao.py",
         "Gera gráficos, vetores e imagem estroboscópica.\nNão deve alterar os dados brutos.",
         PALETTE["blue"], PALETTE["blue_border"]),
        ((160, 2520, 990, 2840), "validacao.py",
         "Testa unidades, FPS, escala, número de pontos e coerência física.",
         PALETTE["green"], PALETTE["green_border"]),
        ((1490, 2520, 2320, 2840), "app_streamlit.py",
         "Cuida da interface: upload, botões, parâmetros e downloads.",
         PALETTE["gray"], PALETTE["gray_border"]),
    ]
    for box, title, body, fill, border in modules:
        rounded_box(d, box, title, body, fill, border, body_size=27)
        connect(d, central, box)

    bottom = (480, 3040, 2000, 3220)
    rounded_box(d, bottom, "Critério de compatibilidade",
                "Se uma biblioteca nova entrega o mesmo contrato de dados, ela pode substituir a anterior sem reescrever a matemática.",
                PALETTE["yellow"], PALETTE["yellow_border"], 36, 28, center=True)
    footer(d, "Uso sugerido: orientar refatoração futura do produto educacional e justificar escolhas técnicas.")
    return save(img, "04_mapa_modularizacao_codigo_A4")


def main():
    outputs = []
    for maker in (mapa_geral, mapa_blocos, mapa_limites, mapa_modularizacao):
        outputs.extend(maker())
    print("Arquivos gerados:")
    for path in outputs:
        print(path)


if __name__ == "__main__":
    main()
