import { memo, useEffect, useRef, useState } from 'react';

import { parseWav } from '../../core/wav';
import { type AudioInput, type InputProbe, MonoInputError, type Recording, type Transfer, describeRecording, listInputs, probeInput, recordBackup, recordingWavBytes, requireDistinctChannels, sendRestore } from '../device';
import { downloadBytes } from '../download';
import type { WavData } from '../../core/wav';
import { store, useAppFields } from '../store';

export type DeviceMode = 'send' | 'import';

/**
 * iPhone and iPad: their browsers give a page one microphone channel whatever is plugged in,
 * and a backup needs both, so importing works from a computer only. iPadOS reports itself as
 * a Mac, told apart by its touch screen.
 */
const MONO_ONLY_DEVICE =
  typeof navigator !== 'undefined' && (/iPhone|iPad|iPod/.test(navigator.userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1));

/** `inPlace`: shown in the guide's page rather than opened by the user, so it does nothing on its own (no input check). */
function DeviceDialogView({ mode, inPlace = false }: { mode: DeviceMode; inPlace?: boolean }) {
  return (
    <div className="modal-backdrop" onClick={() => store.closeDevice()}>
      <div className="modal editor" onClick={(e) => e.stopPropagation()}>
        <header>
          <strong>{mode === 'send' ? 'Send to PO-33' : 'Import from PO-33'}</strong>
          <div className="spacer" />
          <button onClick={() => store.closeDevice()}>Close</button>
        </header>
        <div className="editor-body">{mode === 'send' ? <Send /> : <Import inPlace={inPlace} />}</div>
      </div>
    </div>
  );
}

function Send() {
  const { project } = useAppFields('project');
  const [gain, setGain] = useState(0.6);
  const [transfer, setTransfer] = useState<Transfer | null>(null);
  const [position, setPosition] = useState(0);
  const [finished, setFinished] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    if (!transfer) return;
    const timer = setInterval(() => setPosition(transfer.position()), 200);
    return () => clearInterval(timer);
  }, [transfer]);
  const start = () => {
    try {
      const t = sendRestore(store.buildLabels(), gain);
      setTransfer(t);
      setFinished(false);
      setError(null);
      void t.done.then(() => {
        setFinished(true);
        setTransfer(null);
      });
    } catch (e) {
      setError((e as Error).message);
    }
  };
  // The whole restore is built to measure it: at once when the dialog opens, then half a second after
  // the edits stop, so editing with the dialog in view (the guide shows it in place) stays quick.
  const [seconds, setSeconds] = useState<number | null>(() => (project ? store.transferSeconds() : null));
  const measured = useRef(project);
  useEffect(() => {
    if (!project || project === measured.current) return;
    const timer = setTimeout(() => {
      measured.current = project;
      setSeconds(store.transferSeconds());
    }, 500);
    return () => clearTimeout(timer);
  }, [project]);
  return (
    <>
      <ol>
        <li>Connect the computer's headphone output to the PO-33's line input. Unplug any cable from the PO-33's output, otherwise the device hears its own echo.</li>
        <li>Set the output volume to a fixed, medium level and turn off any sound enhancements.</li>
        <li>On the PO-33, hold <b>write</b> and press <b>sound</b> + <b>record</b>. It waits for the transfer.</li>
        <li>Press Play below. The transfer takes about {seconds === null ? '–' : Math.round(seconds)} s; the PO-33 shows ERR if it loses the signal, in which case try another level.</li>
      </ol>
      {/* The level, its slider and the button on one line; while sending, the button cancels and the progress shows below. */}
      <div className="input-row">
        <label>
          <span className="level">Level {Math.round(gain * 100)}%</span>
          <input type="range" min={0.1} max={1} step={0.05} value={gain} disabled={!!transfer} onChange={(e) => setGain(Number(e.target.value))} aria-label="Level" />
        </label>
        {transfer ? (
          <button onClick={() => transfer.cancel()}>Cancel</button>
        ) : (
          <button className="on" disabled={!project} onClick={start}>
            Play restore
          </button>
        )}
      </div>
      {error && <p className="warn">{error}</p>}
      {transfer && (
        <p>
          Sending… {position.toFixed(0)} / {transfer.seconds.toFixed(0)} s
        </p>
      )}
      {!transfer && finished && <p className="muted">Finished. The PO-33 should have left transfer mode without ERR.</p>}
    </>
  );
}

