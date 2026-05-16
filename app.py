"""Streamlit web app for LabOralidade — análise fonética de áudio."""

from __future__ import annotations

import matplotlib
import matplotlib.pyplot as plt
import streamlit as st

from lab_oralidade.audio import AudioSignal, save_temp_wav
from lab_oralidade.comparison import compare_spectra
from lab_oralidade.pitch import extract_pitch_contour
from lab_oralidade.pitch_comparison import compare_pitch_contours, generate_feedback
from lab_oralidade.spectrum import SpectrumAnalyzer
from lab_oralidade.visualization import (
    plot_comparison,
    plot_pitch,
    plot_pitch_contour_comparison,
    plot_spectrum,
)

matplotlib.use("Agg")

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="LabOralidade",
    page_icon="🎙️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar — navigation + global parameters
# ---------------------------------------------------------------------------
st.sidebar.title("🎙️ LabOralidade")
st.sidebar.markdown("Análise fonética de áudio")

section = st.sidebar.radio(
    "Navegação",
    ["Gravar e Ouvir", "Análise Individual", "Comparar Pronúncia"],
    index=2,
)

st.sidebar.markdown("---")
st.sidebar.subheader("Parâmetros")
time_step = st.sidebar.slider("Passo temporal (ms)", 5, 50, 10) / 1000.0
pitch_floor = st.sidebar.number_input("F0 mínimo (Hz)", 50, 200, 75)
pitch_ceiling = st.sidebar.number_input("F0 máximo (Hz)", 300, 800, 600)
n_fft = st.sidebar.select_slider("Tamanho FFT", [512, 1024, 2048, 4096], value=2048)
deviation_threshold = st.sidebar.slider("Limiar de desvio (semitons)", 0.5, 5.0, 2.0, 0.5)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_audio_input(label: str, key_prefix: str) -> bytes | None:
    """Provide mic recording and file upload, return WAV bytes or None."""
    tab_mic, tab_upload = st.tabs(["🎤 Microfone", "📁 Upload"])

    with tab_mic:
        audio = st.audio_input(f"Gravar {label}", key=f"{key_prefix}_mic")
        if audio is not None:
            return audio.getvalue()

    with tab_upload:
        uploaded = st.file_uploader(
            f"Upload {label} (WAV)",
            type=["wav"],
            key=f"{key_prefix}_upload",
        )
        if uploaded is not None:
            return uploaded.getvalue()

    return None


# ---------------------------------------------------------------------------
# Section 1: Gravar e Ouvir
# ---------------------------------------------------------------------------
if section == "Gravar e Ouvir":
    st.header("🎤 Gravar e Ouvir")
    st.markdown("Grave ou carregue um áudio para ouvir e salvar na sessão.")

    audio_bytes = _get_audio_input("áudio", "rec")

    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")
        signal = AudioSignal.from_buffer(audio_bytes)
        st.success(f"Áudio carregado: {signal.duration:.1f}s | {signal.sample_rate} Hz")


# ---------------------------------------------------------------------------
# Section 2: Análise Individual
# ---------------------------------------------------------------------------
elif section == "Análise Individual":
    st.header("📊 Análise Individual")
    st.markdown("Analise o espectro de frequência e o contorno de pitch de um áudio.")

    audio_bytes = _get_audio_input("áudio", "analysis")

    if audio_bytes:
        st.audio(audio_bytes, format="audio/wav")

        signal = AudioSignal.from_buffer(audio_bytes)
        tmp_path = save_temp_wav(audio_bytes)

        tab_spectrum, tab_pitch = st.tabs(["Espectro", "Pitch (F0)"])

        with tab_spectrum:
            analyzer = SpectrumAnalyzer(n_fft=n_fft)
            result = analyzer.compute(signal.trim_silence().normalize())
            fig = plot_spectrum(result, max_freq=5000.0)
            st.pyplot(fig)
            plt.close(fig)

            col1, col2 = st.columns(2)
            col1.metric("Frequência dominante", f"{result.dominant_frequency:.1f} Hz")

        with tab_pitch:
            contour = extract_pitch_contour(
                tmp_path, time_step=time_step,
                pitch_floor=pitch_floor, pitch_ceiling=pitch_ceiling,
            )
            fig = plot_pitch(contour)
            st.pyplot(fig)
            plt.close(fig)

            f0_min, f0_max = contour.f0_range
            col1, col2, col3 = st.columns(3)
            col1.metric("F0 médio", f"{contour.mean_f0:.1f} Hz")
            col2.metric("F0 mín", f"{f0_min:.1f} Hz")
            col3.metric("F0 máx", f"{f0_max:.1f} Hz")


