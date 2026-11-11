import { useAppState } from '../store';
import { ClipEditor } from './ClipEditor';
import { DeviceDialog } from './DeviceDialog';
import { KitEditor } from './KitEditor';
import { Library } from './Library';
import { MemoryDialog } from './MemoryDialog';
import { Toast } from './Toast';

/** The editors, the library and the device dialogs as the store opens them, and the notice toast: shared by the app and the guide. */
export function Modals() {
  const state = useAppState();
  const top = state.editors[state.editors.length - 1];
  return (
    <>
      {top?.kind === 'clip' && <ClipEditor target={top.target} />}
      {top?.kind === 'kit' && <KitEditor slot={top.slot} />}
      {top?.kind === 'memory' && <MemoryDialog />}
      {state.library.open && <Library />}
      {state.device && <DeviceDialog mode={state.device} />}
      <Toast />
    </>
  );
}
