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

## Interface Web (Streamlit)

A forma mais simples de usar a ferramenta é pela interface web, que permite gravar pelo microfone, carregar arquivos, analisar espectro e pitch, e comparar pronúncias — tudo no navegador.

```bash
# Ativar o ambiente virtual (se ainda não estiver ativo)
source laborvenv/bin/activate

# Iniciar a interface web
streamlit run app.py
```

O Streamlit abre automaticamente o navegador em **http://localhost:8501**. Caso não abra, acesse esse endereço manualmente. Para usar outra porta:

```bash
streamlit run app.py --server.port 8080
```

Pressione `Ctrl+C` no terminal para encerrar o servidor.

## Uso rápido

### Comparação de pitch (caso principal)

```python
from lab_oralidade import extract_pitch_contour, compare_pitch_contours, generate_feedback
from lab_oralidade import plot_pitch_contour_comparison

# Extrair contornos de pitch
ref_contour = extract_pitch_contour("samples/referencia.wav")
aluno_contour = extract_pitch_contour("samples/aluno.wav")

# Comparar (normaliza tempo, converte para semitons, calcula métricas)
result = compare_pitch_contours(ref_contour, aluno_contour)

# Feedback textual
print(generate_feedback(result))

# Visualização (overlay + gráfico de diferença)
plot_pitch_contour_comparison(result, output_path="comparacao_pitch.png")
```

### Análise espectral

```python
from lab_oralidade import AudioSignal, SpectrumAnalyzer, plot_comparison

referencia = AudioSignal.from_file("samples/referencia.wav")
aluno = AudioSignal.from_file("samples/aluno.wav")

analyzer = SpectrumAnalyzer()
spec_ref = analyzer.compute(referencia)
spec_aluno = analyzer.compute(aluno)

plot_comparison(spec_ref, spec_aluno, labels=["Referência", "Aluno"])
```

## Fluxo completo via CLI

```bash
# 1. Gravar referência (3 segundos)
lab-oralidade record samples/referencia.wav -d 3

# 2. Gravar aluno
lab-oralidade record samples/aluno.wav -d 3

# 3. Ouvir para conferir
lab-oralidade play samples/referencia.wav
lab-oralidade play samples/aluno.wav

# 4. Comparar contornos de pitch
lab-oralidade pitch-compare samples/referencia.wav samples/aluno.wav -o resultado.png
```

## CLI

### `record` — Gravar áudio do microfone

```bash
# Gravar até pressionar Enter
lab-oralidade record gravacao.wav

# Gravar por duração fixa (5 segundos)
lab-oralidade record gravacao.wav --duration 5

# Especificar sample rate e dispositivo de entrada
lab-oralidade record gravacao.wav -d 3 -sr 44100 --device 2
```

| Argumento | Descrição |
|-----------|-----------|
| `output_file` | Caminho para salvar o arquivo WAV (obrigatório) |
| `--duration`, `-d` | Duração em segundos. Sem este argumento, grava até pressionar Enter |
| `--sample-rate`, `-sr` | Taxa de amostragem em Hz (padrão: 22050) |
| `--device` | Dispositivo de entrada (índice ou nome) |

### `play` — Reproduzir áudio

```bash
# Reproduzir um arquivo
lab-oralidade play gravacao.wav

# Usar dispositivo de saída específico
lab-oralidade play gravacao.wav --device 1
```

| Argumento | Descrição |
|-----------|-----------|
| `audio_file` | Arquivo de áudio para reproduzir (obrigatório) |
| `--device` | Dispositivo de saída (índice ou nome) |

### `spectrum` — Gerar espectro de frequência

```bash
# Exibir espectro na tela
lab-oralidade spectrum gravacao.wav

# Salvar espectro como imagem
lab-oralidade spectrum gravacao.wav --output espectro.png

# Ajustar parâmetros FFT
lab-oralidade spectrum gravacao.wav --n-fft 4096 --max-freq 8000
```

| Argumento | Descrição |
|-----------|-----------|
| `audio_file` | Arquivo de áudio para análise (obrigatório) |
| `--output`, `-o` | Caminho para salvar a imagem do espectro |
| `--n-fft` | Tamanho da FFT (padrão: 2048) |
| `--max-freq` | Frequência máxima exibida em Hz (padrão: 5000) |

### `compare` — Comparar espectros de dois áudios

```bash
# Comparar e exibir na tela
lab-oralidade compare referencia.wav aluno.wav

# Salvar comparação como imagem
lab-oralidade compare referencia.wav aluno.wav --output comparacao.png
```

| Argumento | Descrição |
|-----------|-----------|
| `reference` | Arquivo de áudio de referência (obrigatório) |
| `target` | Arquivo de áudio do aluno (obrigatório) |
| `--output`, `-o` | Caminho para salvar a imagem da comparação |
| `--n-fft` | Tamanho da FFT (padrão: 2048) |
| `--max-freq` | Frequência máxima exibida em Hz (padrão: 5000) |

### `pitch` — Extrair contorno de pitch (F0)

```bash
# Exibir gráfico de pitch na tela
lab-oralidade pitch gravacao.wav

# Salvar como imagem
lab-oralidade pitch gravacao.wav --output pitch.png

# Ajustar parâmetros de detecção
lab-oralidade pitch gravacao.wav --floor 50 --ceiling 400 --time-step 0.005
```

| Argumento | Descrição |
|-----------|-----------|
| `audio_file` | Arquivo de áudio para análise (obrigatório) |
| `--output`, `-o` | Caminho para salvar a imagem do contorno |
| `--time-step` | Passo temporal em segundos (padrão: 0.01) |
| `--floor` | F0 mínimo em Hz (padrão: 75) |
| `--ceiling` | F0 máximo em Hz (padrão: 600) |

### `pitch-compare` — Comparar contornos de pitch de dois áudios

```bash
# Comparar e exibir métricas + gráfico
lab-oralidade pitch-compare referencia.wav aluno.wav

# Salvar gráfico de comparação
lab-oralidade pitch-compare referencia.wav aluno.wav --output comparacao_pitch.png

# Ajustar limiar de desvio (semitons)
lab-oralidade pitch-compare referencia.wav aluno.wav --threshold 1.5
```

| Argumento | Descrição |
|-----------|-----------|
| `reference` | Arquivo de áudio de referência (obrigatório) |
| `target` | Arquivo de áudio do aluno (obrigatório) |
| `--output`, `-o` | Caminho para salvar a imagem da comparação |
| `--time-step` | Passo temporal em segundos (padrão: 0.01) |
| `--floor` | F0 mínimo em Hz (padrão: 75) |
| `--ceiling` | F0 máximo em Hz (padrão: 600) |
| `--threshold` | Limiar de desvio em semitons (padrão: 2.0) |

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
