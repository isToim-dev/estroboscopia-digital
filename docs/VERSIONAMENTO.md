# Versionamento e reprodutibilidade

Este documento registra as versões dos componentes necessários para executar o aplicativo **ESTROBOSCOPIA DIGITAL** sem depender de atualizações futuras de bibliotecas.

## Ambiente de execução

| Componente | Versão / arquivo | Função no aplicativo |
| --- | --- | --- |
| Python | 3.11 (`runtime.txt`) | Interpretador usado no Streamlit Community Cloud. |
| Streamlit Community Cloud | Selecionar Python 3.11 nas configurações do app | Hospedagem e execução web. |
| Dependências Python | `requirements.txt` | Bibliotecas diretas versionadas com `==`. |
| Dependências Linux | `packages.txt` | Pacotes de sistema exigidos por OpenCV/vídeo. |

Observação: o Streamlit Community Cloud pode ignorar `runtime.txt` em alguns fluxos recentes de deploy. Por isso, a versão Python 3.11 também deve ser confirmada pela interface do Streamlit.

## Dependências Python diretas

| Pacote | Versão fixada | Motivo |
| --- | --- | --- |
| `opencv-contrib-python-headless` | 4.12.0.88 | Rastreio CSRT via `cv2.TrackerCSRT_create()` em ambiente sem interface gráfica. |
| `numpy` | 2.2.5 | Cálculo numérico, homografia, vetores e séries. |
| `pandas` | 2.2.3 | Tabelas cinemáticas e exportação CSV. |
| `scipy` | 1.17.1 | Filtro Savitzky-Golay. |
| `streamlit` | 1.44.1 | Interface web. |
| `streamlit-image-coordinates` | 0.4.0 | Captura de cliques sobre a imagem do frame. |
| `matplotlib` | 3.10.9 | Gráficos cinemáticos, modelos e figuras do relatório. |
| `Pillow` | 11.1.0 | Manipulação de imagens e miniaturas. |
| `reportlab` | 4.4.10 | Geração do relatório PDF. |

## Dependências Linux de sistema

| Pacote | Arquivo | Finalidade |
| --- | --- | --- |
| `ffmpeg` | `packages.txt` | Leitura/escrita de vídeo. |
| `libsm6` | `packages.txt` | Dependência compartilhada usada por OpenCV. |
| `libxext6` | `packages.txt` | Dependência compartilhada usada por OpenCV. |
| `libgl1` | `packages.txt` | Suporte gráfico mínimo exigido por bibliotecas de imagem/vídeo. |

Esses pacotes são instalados pelo gerenciador Linux da plataforma. O Streamlit Community Cloud não fixa versões exatas de pacotes apt pelo `packages.txt`; a reprodutibilidade principal fica garantida pelas versões Python fixadas e pela escolha de Python 3.11.

## Componentes internos versionados pelo Git

| Módulo | Responsabilidade | Contrato principal |
| --- | --- | --- |
| `stroboscopic_app.py` | Orquestra telas, upload, calibração, análise e exportações. | Entrada Streamlit. |
| `app_config.py` | Constantes, CSS e presets visuais. | `STAMP_DENSITY_PRESETS`, `DEFAULT_APP_CSS`. |
| `app_state.py` | Estado do vídeo e limpeza de sessão. | `reset_video_state()`, `load_selected_video(...)`. |
| `sample_videos.py` | Galeria de vídeos de validação. | `list_validation_videos()`, `make_video_thumbnail(...)`. |
| `video_processing.py` | Rastreio, imagem estroboscópica, tabela e vídeo rastreado. | `processar_video(...)`. |
| `perspective_calibration.py` | Homografia métrica e resolução automática do plano. | `build_metric_homography(...)`, `aplicar_homografia(...)`. |
| `savgol_reverse.py` | Otimização reversa do Savitzky-Golay. | `optimize_savgol_parameters(...)`, `apply_savgol_kinematics(...)`. |
| `visualization.py` | Gráficos, grade cartesiana e vetores. | `plotar_graficos(...)`, `desenhar_grade_cartesiana(...)`. |
| `ui_controls.py` | Controles reutilizáveis. | `render_stamp_density_selector()`. |
| `report_generation.py` | Relatório PDF didático e personalizado. | `generate_student_report_pdf(...)`. |

Para reproduzir exatamente uma versão do aplicativo, use o commit do GitHub correspondente ao deploy.

## Comandos recomendados

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run stroboscopic_app.py
```

No Linux/macOS:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run stroboscopic_app.py
```
