# LabOralidade

Ferramenta de análise de áudio para aulas de fonética. Grava, reproduz e analisa arquivos de áudio produzindo espectros de Fourier e contornos de pitch (F0) para que alunos possam comparar suas pronúncias com referências e aprimorar a fala.

## Funcionalidades

- **Gravação e reprodução** — Captura áudio do microfone (duração fixa ou livre) e reproduz gravações
- **Espectro de frequência** — Análise FFT com visualização do espectro de magnitudes
- **Contorno de Pitch (F0)** — Extração da frequência fundamental via Praat/parselmouth
- **Comparação de pitch** — Alinha contornos por tempo normalizado, calcula similaridade (MAE, RMSE, correlação em semitons) e gera feedback textual com regiões que precisam de atenção
- **Interface web (Streamlit)** — Aplicação no navegador para gravar, analisar e comparar áudios sem usar a linha de comando

## Instalação

```bash
python -m venv laborvenv
source laborvenv/bin/activate
pip install -e ".[dev]"
```

## Interface web

A interface web foi reorganizada para usar um backend FastAPI e um frontend React/Vite, que permitem upload de áudio e análise em tempo real sem depender da gravação local do navegador.

### Backend

```bash
# LabOralidade

Ferramenta de análise de áudio para aulas de fonética. Este repositório mantém apenas a interface web atual baseada em:

- Backend: `FastAPI` (`backend.py`) — endpoints `/analyze` e `/compare` que retornam imagens (base64) e métricas
- Frontend: `React` + `Vite` (`frontend/`) — gravação no navegador, upload, análise e visualização (espectro + contorno de pitch)

## Instalação

Requisitos principais: Python (3.11+ recomendado), virtualenv, Node.js (LTS) e npm.

```bash
python -m venv laborvenv
source laborvenv/bin/activate
pip install -e ".[dev]"
```

## Executando localmente

Backend:

```bash
source laborvenv/bin/activate
pip install -r requirements.txt
python backend.py
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Abra http://localhost:5173 para a interface que permite gravação no navegador, upload, análise e comparação de áudios (espectro + contorno de pitch).

## Funcionalidades mantidas

- Gravação no navegador via MediaRecorder
- Upload de arquivos de áudio
- Análise individual (`/analyze`): espectro e contorno de pitch (F0)
- Comparação (`/compare`): espectro sobreposto e comparação de contornos de pitch (imagem + métricas + feedback)

## Testes

```bash
pytest
```
## Testes

```bash
pytest                      # toda a suíte
pytest tests/test_spectrum.py::test_sine_wave_peak  # um teste específico
```

## Lint

```bash
ruff check src/ tests/
ruff format src/ tests/
```
