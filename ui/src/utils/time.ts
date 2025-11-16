export function formatTime(ts: number): string {
  const date = new Date(ts * 1000);
  return date.toLocaleString();
}
