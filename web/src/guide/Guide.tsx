import { type ReactNode, useEffect } from 'react';

import { ChainStrip } from '../app/components/ChainStrip';
import { ClipEditor } from '../app/components/ClipEditor';
import { DeviceDialog } from '../app/components/DeviceDialog';
import { FxRow } from '../app/components/FxRow';
import { KitEditor } from '../app/components/KitEditor';
import { Library } from '../app/components/Library';
import { MemoryDialog } from '../app/components/MemoryDialog';
import { FxPads, SequencePads, SongPads, SoundList } from '../app/components/MobileView';
import { PatternBar } from '../app/components/PatternBar';
import { TrackGrid } from '../app/components/TrackGrid';
import { type LibraryTarget, useAppFields } from '../app/store';
import { NarrowOverride } from '../app/useNarrow';

/** The clip editor's default targets, one object per sound so the memoized editor is not redrawn for a new but equal target. */
const defaultClipTargets: LibraryTarget[] = Array.from({ length: 8 }, (_, i) => ({ kind: 'melodic', slot: i + 1 }));

/**
 * The guide layout at /guide: the same app, with the same project and the same components,
 * laid out on one page instead of switched between. The desktop sequencer, the four phone
 * views, the library and every dialog are mounted once, in order, with the explanation of
 * each between them. Everything works as in the usual layout; what would open as a dialog
 * there is already on the page here, and the page scrolls to it.
 */
