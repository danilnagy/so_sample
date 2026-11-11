import { useEffect, useRef, useState } from 'react';

import { downloadBytes } from '../download';
import { CheckIcon, CopyIcon, DownloadIcon, PendingIcon, ThemeIcon, TrashIcon } from './Icons';
import { type Theme, store, useAppFields } from '../store';
import { useNarrow } from '../useNarrow';
import { UndoButtons } from './UndoButtons';

const THEME_NAMES: Record<Theme, string> = { system: 'System', light: 'Light', dark: 'Dark' };
const NEXT_THEME: Record<Theme, Theme> = { system: 'light', light: 'dark', dark: 'system' };

export function TopBar() {
  const { project, projects, theme, saving, guide } = useAppFields('project', 'projects', 'theme', 'saving', 'guide');
  const [menu, setMenu] = useState<'projects' | 'device' | null>(null);
  const narrow = useNarrow();
  const archiveInput = useRef<HTMLInputElement>(null);
  // An open menu closes on a click anywhere outside the bar's menus, or on Escape.
  useEffect(() => {
    if (!menu) return;
    const away = (e: MouseEvent) => {
      if (!(e.target as Element).closest('.menu')) setMenu(null);
    };
    const key = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMenu(null);
    };
    document.addEventListener('mousedown', away);
    document.addEventListener('keydown', key);
    return () => {
      document.removeEventListener('mousedown', away);
      document.removeEventListener('keydown', key);
    };
  }, [menu]);
  if (!project) return null;
  const exportProject = (id: string) => {
    store
      .projectArchive(id)
      .then(({ name, bytes }) => downloadBytes(name, bytes, 'application/zip'))
      .catch((error) => store.notify((error as Error).message));
    setMenu(null);
  };
  const toggle = (name: 'projects' | 'device') => setMenu(menu === name ? null : name);
  const exportWav = () => {
    try {
      downloadBytes(`${project.name || 'sosample'}.wav`, store.buildRestore());
    } catch (error) {
      store.notify((error as Error).message);
    }
    setMenu(null);
  };
  return (
    <div className="topbar">
      <span className="brand" aria-label="SoSample">
        <strong>SoS</strong>ample
      </span>
      <div className="menu">
        <button className={menu === 'projects' ? 'on' : ''} onClick={() => toggle('projects')}>
          Projects
        </button>
        {menu === 'projects' && (
          <div className="items">
            <button
              onClick={() => {
                void store.newProject();
                setMenu(null);
              }}
            >
              New project
            </button>
            <button
              onClick={() => {
                archiveInput.current?.click();
                setMenu(null);
              }}
            >
              Import project…
            </button>
            {projects.map((p) => (
              // A project row: the name opens it; on hover, duplicate and delete appear at its right.
              <div className="project-row" key={p.id}>
                <button
                  className={p.id === project.id ? 'on' : ''}
                  title={p.name}
                  onClick={() => {
                    void store.openProject(p.id);
                    setMenu(null);
                  }}
                >
                  {p.name}
                </button>
                <span className="row-actions">
                  <button className="icon-button" title="Export the project as a zip of JSON and WAV files" aria-label={`Export ${p.name}`} onClick={() => exportProject(p.id)}>
                    <DownloadIcon />
                  </button>
                  <button
                    className="icon-button"
                    title="Duplicate the project"
                    aria-label={`Duplicate ${p.name}`}
                    onClick={() => {
                      void store.duplicateProject(p.id);
                      setMenu(null);
                    }}
                  >
                    <CopyIcon />
                  </button>
                  <button
                    className="icon-button"
                    title="Delete the project; samples stay in the library"
                    aria-label={`Delete ${p.name}`}
                    onClick={() => {
                      if (confirm(`Delete "${p.name}"? Samples stay in the library.`)) void store.deleteProject(p.id);
                      setMenu(null);
                    }}
                  >
                    <TrashIcon />
                  </button>
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
      <input
        ref={archiveInput}
        type="file"
        accept=".zip,application/zip"
        hidden
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) {
            store
              .importProjectArchive(file)
              .then((message) => store.notify(message))
              .catch((error) => store.notify(`Could not import ${file.name}: ${(error as Error).message}`));
          }
          e.target.value = '';
        }}
      />
      <span className={`save-state ${saving ? 'saving' : ''}`} title={saving ? 'Saving…' : 'Saved'} role="img" aria-label={saving ? 'Saving' : 'Saved'}>
        {saving ? <PendingIcon /> : <CheckIcon />}
      </span>
      <input className="name" value={project.name} onChange={(e) => store.renameProject(e.target.value)} aria-label="Project name" />
      {/* On a phone the bar has no room; the bottom bar holds them there. */}
      {!narrow && <UndoButtons />}
      <button onClick={() => store.openLibrary(null)}>Library</button>
      <div className="menu right">
        <button className={menu === 'device' ? 'on' : ''} onClick={() => toggle('device')}>
          Device
        </button>
        {menu === 'device' && (
          <div className="items">
            <button onClick={exportWav}>Download restore WAV</button>
            <button
              onClick={() => {
                store.openDevice('send');
                setMenu(null);
              }}
            >
              Send to PO-33…
            </button>
            <button
              onClick={() => {
                store.openDevice('import');
                setMenu(null);
              }}
            >
              Import from PO-33…
            </button>
          </div>
        )}
      </div>
      <select value={theme} onChange={(e) => void store.setTheme(e.target.value as Theme)} aria-label="Theme">
        <option value="system">System</option>
        <option value="light">Light</option>
        <option value="dark">Dark</option>
      </select>
      {/* On a phone the list has no room: one button cycles System, Light, Dark. */}
      <button className="theme-button" title={`Theme: ${THEME_NAMES[theme]}. Tap for ${THEME_NAMES[NEXT_THEME[theme]]}.`} aria-label={`Theme: ${THEME_NAMES[theme]}. Tap for ${THEME_NAMES[NEXT_THEME[theme]]}`} onClick={() => void store.setTheme(NEXT_THEME[theme])}>
        <ThemeIcon theme={theme} />
      </button>
      {/* The guide, at the very right: it switches the app to its guide layout and back. */}
      <button className={`help-button ${guide ? 'on' : ''}`} aria-pressed={guide} title={guide ? 'Back to the app layout' : 'Guide: every view at once, explained'} aria-label={guide ? 'Close the guide' : 'Guide'} onClick={() => store.setGuide(!guide)}>
        ?
      </button>
    </div>
  );
}
