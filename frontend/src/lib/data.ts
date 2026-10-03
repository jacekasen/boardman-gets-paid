import snapshot from "@/data/league.json";
export const league = snapshot;
export type Player = (typeof league.players)[number];
export type Team = (typeof league.teams)[number];
export const brackets = [
  "Below tax",
  "Luxury tax",
  "First apron",
  "Second apron",
];
export const money = (value: number, signed = false) =>
  `${value < 0 ? "−" : signed && value > 0 ? "+" : ""}$${(Math.abs(value) / 1e6).toFixed(2)}M`;
export const compact = (value: number) => `$${(value / 1e6).toFixed(1)}M`;
export const initials = (name: string) =>
  name
    .split(" ")
    .map((n) => n[0])
    .slice(0, 2)
    .join("");
export type Delta = {
  team: string;
  pre_payroll: number;
  post_payroll: number;
  pre_bracket: number;
  post_bracket: number;
  delta_nsv: number;
  friction_relief: number;
};
export type TradeResult = {
  is_legal: boolean;
  violations: string[];
  delta_a: Delta;
  delta_b: Delta;
};