export function Guide() {
  const { project, pattern, copying, editors, library, device } = useAppFields('project', 'pattern', 'copying', 'editors', 'library', 'device');
  const top = editors[editors.length - 1];

  // What the usual layout would open over the page is scrolled to here.
  const focus = top?.kind === 'clip' ? 'guide-clip' : top?.kind === 'kit' ? 'guide-kit' : top?.kind === 'memory' ? 'guide-memory' : device ? `guide-${device}` : library.open ? 'guide-library' : null;
  useEffect(() => {
    if (focus) document.getElementById(focus)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [focus, top, library.target, library.editing]);

  if (!project) return null;
  // The clip and kit editors show what the app last opened, else the first sound that has one.
  const firstClip = project.melodic.findIndex((c) => c);
  const clipTarget: LibraryTarget | null = top?.kind === 'clip' ? top.target : firstClip >= 0 ? defaultClipTargets[firstClip] : null;
  const firstKit = project.drums.findIndex((d) => d);
  const kitSlot = top?.kind === 'kit' ? top.slot : firstKit >= 0 ? firstKit + 9 : 9;

  return (
    <div className="guide">
      <main className="guide-body">
        <h1>Guide</h1>
        <p className="lead">
          Welcome to SoSample! This view introduces the functionality of the app with instructions on how to use each feature. You can switch between this and the standard view by clicking the <b>?</b> button in the top bar.
        </p>
        <nav aria-label="Contents">
          <ol className="toc">
            {[
              ['start', 'Projects, playback and the bars'],
              ['desktop', 'The sequencer'],
              ['phone', 'The mobile views'],
              ['library', 'The library and samples'],
              ['editors', 'Clips and kits'],
              ['memory', 'Memory'],
              ['device', 'Sending to and importing from the PO-33'],
            ].map(([id, title]) => (
              <li key={id}>
                <a href={`#${id}`}>{title}</a>
              </li>
            ))}
          </ol>
        </nav>

        <Section id="start" title="Projects, playback and the bars">
          <p>
            SoSample builds samples, kits, patterns and songs for the Teenage Engineering PO-33 K.O!, plays them in the browser, and sends them to the device through its audio input. Everything is
            kept on this device; nothing is uploaded. Ten projects and seven drum kits come with the app and are added to your library when it loads; a deleted one comes back.
          </p>
          <h3>The top bar, at the top of this page</h3>
          <ol>
            <Step title="Projects">
              Open a project, start a <b>New project</b>, or <b>Import project…</b> from a file. Hover a project for export, duplicate and delete.
            </Step>
            <Step title="The name">Click it and type to rename. The mark beside it shows whether the last change is saved; saving is automatic.</Step>
            <Step title="Undo and redo">
              The arrows beside the name, or ⌘Z and ⇧⌘Z (Ctrl+Z and Ctrl+Y). Each click, drag or field edit is one step, and an undo shows the pattern it changed. Mute and solo are not
              undone. On a phone the arrows sit in the bottom bar. The history lasts until you switch project or reload.
            </Step>
            <Step title="Library and Device">Open the sample library, or send to or import from the PO-33. Both are further down this page, and the page scrolls to them.</Step>
            <Step title="Theme">System, Light or Dark.</Step>
            <Step title="?">Switches between this guide and the usual layout.</Step>
          </ol>
          <h3>The bottom bar, at the bottom of the screen</h3>
          <ol>
            <Step title="Play">
              Plays the preview; the space bar does too. <b>Song</b> plays the song from its first pattern, <b>Pattern</b> loops the pattern on screen, and <b>Follow</b> keeps the pattern on screen
              with the song. On a narrow screen these show as a triangle, <b>P</b>, <b>S</b> and <b>F</b>.
            </Step>
            <Step title="Tempo and swing">Swing delays every even step by up to 18 twenty-fourths of a step. On a phone they fold into one button that opens steppers.</Step>
            <Step title="Memory">The meter shows how much of the PO-33's 241 pages the project uses (on the narrowest phones, the bar alone); click it to jump to the breakdown below. Messages appear briefly above the bar.</Step>
          </ol>
        </Section>

        <Section id="desktop" title="The sequencer">
          <p>
            A project has sixteen sounds and sixteen patterns of sixteen steps, as the PO-33 does. Sounds 1 to 8 play one sample across sixteen keys; sounds 9 to 16 are drum kits, a sample per key.
            On a wide screen the app shows this sequencer; on a phone, the views in the next section.
          </p>
          <h3>Patterns and effects</h3>
          <ol>
            <Step title="Choose a pattern">Click a number. A dot marks a pattern with content, a bar under it the pattern playing, a triangle a pattern that asks for more than four voices.</Step>
            <Step title="Copy and clear">
              <b>Copy</b>, then a pattern number, copies the pattern there; <b>Clear</b> empties it; Escape cancels. Shift-click a number to add it to the song.
            </Step>
            <Step title="Effects">The FX row sets the PO-33's punch-in effect on each step; hover a cell for what it does. Its Copy and Clear act on the effects only.</Step>
          </ol>
          <Frame className="wide">
            <PatternBar />
            <FxRow />
          </Frame>
          <h3>Sounds and notes</h3>
          <ol>
            <Step title="A sound's editor">Click a sound's name: a melodic sound opens its clip editor, an empty one the library, a drum sound its kit editor (all below on this page).</Step>
            <Step title="Hear it">Hover the icon and click play: it plays the sound's current key.</Step>
            <Step title="Notes">
              Click an empty step; if the keys are rolled up the first click opens them, then a click adds a note on the current key. Click a note to remove it. Shift-click adds at once; arrows,
              Space and Delete work from the keyboard.
            </Step>
            <Step title="Keys">The chevron opens a sound's keys: click a step in a lane to put the note on that key, which becomes the current key.</Step>
            <Step title="Parameters">
              Under an open roll, choose Pitch, Vol, Filt or Res and drag a handle; dragging across steps paints them. Double-click removes a step's lock, so it keeps the value before it. A dot on a
              note means it changes a parameter.
            </Step>
            <Step title="Mute and solo">M and S silence or isolate a sound in the preview; double-click either to clear all.</Step>
            <Step title="Four voices">The PO-33 plays four notes at once. Notes a busy step drops carry a triangle; hover or click it for why.</Step>
          </ol>
          <Frame className="wide tall">
            <TrackGrid />
          </Frame>
          <h3>The song</h3>
          <ol>
            <Step title="Build it">
              <b>+</b> adds a pattern at the end. Click a chip to select it, then <b>Move left</b>, <b>Move right</b> or <b>Remove</b>; or drag chips. <b>Clear</b> resets the song to pattern 1.
            </Step>
          </ol>
          <Frame className="wide">
            <ChainStrip />
          </Frame>
        </Section>

        <Section id="mobile" title="The mobile views">
          <p>
            On a mobile device the app shows one of these views at a time, chosen by tabs, with the pattern strip under the tabs. Here all four are side by side and work on the same project: change a note in
            the Pattern view and it changes in the sequencer above.
          </p>
          <NarrowOverride.Provider value={true}>
            <div className="app narrow guide-phones">
              <div className="mobile guide-strip">
                <PatternBar compact />
              </div>
              <div className="guide-phone-row">
              <Phone title="Sound">
                <SoundList />
              </Phone>
              <Phone title="FX">
                <FxPads data={project.patterns[pattern - 1]} pattern={pattern} copying={copying} />
              </Phone>
              <Phone title="Pattern">
                <SequencePads />
              </Phone>
              <Phone title="Song">
                <SongPads />
              </Phone>
              </div>
            </div>
          </NarrowOverride.Provider>
          <ol>
            <Step title="The pattern strip">Selects the pattern every view works on, shows the one playing, and is where a copy lands.</Step>
            <Step title="Sound">
              Each sound as a row. Tap a name to open its editor and make it the sound the Pattern view shows. The play button plays the current key and lights with the key whenever the sound plays.
            </Step>
            <Step title="FX">The pattern's effects on the pads. The bar copies and clears the whole pattern (left) or its effects (right).</Step>
            <Step title="Pattern">
              One sound's steps on the pads, the sound chosen from the list. The key row sets the current key. Tap an empty pad to add a note, a note to select it, the selected note to remove it. With a
              step selected the parameter row edits it; <b>Clear</b> and <b>Clear all</b> remove its locks.
            </Step>
            <Step title="Song">Rows to drag by the handle or move with the arrows; the bin removes one; <b>+ Add pattern</b> appends.</Step>
            <Step title="Silent switch">On an iPhone or iPad the preview plays with the ring/silent switch in either position once anything on the page has been tapped.</Step>
          </ol>
        </Section>

        <Section id="library" title="The library and samples">
          <ol>
            <Step title="Samples">The library holds every sample on this device, shared by all projects. Click a sample's play button to hear it.</Step>
            <Step title="Add">
              <b>Add files…</b>, or drop audio files on the list: they are made mono and converted to the PO-33's rate.
            </Step>
            <Step title="Folders">
              Choose a folder to filter; <b>New folder</b> starts one; a selected folder can be renamed or deleted (its samples stay). Click a sample's folder to move it.
            </Step>
            <Step title="Select">Tick samples, shift-click for a range, or tick the heading for all; delete them together.</Step>
            <Step title="Edit a sample">
              Click its row. Trim on the waveform, set gain, normalize, fades and a compressor; <b>Reset</b> undoes, <b>Resample</b> bakes the edits in, <b>Resample as copy</b> keeps the original.
            </Step>
            <Step title="Choosing for a sound">Opened from an empty sound or a kit pad, the library shows <b>Use</b> on each sample.</Step>
            <Step title="Files">A project or kit file is a zip of a readable description and WAV samples. Export and import them from the Projects menu and the Kits menu.</Step>
          </ol>
          <Frame id="guide-library" className="dialog">
            <Library />
          </Frame>
        </Section>

        <Section id="editors" title="Clips and kits">
          <h3>A melodic sound's clip</h3>
          <ol>
            <Step title="The window">
              Drag on the waveform, or type Start and End, to choose the part that plays. <b>Preview</b> plays it; <b>Whole sample</b>, <b>Edit sample</b>, <b>Change sample…</b> and <b>Clear</b> do
              what they say. The sample is stored once however many sounds use it. The clip shown is the one last opened, else the first sound with a sample.
            </Step>
          </ol>
          <Frame id="guide-clip" className="dialog">
            {clipTarget ? <ClipEditor target={clipTarget} /> : <p className="muted guide-empty">No melodic sound has a sample yet; click a sound's name in the sequencer to choose one.</p>}
          </Frame>
          <h3>A drum kit</h3>
          <ol>
            <Step title="Pads">Each pad is a key. Click a filled pad to hear it and make it the current key, shown filled. A dot marks a key the current pattern plays.</Step>
            <Step title="Fill keys">Click an empty pad to choose its sample, or drop files on a pad to fill it and the keys after it. A pad's <b>…</b> edits its window.</Step>
            <Step title="Kits">
              Name the kit; <b>Kits ▾</b> saves it, imports a kit file, and loads, exports or deletes your kits. <b>Clear kit</b> empties the sound. The kit shown is the one last opened, else the first
              drum sound with a kit.
            </Step>
          </ol>
          <Frame id="guide-kit" className="dialog">
            <KitEditor slot={kitSlot} />
          </Frame>
        </Section>

        <Section id="memory" title="Memory">
          <p>
            Each sample the project stores on the device, where, what plays it and how many pages it takes. A sample used by several sounds is stored once, drum kits included. Sort by the headings.
          </p>
          <Frame id="guide-memory" className="dialog">
            <MemoryDialog />
          </Frame>
        </Section>

        <Section id="device" title="Sending to and importing from the PO-33">
          <p>The PO-33 has no USB data port: projects travel as sound through its 3.5 mm jacks. Use a cable, and one cable at a time.</p>
          <h3>Send</h3>
          <p>
            The steps are in the dialog. The transfer replaces everything on the device; <b>Device ▸ Download restore WAV</b> saves it to play later instead. Its play button really sends: mind the
            volume.
          </p>
          <Frame id="guide-send" className="dialog">
            <DeviceDialog mode="send" inPlace />
          </Frame>
          <h3>Import</h3>
          <p>A stereo line input is needed; a built-in microphone is mono. The backup becomes a new project, its samples in a library folder of their own.</p>
          <Frame id="guide-import" className="dialog">
            <DeviceDialog mode="import" inPlace />
          </Frame>
          <p className="muted">
            The PO-33 does not store its live knob settings, so after a send, auditioning a sound by hand may sound filtered until you turn knob B. The patterns play as written.
          </p>
        </Section>
        <footer className="guide-end muted">
          <p>
            SoSample is open source under the MIT licence. Its kits and projects are synthesized and free to use. It is an independent project, not affiliated with or endorsed by Teenage
            Engineering; PO-33 and K.O! are their trademarks.
          </p>
        </footer>
      </main>
    </div>
  );
}

function Section({ id, title, children }: { id: string; title: string; children: ReactNode }) {
  return (
    <section id={id}>
      <h2>{title}</h2>
      {children}
    </section>
  );
}

function Step({ title, children }: { title: string; children: ReactNode }) {
  return (
    <li>
      <strong>{title}.</strong> {children}
    </li>
  );
}

/** A frame around a part of the app shown in place. */
function Frame({ id, className = '', children }: { id?: string; className?: string; children: ReactNode }) {
  return (
    <div id={id} className={`guide-example ${className}`}>
      <div className="guide-frame">{children}</div>
    </div>
  );
}

/** One phone view in a phone-sized frame, captioned with its tab's name. */
function Phone({ title, children }: { title: string; children: ReactNode }) {
  return (
    <figure className="guide-example phone">
      <div className="guide-frame">
        <div className="mobile guide-phone">{children}</div>
      </div>
      <figcaption>{title}</figcaption>
    </figure>
  );
}
