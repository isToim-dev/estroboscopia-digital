# Deploy no Streamlit Community Cloud

## Arquivos necessários no repositório

- `stroboscopic_app.py`
- `requirements.txt`
- `packages.txt`
- `runtime.txt`
- módulos Python (`app_config.py`, `app_state.py`, `sample_videos.py`, `visualization.py`, `video_processing.py`, `perspective_calibration.py`, `savgol_reverse.py`, `ui_controls.py`)
- `videos_validacao/` se as amostras de 24, 60 e 120 FPS devem aparecer no deploy

## Configuração do deploy

- Main file path: `stroboscopic_app.py`
- Python: definido em `runtime.txt` como `python-3.11`
- Dependências Python: `requirements.txt`
- Dependências de sistema Linux: `packages.txt`

## Antes de publicar

Execute localmente:

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

## Vídeos de validação

Para incluir amostras no deploy, mantenha os vídeos em uma pasta chamada:

```text
videos_validacao/
```

O app também reconhece uma pasta local próxima chamada `Video - Validação`, usada durante o desenvolvimento.
