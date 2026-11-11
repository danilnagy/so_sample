/**
 * Layout tokens shared by the code and the stylesheet. The stylesheet reads them as
 * custom properties that `applyTokens` sets on the document, so each value lives here once.
 */

/** Height of a table row and a roll lane, without the 1px rule under it; also every small waveform. */
export const ROW_HEIGHT = 19;

export function applyTokens(): void {
  document.documentElement.style.setProperty('--row', `${ROW_HEIGHT}px`);
}
