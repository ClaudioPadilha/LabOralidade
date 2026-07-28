import { useEffect, useMemo, useRef, useState } from 'react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function App() {
  const [singleFile, setSingleFile] = useState(null);
  const [referenceFile, setReferenceFile] = useState(null);
  const [targetFile, setTargetFile] = useState(null);
  const [singleResult, setSingleResult] = useState(null);
  const [comparisonResult, setComparisonResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [recording, setRecording] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState(null);
  const [referenceRecordedBlob, setReferenceRecordedBlob] = useState(null);
  const [targetRecordedBlob, setTargetRecordedBlob] = useState(null);
  const [recordingTarget, setRecordingTarget] = useState(null); // 'reference' | 'target' | null
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  useEffect(() => {
    return () => {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  // Helpers: convert recorded Blob (webm/ogg) -> WAV File so backend can read
  async function blobToWavFile(blob, filename = 'recording.wav') {
    const arrayBuffer = await blob.arrayBuffer();
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);

    const numChannels = audioBuffer.numberOfChannels;
    const sampleRate = audioBuffer.sampleRate;
    const length = audioBuffer.length * numChannels * 2 + 44;
    const buffer = new ArrayBuffer(length);
    const view = new DataView(buffer);

    // write WAV header
    function writeString(view, offset, str) {
      for (let i = 0; i < str.length; i++) view.setUint8(offset + i, str.charCodeAt(i));
    }

    let offset = 0;
    writeString(view, offset, 'RIFF'); offset += 4;
    view.setUint32(offset, 36 + audioBuffer.length * numChannels * 2, true); offset += 4;
    writeString(view, offset, 'WAVE'); offset += 4;
    writeString(view, offset, 'fmt '); offset += 4;
    view.setUint32(offset, 16, true); offset += 4;
    view.setUint16(offset, 1, true); offset += 2; // PCM
    view.setUint16(offset, numChannels, true); offset += 2;
    view.setUint32(offset, sampleRate, true); offset += 4;
    view.setUint32(offset, sampleRate * numChannels * 2, true); offset += 4;
    view.setUint16(offset, numChannels * 2, true); offset += 2;
    view.setUint16(offset, 16, true); offset += 2;
    writeString(view, offset, 'data'); offset += 4;
    view.setUint32(offset, audioBuffer.length * numChannels * 2, true); offset += 4;

    // write PCM samples
    const channelData = [];
    for (let c = 0; c < numChannels; c++) channelData.push(audioBuffer.getChannelData(c));

    let pos = 44;
    for (let i = 0; i < audioBuffer.length; i++) {
      for (let c = 0; c < numChannels; c++) {
        let sample = Math.max(-1, Math.min(1, channelData[c][i]));
        view.setInt16(pos, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
        pos += 2;
      }
    }

    const wavBlob = new Blob([view], { type: 'audio/wav' });
    return new File([wavBlob], filename, { type: 'audio/wav' });
  }

  async function startRecording(target = null) {
    setError('');
    if (!navigator.mediaDevices || !window.MediaRecorder) {
      setError('Seu navegador não suporta gravação de áudio.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) chunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
        // convert to WAV file for backend compatibility
        if (target === 'reference') {
          setReferenceRecordedBlob(blob);
          try {
            const wavFile = await blobToWavFile(blob, 'reference_gravacao.wav');
            setReferenceFile(wavFile);
          } catch (e) {
            // fallback to raw blob if conversion fails
            const file = new File([blob], 'reference_gravacao.webm', { type: 'audio/webm' });
            setReferenceFile(file);
          }
        } else if (target === 'target') {
          setTargetRecordedBlob(blob);
          try {
            const wavFile = await blobToWavFile(blob, 'target_gravacao.wav');
            setTargetFile(wavFile);
          } catch (e) {
            const file = new File([blob], 'target_gravacao.webm', { type: 'audio/webm' });
            setTargetFile(file);
          }
        } else {
          setRecordedBlob(blob);
        }
        stream.getTracks().forEach((track) => track.stop());
        setRecordingTarget(null);
      };

      mediaRecorder.start();
      setRecording(true);
      setRecordedBlob(null);
      setRecordingTarget(target);
    } catch (err) {
      setError('Não foi possível acessar o microfone. Certifique-se de permitir a permissão.');
    }
  }

  function stopRecording() {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setRecording(false);
    }
  }

  async function handleAnalyze() {
    let fileToSend = null;
    if (singleFile) fileToSend = singleFile;
    else if (recordedBlob) {
      try {
        fileToSend = await blobToWavFile(recordedBlob, 'gravacao.wav');
      } catch (e) {
        fileToSend = new File([recordedBlob], 'gravacao.webm', { type: 'audio/webm' });
      }
    }
    if (!fileToSend) return;
    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', fileToSend);

    try {
      const response = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Erro ao analisar áudio');
      setSingleResult(data);
    } catch (err) {
      setError(err.message || 'Falha inesperada');
    } finally {
      setLoading(false);
    }
  }

  async function handleCompare() {
    if (!referenceFile || !targetFile) return;
    setLoading(true);
    setError('');

    const formData = new FormData();
    formData.append('reference', referenceFile);
    formData.append('target', targetFile);

    try {
      const response = await fetch(`${API_URL}/compare`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Erro ao comparar áudio');
      setComparisonResult(data);
    } catch (err) {
      setError(err.message || 'Falha inesperada');
    } finally {
      setLoading(false);
    }
  }

  const recordedPreviewUrl = useMemo(() => {
    if (!recordedBlob) return null;
    return URL.createObjectURL(recordedBlob);
  }, [recordedBlob]);

  const referencePreviewUrl = useMemo(() => {
    if (!referenceRecordedBlob) return null;
    return URL.createObjectURL(referenceRecordedBlob);
  }, [referenceRecordedBlob]);

  const targetPreviewUrl = useMemo(() => {
    if (!targetRecordedBlob) return null;
    return URL.createObjectURL(targetRecordedBlob);
  }, [targetRecordedBlob]);

  const [referenceFileUrl, setReferenceFileUrl] = useState(null);
  const [targetFileUrl, setTargetFileUrl] = useState(null);

  // create object URLs for uploaded files so they can be played
  useEffect(() => {
    if (referenceFile) {
      const url = URL.createObjectURL(referenceFile);
      setReferenceFileUrl(url);
      return () => URL.revokeObjectURL(url);
    }
    setReferenceFileUrl(null);
    return undefined;
  }, [referenceFile]);

  useEffect(() => {
    if (targetFile) {
      const url = URL.createObjectURL(targetFile);
      setTargetFileUrl(url);
      return () => URL.revokeObjectURL(url);
    }
    setTargetFileUrl(null);
    return undefined;
  }, [targetFile]);

  const [singleFileUrl, setSingleFileUrl] = useState(null);
  useEffect(() => {
    if (singleFile) {
      const url = URL.createObjectURL(singleFile);
      setSingleFileUrl(url);
      return () => URL.revokeObjectURL(url);
    }
    setSingleFileUrl(null);
    return undefined;
  }, [singleFile]);

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: 24, fontFamily: 'Arial, sans-serif' }}>
      <h1>LabOralidade</h1>
      <p>Grave áudio diretamente no navegador ou envie arquivos para gerar espectrograma, contorno de pitch e comparar dois áudios.</p>

      {error ? <p style={{ color: 'crimson' }}>{error}</p> : null}

      {/* standalone recording removed per request */}

      <section style={{ marginTop: 24 }}>
        <h2>Analisar um áudio</h2>
        <input type="file" accept="audio/*" onChange={(e) => setSingleFile(e.target.files?.[0] || null)} />
        <div style={{ marginTop: 8 }}>
          <button onClick={handleAnalyze} disabled={loading || (!singleFile && !recordedBlob)}>
            {loading ? 'Analisando...' : 'Analisar áudio'}
          </button>
        </div>
        {singleFileUrl ? (
          <div style={{ marginTop: 8 }}>
            <audio controls src={singleFileUrl} />
          </div>
        ) : null}
        {singleResult ? (
          <div style={{ marginTop: 16 }}>
            <p><strong>Arquivo:</strong> {singleResult.filename}</p>
            <p><strong>Duração:</strong> {singleResult.duration_seconds}s</p>
            <p><strong>Frequência dominante:</strong> {singleResult.dominant_frequency_hz} Hz</p>
            <p><strong>Pitch médio:</strong> {singleResult.pitch_mean_hz} Hz</p>
            <img src={singleResult.spectrum_image} alt="Espectrograma" style={{ width: '100%', maxWidth: 500, marginRight: 12 }} />
            <img src={singleResult.pitch_image} alt="Contorno de pitch" style={{ width: '100%', maxWidth: 500 }} />
          </div>
        ) : null}
      </section>

      <section style={{ marginTop: 40 }}>
        <h2>Comparar dois áudios</h2>
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
          <div style={{ minWidth: 240 }}>
            <label>
              Referência
              <br />
              <input type="file" accept="audio/*" onChange={(e) => setReferenceFile(e.target.files?.[0] || null)} />
            </label>
            <div style={{ marginTop: 8 }}>
              <button onClick={() => (recordingTarget === 'reference' ? stopRecording() : startRecording('reference'))} style={{ marginRight: 8 }}>
                {recordingTarget === 'reference' ? 'Parar gravação (Referência)' : 'Gravar Referência'}
              </button>
              {(referenceRecordedBlob || referenceFileUrl) ? (
                <div style={{ marginTop: 8 }}>
                  <audio controls src={referenceRecordedBlob ? referencePreviewUrl : referenceFileUrl} />
                </div>
              ) : null}
            </div>
          </div>

          <div style={{ minWidth: 240 }}>
            <label>
              Aluno
              <br />
              <input type="file" accept="audio/*" onChange={(e) => setTargetFile(e.target.files?.[0] || null)} />
            </label>
            <div style={{ marginTop: 8 }}>
              <button onClick={() => (recordingTarget === 'target' ? stopRecording() : startRecording('target'))} style={{ marginRight: 8 }}>
                {recordingTarget === 'target' ? 'Parar gravação (Aluno)' : 'Gravar Aluno'}
              </button>
              {(targetRecordedBlob || targetFileUrl) ? (
                <div style={{ marginTop: 8 }}>
                  <audio controls src={targetRecordedBlob ? targetPreviewUrl : targetFileUrl} />
                </div>
              ) : null}
            </div>
          </div>
        </div>
        <button onClick={handleCompare} disabled={!referenceFile || !targetFile || loading} style={{ marginTop: 12 }}>
          {loading ? 'Comparando...' : 'Comparar'}
        </button>
        {comparisonResult ? (
          <div style={{ marginTop: 16 }}>
            <p><strong>Similaridade:</strong> {comparisonResult.comparison.similarity_percent}%</p>
            <p><strong>Diferença de frequência dominante:</strong> {comparisonResult.comparison.dominant_freq_diff_hz} Hz</p>
            <p><strong>MAE de pitch:</strong> {comparisonResult.comparison.mae_semitones} semitons</p>
            <img src={comparisonResult.comparison_image} alt="Comparação" style={{ width: '100%', maxWidth: 700 }} />
            {comparisonResult.pitch_comparison_image ? (
              <div style={{ marginTop: 12 }}>
                <img src={comparisonResult.pitch_comparison_image} alt="Comparação de Pitch" style={{ width: '100%', maxWidth: 700 }} />
              </div>
            ) : null}
            <pre style={{ whiteSpace: 'pre-wrap', marginTop: 12 }}>{comparisonResult.feedback}</pre>
          </div>
        ) : null}
      </section>
    </div>
  );
}

export default App;
