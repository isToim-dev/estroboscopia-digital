# 🔬 Gerador de Imagem Estroboscópica e Dados de Trajetória

Este projeto foi desenvolvido como parte de um trabalho de conclusão de curso do Mestrado Profissional em Matemática em Rede Nacional (PROFMAT) na Universidade Federal de Uberlândia (UFU).

---

## Autoria e Orientação

* **Aluno de Mestrado:** Antônio Marcos da Silva Leite
* **Professor Orientador:** Prof. Dr. Rafael Figueiredo
* **Instituição:** Instituto de Matemática e Estatística da Universidade Federal de Uberlândia (IME-UFU)
* **Programa:** Mestrado Profissional em Matemática em Rede Nacional (PROFMAT)

---

Uma aplicação web construída com Streamlit e OpenCV para analisar o movimento de objetos em vídeos. A ferramenta gera uma imagem estroboscópica que visualiza a trajetória do objeto e exporta dados de posição frame a frame para um arquivo CSV.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.44.1-ff4b4b.svg)](https://streamlit.io)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.12.0-5C3EE8.svg)](https://opencv.org/)

---

## 🚀 Link para a Aplicação Web

**[Acesse a aplicação aqui!](https://estroboscopia-digital-5lqlcjeub9abnhzgaepxvl.streamlit.app/)**

---

## ✨ Funcionalidades

- **Upload de Vídeo:** Suporte para os formatos de vídeo mais comuns (MP4, AVI, MOV).
- **Seleção Interativa de Objeto:** Uma grade de referência cartesiana (origem no canto inferior esquerdo) e uma pré-visualização em tempo real do *bounding box* permitem uma seleção precisa do objeto de interesse.
- **Geração de Imagem Estroboscópica:** Cria uma única imagem composta que mostra o objeto em múltiplas posições ao longo do tempo.
- **Exportação de Dados de Trajetória:** Gera um arquivo `.csv` com a posição (relativa e absoluta) do centro do objeto em cada frame do vídeo.
- **Densidade Estroboscópica Guiada:** Escolha entre três presets visuais de marcação da trajetória: poucos pontos, densidade média ou muitos pontos.
- **Homografia Métrica:** Use linhas de um plano conhecido ou retângulos reais do cenário para corrigir perspectiva e definir escala espacial em vídeos não ortogonais.
- **Savitzky-Golay Reverso:** Estima um par exato de janela e ordem do filtro a partir da trajetória rastreada, minimizando custo computacional sem sair do erro mínimo admissível.

---

## 💡 Dicas para Melhores Resultados

-   **Câmera Estritamente Estática:** Para um resultado preciso, é fundamental que o vídeo tenha sido gravado com a **câmera completamente parada**. Qualquer movimento, vibração ou ajuste de zoom na câmera durante a gravação pode interferir na lógica de rastreamento e comprometer a qualidade da imagem e dos dados gerados.
-   **Bom Contraste:** Vídeos onde o objeto em movimento tem um bom contraste em relação ao fundo tendem a produzir resultados mais confiáveis.
-   **Seleção Precisa:** Dedique um momento para ajustar o retângulo de seleção azul para que ele envolva o objeto de forma justa na sua posição inicial. Uma seleção precisa é a chave para um rastreamento bem-sucedido.

---

## 🛠️ Tecnologias Utilizadas

- **Backend:** Python
- **Processamento de Imagem e Vídeo:** OpenCV (`opencv-contrib-python-headless`)
- **Interface Web:** Streamlit
- **Manipulação de Dados:** Pandas & NumPy
- **Hospedagem:** Streamlit Community Cloud

### Versões fixadas para reprodutibilidade

O arquivo `requirements.txt` fixa as versões das bibliotecas Python para evitar
que atualizações futuras quebrem a execução do aplicativo. No Streamlit Community
Cloud, selecione Python 3.11 nas configurações avançadas do app; o `runtime.txt`
fica no repositório como registro documental da versão usada.

| Ferramenta / biblioteca | Versão |
| --- | --- |
| Python | 3.11 |
| opencv-contrib-python-headless | 4.12.0.88 |
| NumPy | 2.2.5 |
| Streamlit | 1.44.1 |
| Pandas | 2.2.3 |
| SciPy | 1.17.1 |
| Matplotlib | 3.10.9 |
| Pillow | 11.1.0 |
| streamlit-image-coordinates | 0.4.0 |
| ReportLab | 4.4.10 |
| ffmpeg, libsm6, libxext6, libgl1 | Instalados pelo `packages.txt` no ambiente Linux |

Observação: o rastreamento CSRT depende do pacote `opencv-contrib-python-headless`;
substituí-lo por `opencv-python` pode remover `cv2.TrackerCSRT_create()` e impedir
o funcionamento do rastreador.

---

## 📂 Estrutura do Projeto
```text
├── stroboscopic_app.py              # Entrada Streamlit e orquestração da interface
├── app_config.py                    # Constantes, CSS e presets da interface
├── app_state.py                     # Contratos de estado do vídeo no Streamlit
├── sample_videos.py                 # Descoberta, metadados e miniaturas dos vídeos de validação
├── video_processing.py              # Rastreamento, tabela cinemática e imagem estroboscópica
├── visualization.py                 # Gráficos, grade cartesiana e vetores de velocidade
├── perspective_calibration.py       # Homografia métrica para vídeos não ortogonais
├── savgol_reverse.py                # Otimização reversa do filtro Savitzky-Golay
├── ui_controls.py                   # Controles visuais reutilizáveis da interface
├── report_generation.py             # Relatório PDF estruturado para o estudante
├── videos_validacao/                 # Amostras de 24, 60 e 120 FPS usadas no deploy
├── static/                           # Pasta usada pelos exports do Streamlit
├── docs/CONTRATOS_MODULOS.md        # Contratos entre módulos
├── DEPLOY_STREAMLIT.md              # Guia de publicação no Streamlit Community Cloud
├── requirements.txt                 # Dependências Python versionadas
├── packages.txt                     # Dependências Linux de vídeo/sistema
├── runtime.txt                      # Versão do Python usada no deploy
└── README.md
```

O contrato central do pipeline é a tabela de saída com `frame`, `tempo_s`, posições em pixels, posições em unidade real, velocidades e acelerações. Assim, rastreador, filtro, visualização e interface podem evoluir sem reescrever o método matemático.

---

## 🖥️ Como Executar Localmente

Para executar esta aplicação em sua máquina local, siga os passos abaixo.

### Pré-requisitos

- Git
- Python 3.11
- `pip` e `venv`

### Passos

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/isToim-dev/estroboscopia-digital.git
    cd estroboscopia-digital
    ```

2.  **Crie e ative um ambiente virtual:**
    ```bash
    # Para Windows
    python -m venv venv
    .\venv\Scripts\activate

    # Para macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Instale as dependências de sistema (apenas para Linux):**
    A aplicação depende de algumas bibliotecas que precisam ser instaladas. Em sistemas baseados em Debian/Ubuntu:
    ```bash
    sudo apt-get update
    sudo apt-get install -y ffmpeg libsm6 libxext6 libgl1
    ```

4.  **Instale as dependências Python:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Execute a aplicação Streamlit:**
    ```bash
    streamlit run stroboscopic_app.py
    ```
    A aplicação será aberta automaticamente no seu navegador.

## 📄 Licença

Este projeto está licenciado sob a **Licença MIT**. Veja o arquivo `LICENSE` no repositório para mais detalhes.

## 👨‍💻 Autor

- **[Rafael-UFU](https://github.com/Rafael-UFU)**
