// The JWT lives in localStorage so it survives reloads and is sent as a
// Bearer header. Tradeoff: any injected script could read it (an httpOnly
// cookie would not be readable), accepted for this project's scope.

const STORAGE_KEY = "forkful.token";
const CHANGE_EVENT = "forkful:token-change";

export function readToken(): string | null {
  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

export function writeToken(token: string | null): void {
  try {
    if (token) {
      window.localStorage.setItem(STORAGE_KEY, token);
    } else {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  } finally {
    window.dispatchEvent(new Event(CHANGE_EVENT));
  }
}

/** Notifies on changes in this tab and in other tabs (the `storage` event). */
export function subscribeToken(onChange: () => void): () => void {
  window.addEventListener(CHANGE_EVENT, onChange);
  window.addEventListener("storage", onChange);
  return () => {
    window.removeEventListener(CHANGE_EVENT, onChange);
    window.removeEventListener("storage", onChange);
  };
}
