export function formatReasonList(reasons, backendExplanation) {
  const list = Array.isArray(reasons) ? reasons.filter(Boolean) : [];
  if (list.length) return list;
  if (backendExplanation && backendExplanation.trim()) return [backendExplanation.trim()];
  return [];
}
