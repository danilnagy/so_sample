/** Where the app and its guide live, under the build's base path. */
export const APP_URL = import.meta.env.BASE_URL;
export const GUIDE_URL = `${import.meta.env.BASE_URL}guide`;

/** Whether the page's address is the guide's. */
export function isGuidePath(): boolean {
  return typeof location !== 'undefined' && location.pathname.replace(/\/$/, '') === GUIDE_URL;
}
