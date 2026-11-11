/** Hand the viewer a file through a temporary object URL. */
export function downloadBytes(name: string, bytes: Uint8Array, type = 'audio/wav'): void {
  const url = URL.createObjectURL(new Blob([bytes as BlobPart], { type }));
  const a = document.createElement('a');
  a.href = url;
  a.download = name;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
