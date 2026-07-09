# Deploy no Streamlit Community Cloud

## Arquivos necessários no repositório

- `stroboscopic_app.py`
- `requirements.txt`
- `packages.txt`
- `runtime.txt` como registro documental da versão do Python
- módulos Python (`app_config.py`, `app_state.py`, `sample_videos.py`, `visualization.py`, `video_processing.py`, `perspective_calibration.py`, `savgol_reverse.py`, `ui_controls.py`)
- `videos_validacao/` se as amostras de 24, 60 e 120 FPS devem aparecer no deploy
- `docs/` com a documentação técnica, contratos e figuras dos fluxos
- `scripts/generate_documentation_diagrams.py` para regenerar os mapas visuais da documentação

## Configuração do deploy

- Main file path: `stroboscopic_app.py`
- Python: selecione `3.11` nas configurações avançadas do Streamlit Community Cloud
- Dependências Python: `requirements.txt`
- Dependências de sistema Linux: `packages.txt`
- Versões documentadas: `docs/VERSIONAMENTO.md`

Observação: o Community Cloud pode ignorar `runtime.txt` em fluxos recentes de deploy.
Por isso, confirme a versão do Python pela interface do Streamlit antes de publicar
ou reiniciar o aplicativo.

## Antes de publicar

Execute localmente:

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
streamlit run stroboscopic_app.py
```

Se alterar a arquitetura dos módulos, regenere os diagramas antes do commit:

```bash
python scripts/generate_documentation_diagrams.py
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
