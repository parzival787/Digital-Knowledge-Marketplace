export function auctionDurationSeconds(value: string, unit: "minutes" | "hours"): bigint {
  const amount = Number(value);
  const seconds = amount * (unit === "minutes" ? 60 : 3600);
  if (!Number.isInteger(amount) || seconds < 120 || seconds > 720 * 3600) {
    throw new Error("Choose a whole-number duration from 2 minutes to 720 hours.");
  }
  return BigInt(seconds);
}
