# Método e fluxos dos módulos

Esta documentação separa o método matemático de estroboscopia digital das limitações das ferramentas computacionais. A ideia central é preservar contratos claros entre módulos: o rastreador pode evoluir, a biblioteca pode ser substituída, mas a tabela cinemática final deve manter a mesma estrutura.

## Fluxo dos módulos

![Fluxo dos módulos do aplicativo](figures/fluxo_modulos_app.png)

O aplicativo é organizado em blocos: entrada Streamlit, estado, galeria, calibração, rastreio, cinemática, filtro, visualização, CSV e relatório. Cada bloco possui uma responsabilidade pequena e um contrato de entrada/saída.

## Método matemático

![Método matemático da estroboscopia digital](figures/fluxo_metodo_matematico.png)

O método começa com o vídeo e a seleção do objeto. Em seguida, a escala espacial é definida por dois pontos ou por homografia métrica. O rastreio fornece posições, a calibração converte essas posições para unidades reais, o filtro Savitzky-Golay suaviza a trajetória e as derivadas produzem velocidades e acelerações. Os modelos ajustados interpretam o movimento.

## Contrato dos dados

![Contrato de dados do pipeline](figures/contrato_dados_pipeline.png)

A tabela cinemática é o contrato central do projeto:

```text
frame, tempo_s, pos_x_px, pos_y_px, pos_x_um, pos_y_um,
vx_um_s, vy_um_s, ax_um_s2, ay_um_s2
```

Quando a homografia métrica está ativa, `pos_x_px` e `pos_y_px` representam o ponto no plano retificado usado para cálculo métrico. Para preservar a visualização sobre o vídeo original, a tabela também registra `view_x_px` e `view_y_px`, que indicam o centro do objeto no frame não distorcido. Essa separação impede que gráficos, vetores e imagens sobre o vídeo disputem o mesmo sistema de coordenadas.

Esse contrato permite que o método matemático seja preservado mesmo se futuramente o rastreador CSRT for trocado por outro algoritmo.

## Etapas matemáticas principais

| Etapa | Fórmula / regra | Interpretação |
| --- | --- | --- |
| Centro do objeto | `p_x = x_caixa + w/2`, `p_y = y_caixa + h/2` | Reduz a caixa do rastreador a um ponto representativo. |
| Tempo | `t = (frame - frame_inicial) / FPS` | Converte frames em segundos. |
| Escala | `S = d_real / d_px` | Converte pixel em unidade real. |
| Coordenadas físicas | `X = (p_x - O_x)S`, `Y = -(p_y - O_y)S` | Coloca a origem no sistema definido pelo usuário. |
| Homografia métrica | `p' = H p` | Projeta pontos do vídeo para um plano métrico sem distorcer a visualização do vídeo. |
| Modelo horizontal | `X(t) = v_x t + X_0` | Representa velocidade horizontal aproximadamente constante. |
| Modelo vertical | `Y(t) = at² + bt + c`, `a_y = 2a` | Estima aceleração vertical a partir do coeficiente quadrático. |
| Savitzky-Golay | ajuste polinomial local de ordem `d` em janela `w` | Suaviza a trajetória e permite derivadas numéricas. |

## Estudo estatístico da aceleração vertical

![Estudo estatístico da aceleração vertical](figures/estudo_estatistico_aceleracao_y.png)

O relatório final destaca a aceleração vertical porque ela permite discutir a gravidade no lançamento oblíquo. A linha verde representa a média de \(a_y\), a linha roxa representa a mediana e a faixa sombreada indica média ± um desvio padrão. Quanto menor essa faixa, mais estável foi a estimativa da aceleração ao longo do vídeo analisado.

## Imagens geradas

Os diagramas desta pasta são gerados por:

```bash
python scripts/generate_documentation_diagrams.py
```

Arquivos produzidos:

- `docs/figures/fluxo_modulos_app.png`
- `docs/figures/fluxo_metodo_matematico.png`
- `docs/figures/contrato_dados_pipeline.png`
- `docs/figures/estudo_estatistico_aceleracao_y.png`
