"""Command-line interface for LabOralidade."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from lab_oralidade.audio import AudioSignal
from lab_oralidade.comparison import compare_spectra
from lab_oralidade.pitch import PitchContour, extract_pitch_contour
from lab_oralidade.pitch_comparison import compare_pitch_contours, generate_feedback
from lab_oralidade.recording import play_file, record, record_until_enter, save_recording
from lab_oralidade.spectrum import SpectrumAnalyzer
from lab_oralidade.visualization import (
    plot_comparison,
    plot_pitch,
    plot_pitch_comparison,
    plot_pitch_contour_comparison,
    plot_spectrum,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lab-oralidade",
        description="Análise espectral de áudio para fonética",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # record subcommand
    rp = subparsers.add_parser("record", help="Gravar áudio do microfone")
    rp.add_argument("output_file", type=Path, help="Caminho para salvar o arquivo WAV")
    rp.add_argument(
        "--duration", "-d", type=float, default=None,
        help="Duração em segundos (sem este argumento, grava até pressionar Enter)",
    )
    rp.add_argument("--sample-rate", "-sr", type=int, default=22050)
    rp.add_argument(
        "--device", type=str, default=None,
        help="Dispositivo de entrada (índice ou nome)",
    )

    # play subcommand
    pp = subparsers.add_parser("play", help="Reproduzir um arquivo de áudio")
    pp.add_argument("audio_file", type=Path, help="Arquivo de áudio para reproduzir")
    pp.add_argument(
        "--device", type=str, default=None,
        help="Dispositivo de saída (índice ou nome)",
    )

    # spectrum subcommand
    sp = subparsers.add_parser("spectrum", help="Gerar espectro de um arquivo de áudio")
    sp.add_argument("audio_file", type=Path)
    sp.add_argument("--output", "-o", type=Path, default=None)
    sp.add_argument("--n-fft", type=int, default=2048)
    sp.add_argument("--max-freq", type=float, default=5000.0)

    # compare subcommand
    cp = subparsers.add_parser("compare", help="Comparar espectros de dois arquivos")
    cp.add_argument("reference", type=Path)
    cp.add_argument("target", type=Path)
    cp.add_argument("--output", "-o", type=Path, default=None)
    cp.add_argument("--n-fft", type=int, default=2048)
    cp.add_argument("--max-freq", type=float, default=5000.0)

    # pitch subcommand
    pt = subparsers.add_parser("pitch", help="Extrair contorno de pitch (F0)")
    pt.add_argument("audio_file", type=Path)
    pt.add_argument("--output", "-o", type=Path, default=None)
    pt.add_argument(
        "--time-step", type=float, default=0.01,
        help="Passo temporal em segundos (padrão: 0.01)",
    )
    pt.add_argument("--floor", type=float, default=75.0, help="F0 mínimo em Hz (padrão: 75)")
    pt.add_argument("--ceiling", type=float, default=600.0, help="F0 máximo em Hz (padrão: 600)")

    # pitch-compare subcommand
    pc = subparsers.add_parser("pitch-compare", help="Comparar contornos de pitch de dois áudios")
    pc.add_argument("reference", type=Path, help="Arquivo de áudio de referência")
    pc.add_argument("target", type=Path, help="Arquivo de áudio do aluno")
    pc.add_argument("--output", "-o", type=Path, default=None)
    pc.add_argument(
        "--time-step", type=float, default=0.01,
        help="Passo temporal em segundos (padrão: 0.01)",
    )
    pc.add_argument("--floor", type=float, default=75.0, help="F0 mínimo em Hz (padrão: 75)")
    pc.add_argument("--ceiling", type=float, default=600.0, help="F0 máximo em Hz (padrão: 600)")
    pc.add_argument(
        "--threshold", type=float, default=2.0,
        help="Limiar de desvio em semitons (padrão: 2.0)",
    )

    args = parser.parse_args(argv)

    if args.command == "record":
        device = int(args.device) if args.device and args.device.isdigit() else args.device
        if args.duration:
            signal = record(args.duration, sample_rate=args.sample_rate, device=device)
        else:
            signal = record_until_enter(sample_rate=args.sample_rate, device=device)

        path = save_recording(signal, args.output_file)
        print(f"Salvo em: {path} ({signal.duration:.1f}s)")
        return 0

    if args.command == "play":
        device = int(args.device) if args.device and args.device.isdigit() else args.device
        play_file(args.audio_file, device=device)
        return 0

    if args.command == "pitch":
        contour = extract_pitch_contour(
            args.audio_file,
            time_step=args.time_step,
            pitch_floor=args.floor,
            pitch_ceiling=args.ceiling,
        )
        f0_min, f0_max = contour.f0_range
        print(f"F0 médio: {contour.mean_f0:.1f} Hz")
        print(f"F0 mín: {f0_min:.1f} Hz | F0 máx: {f0_max:.1f} Hz")
        plot_pitch(contour, output_path=args.output)
        if args.output:
            print(f"Salvo em: {args.output}")
        else:
            import matplotlib.pyplot as plt

            plt.show()
        return 0

    if args.command == "pitch-compare":
        ref_contour = extract_pitch_contour(
            args.reference,
            time_step=args.time_step,
            pitch_floor=args.floor,
            pitch_ceiling=args.ceiling,
        )
        tgt_contour = extract_pitch_contour(
            args.target,
            time_step=args.time_step,
            pitch_floor=args.floor,
            pitch_ceiling=args.ceiling,
        )
        result = compare_pitch_contours(
            ref_contour, tgt_contour, deviation_threshold=args.threshold
        )
        feedback = generate_feedback(result)
        print(feedback)
        plot_pitch_contour_comparison(result, output_path=args.output)
        if args.output:
            print(f"\nSalvo em: {args.output}")
        else:
            import matplotlib.pyplot as plt

            plt.show()
        return 0

    analyzer = SpectrumAnalyzer(n_fft=args.n_fft)

    if args.command == "spectrum":
        signal = AudioSignal.from_file(args.audio_file)
        result = analyzer.compute(signal.trim_silence().normalize())
        plot_spectrum(result, max_freq=args.max_freq, output_path=args.output)
        print(f"Frequência dominante: {result.dominant_frequency:.1f} Hz")
        if args.output:
            print(f"Salvo em: {args.output}")
        else:
            import matplotlib.pyplot as plt

            plt.show()

    elif args.command == "compare":
        ref_signal = AudioSignal.from_file(args.reference).trim_silence().normalize()
        tgt_signal = AudioSignal.from_file(args.target).trim_silence().normalize()

        ref_spec = analyzer.compute(ref_signal)
        tgt_spec = analyzer.compute(tgt_signal)

        comparison = compare_spectra(ref_spec, tgt_spec)
        print(f"Similaridade: {comparison.similarity_percent:.1f}%")
        print(f"Diferença freq. dominante: {comparison.dominant_freq_diff_hz:.1f} Hz")
        print(f"Diferença centróide espectral: {comparison.spectral_centroid_diff_hz:.1f} Hz")

        plot_comparison(
            ref_spec,
            tgt_spec,
            labels=["Referência", "Aluno"],
            max_freq=args.max_freq,
            output_path=args.output,
        )
        if not args.output:
            import matplotlib.pyplot as plt

            plt.show()

    return 0


if __name__ == "__main__":
    sys.exit(main())
