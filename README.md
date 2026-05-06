# LabOralidade

Ferramenta de análise espectral de áudio para aulas de fonética. Lê arquivos de áudio e produz espectros de Fourier para que alunos possam comparar suas pronúncias com referências e aprimorar a fala.

## Instalação

```bash
pip install -e ".[dev]"
```

## Uso rápido

```python
from lab_oralidade import AudioSignal, SpectrumAnalyzer, plot_comparison

# Carregar áudios
referencia = AudioSignal.from_file("samples/referencia.wav")
aluno = AudioSignal.from_file("samples/aluno.wav")

# Calcular espectros
analyzer = SpectrumAnalyzer()
spec_ref = analyzer.compute(referencia)
spec_aluno = analyzer.compute(aluno)

# Visualizar comparação
plot_comparison(spec_ref, spec_aluno, labels=["Referência", "Aluno"])
```

## CLI

```bash
# Espectro de um único arquivo
lab-oralidade spectrum arquivo.wav --output espectro.png

# Comparar dois áudios
lab-oralidade compare referencia.wav aluno.wav --output comparacao.png
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
