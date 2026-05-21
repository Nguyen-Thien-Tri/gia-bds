export function formatDate(d?: Date): string {
  const date = d ? new Date(d) : new Date();
  const dd = String(date.getDate()).padStart(2, "0");
  const mm = String(date.getMonth() + 1).padStart(2, "0");
  const yyyy = date.getFullYear();
  return `${dd}/${mm}/${yyyy}`;
}

export const formatNumber = (num: number) =>
  new Intl.NumberFormat("de-DE").format(num);

export function getMostRecentMonday(date = new Date()): Date {
  const day = date.getDay();
  const diff = day === 0 ? 6 : day - 1;
  const monday = new Date(date);
  monday.setDate(date.getDate() - diff);
  monday.setHours(0, 0, 0, 0);
  return monday;
}