function describeProbe(probe: InputProbe): string {
  const name = probe.label || 'This input';
  if (probe.channelCount === null) return `${name}: channel count unknown.`;
  if (probe.channelCount >= 2) return `${name}: stereo, ${probe.channelCount} channels.`;
  return `${name}: mono. A backup needs both channels; choose a stereo line input.`;
}

function Import({ inPlace }: { inPlace: boolean }) {
  const { inputDevice } = useAppFields('inputDevice');
  const [inputs, setInputs] = useState<AudioInput[]>([]);
  const [probe, setProbe] = useState<InputProbe | null>(null);
  const [probing, setProbing] = useState(false);
  const [recording, setRecording] = useState<Recording | null>(null);
  const [status, setStatus] = useState({ peak: 0, started: false, seconds: 0 });
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  /** The last recording that could not be imported, kept so it can be saved and analysed. */
  const [failed, setFailed] = useState<{ wav: WavData; name: string } | null>(null);
  const file = useRef<HTMLInputElement>(null);
  const labelled = inputs.some((i) => i.label);
  const refreshInputs = async () => {
    try {
      setInputs(await listInputs());
    } catch {
      setInputs([]);
    }
  };
  /** Open the input briefly to learn its channel count; also unlocks the device names. */
  const check = async (id: string) => {
    setProbing(true);
    setProbe(null);
    try {
      setProbe(await probeInput(id || undefined));
      await refreshInputs();
    } catch (e) {
      setMessage(`Could not open the audio input: ${(e as Error).message}`);
    } finally {
      setProbing(false);
    }
  };
  const remembered = useRef(inputDevice);
  useEffect(() => {
    let open = true;
    // Device names are only known once the page has used an input; then the remembered one can be checked quietly.
    listInputs().then(
      (found) => {
        if (!open) return;
        setInputs(found);
        // Not on the guide's page: there the dialog is only shown, and checking would open the microphone unasked.
        if (!inPlace && found.some((i) => i.label)) void check(remembered.current);
      },
      () => undefined,
    );
    const media = navigator.mediaDevices;
    media?.addEventListener?.('devicechange', refreshInputs);
    return () => {
      open = false;
      media?.removeEventListener?.('devicechange', refreshInputs);
    };
    // inPlace is fixed for a mounted dialog; listed so the effect stays honest.
  }, [inPlace]);

  useEffect(() => {
    if (!recording) return;
    const timer = setInterval(() => setStatus(recording.status()), 100);
    return () => clearInterval(timer);
  }, [recording]);
  const finish = async (wav: Awaited<Recording['result']>, name: string) => {
    setRecording(null);
    if (!wav) {
      setMessage('Cancelled.');
      return;
    }
    setBusy(true);
    setFailed(null);
    try {
      requireDistinctChannels(wav, name);
      const summary = await store.importBackup(wav, name);
      setMessage(summary);
    } catch (e) {
      setFailed({ wav, name });
      const reason = e instanceof MonoInputError ? e.message : `Could not decode the recording: ${(e as Error).message}`;
      setMessage(`${reason} (${describeRecording(wav)})`);
    } finally {
      setBusy(false);
    }
  };
  const start = async () => {
    setMessage(null);
    try {
      const r = await recordBackup(inputDevice || undefined);
      setRecording(r);
      r.result.then(
        (wav) => finish(wav, `PO-33 backup ${new Date().toLocaleString()}`),
        (e: Error) => {
          setRecording(null);
          setMessage(e.message);
        },
      );
    } catch (e) {
      setMessage(e instanceof MonoInputError ? e.message : `Could not open the audio input: ${(e as Error).message}`);
    }
  };
  const chooseInput = (id: string) => {
    void store.setInputDevice(id);
    setProbe(null);
    setMessage(null);
    void check(id);
  };
  const mono = probe?.channelCount === 1;
  return (
    <>
      {MONO_ONLY_DEVICE && (
        <p className="warn">
          On an iPhone or iPad the browser receives only one channel of audio, and a backup needs both. Import on a computer with a stereo line input, export the project there
          (Projects, the download icon), and open the file here with Projects, Import project. Sending to the PO-33 works from here.
        </p>
      )}
      <ol>
        <li>Connect the PO-33's output to a stereo line input on the computer. Unplug the cable from the PO-33's input.</li>
        <li>Choose that input below and allow the browser to use it. A built-in microphone is mono and cannot carry a backup.</li>
        <li>Press Record, then on the PO-33 hold <b>write</b> and press <b>sound</b> + <b>play</b>. The recording stops by itself 1.5 s after the transfer ends.</li>
      </ol>
      {/* The input, its list and the check button on one line; the list gives up width on a phone. */}
      <div className="input-row">
        <label>
          Input
          <select value={inputDevice} disabled={!!recording || probing} onChange={(e) => chooseInput(e.target.value)} aria-label="Audio input">
            <option value="">Browser default</option>
            {inputs.map((i, n) => (
              <option key={i.id} value={i.id}>
                {i.label || `Input ${n + 1}`}
              </option>
            ))}
          </select>
        </label>
        {!labelled && (
          <button disabled={probing || !!recording} onClick={() => void check(inputDevice)}>
            Allow input access
          </button>
        )}
        {labelled && (
          <button disabled={probing || !!recording} onClick={() => void check(inputDevice)}>
            Check input
          </button>
        )}
      </div>
      {probing && <p className="muted">Checking the input…</p>}
      {probe && <p className={mono ? 'warn' : 'muted'}>{describeProbe(probe)}</p>}
      {recording ? (
        <p>
          {status.started ? 'Recording the transfer…' : 'Waiting for signal…'} {status.seconds.toFixed(0)} s, level {(status.peak * 100).toFixed(1)}%{' '}
          <button onClick={() => recording.cancel()}>Cancel</button>
          {!status.started && status.seconds >= 10 && (
            <span className="muted"> Nothing heard yet: check that the PO-33's output is connected to this input and that it is sending.</span>
          )}
        </p>
      ) : (
        <p>
          <button className="on" disabled={busy || probing || mono} onClick={() => void start()}>
            Record
          </button>{' '}
          <button disabled={busy} onClick={() => file.current?.click()}>
            Import a recording file…
          </button>
          <input
            ref={file}
            type="file"
            accept=".wav,audio/wav"
            hidden
            onChange={async (e) => {
              const f = e.target.files?.[0];
              e.target.value = '';
              if (!f) return;
              setBusy(true);
              try {
                await finish(parseWav(new Uint8Array(await f.arrayBuffer())), f.name.replace(/\.[^.]+$/, ''));
              } catch (err) {
                setMessage((err as Error).message);
                setBusy(false);
              }
            }}
          />
        </p>
      )}
      {busy && <p className="muted">Decoding…</p>}
      {message && <p>{message}</p>}
      {failed && !busy && (
        <p>
          <button onClick={() => downloadBytes(`${failed.name}.wav`, recordingWavBytes(failed.wav))}>Save the recording</button>{' '}
          <span className="muted">Keep it: the research toolkit can analyse it.</span>
        </p>
      )}
    </>
  );
}

/** Memoized: it reads the store itself, so a parent's redraw (a bar change in the guide) need not redraw it. */
export const DeviceDialog = memo(DeviceDialogView);