# ---------------------------------------------------------------------------
# Section 3: Comparar Pronúncia
# ---------------------------------------------------------------------------
elif section == "Comparar Pronúncia":
    st.header("🔄 Comparar Pronúncia")
    st.markdown("Compare o contorno de pitch e o espectro entre uma referência e a gravação do aluno.")

    col_ref, col_tgt = st.columns(2)

    with col_ref:
        st.subheader("Referência")
        ref_bytes = _get_audio_input("referência", "ref")
        if ref_bytes:
            st.audio(ref_bytes, format="audio/wav")

    with col_tgt:
        st.subheader("Aluno")
        tgt_bytes = _get_audio_input("aluno", "tgt")
        if tgt_bytes:
            st.audio(tgt_bytes, format="audio/wav")

    if ref_bytes and tgt_bytes:
        if st.button("🔍 Comparar", type="primary", use_container_width=True):
            with st.spinner("Analisando..."):
                ref_path = save_temp_wav(ref_bytes)
                tgt_path = save_temp_wav(tgt_bytes)

                # --- Pitch comparison ---
                st.subheader("Contorno de Pitch (F0)")

                ref_contour = extract_pitch_contour(
                    ref_path, time_step=time_step,
                    pitch_floor=pitch_floor, pitch_ceiling=pitch_ceiling,
                )
                tgt_contour = extract_pitch_contour(
                    tgt_path, time_step=time_step,
                    pitch_floor=pitch_floor, pitch_ceiling=pitch_ceiling,
                )

                pitch_result = compare_pitch_contours(
                    ref_contour, tgt_contour,
                    deviation_threshold=deviation_threshold,
                )

                fig = plot_pitch_contour_comparison(pitch_result)
                st.pyplot(fig)
                plt.close(fig)

                # Metrics
                col1, col2, col3 = st.columns(3)
                col1.metric("MAE", f"{pitch_result.mae_semitones:.2f} st")
                col2.metric("RMSE", f"{pitch_result.rmse_semitones:.2f} st")
                col3.metric("Correlação", f"{pitch_result.correlation:.3f}")

                # Feedback
                feedback = generate_feedback(pitch_result)
                st.markdown(feedback)

                # --- Spectral comparison ---
                st.subheader("Espectro de Frequência")

                ref_signal = AudioSignal.from_buffer(ref_bytes).trim_silence().normalize()
                tgt_signal = AudioSignal.from_buffer(tgt_bytes).trim_silence().normalize()
                analyzer = SpectrumAnalyzer(n_fft=n_fft)

                ref_spec = analyzer.compute(ref_signal)
                tgt_spec = analyzer.compute(tgt_signal)

                fig = plot_comparison(
                    ref_spec, tgt_spec,
                    labels=["Referência", "Aluno"],
                )
                st.pyplot(fig)
                plt.close(fig)

                spec_result = compare_spectra(ref_spec, tgt_spec)
                col1, col2 = st.columns(2)
                col1.metric("Similaridade espectral", f"{spec_result.similarity_percent:.1f}%")
                col2.metric("Diferença freq. dominante", f"{spec_result.dominant_freq_diff_hz:.1f} Hz")
    else:
        st.info("Grave ou carregue áudio em ambos os slots para comparar.")
