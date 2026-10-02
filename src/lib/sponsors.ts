import SponsorsData from "../../public/json/sponsors.json";

/**
 * Patrocinio segun el dossier 2026-27 ("Dosier patrocinios", octubre 2026).
 *
 * Cada entrada de public/json/sponsors.json lleva un "tier":
 *   institucional   respaldo institucional (UPV, Generacion Espontanea)
 *   principal       colaboradores principales: van en la cabecera de la home
 *   platino | oro | plata | bronce   niveles de pago del dossier
 *   patrocinador    patrocinador sin nivel asignado todavia
 *
 * Todo lo que pinta patrocinadores sale de aqui, para que la cabecera, el
 * carrusel del pie y la pagina de partners cuenten lo mismo.
 */
export type PaidTier = "platino" | "oro" | "plata" | "bronce";

export interface TierInfo {
  key: PaidTier;
  label: string;
  /** Altura del logo en el carrusel del pie: mas aportacion, logo mas grande. */
  carouselHeight: number;
  /** El dossier promete a este nivel aparecer tambien en la cabecera. */
  inHeader: boolean;
}

export const TIERS: TierInfo[] = [
  { key: "platino", label: "Platino", carouselHeight: 80, inHeader: true },
  { key: "oro", label: "Oro", carouselHeight: 68, inHeader: false },
  { key: "plata", label: "Plata", carouselHeight: 56, inHeader: false },
  { key: "bronce", label: "Bronce", carouselHeight: 46, inHeader: false },
];

/** Patrocinadores sin nivel asignado: tamano intermedio hasta que se les asigne. */
const UNTIERED_CAROUSEL_HEIGHT = 52;

export interface Sponsor {
  name: string;
  logo: string;
  url?: string;
  tier: string;
  description?: string;
}

const sponsors = (SponsorsData.sponsors ?? []) as Sponsor[];
const paidKeys = new Set<string>(TIERS.map((t) => t.key));
export const isPaidTier = (tier: string): tier is PaidTier => paidKeys.has(tier);

const byTier = (tier: string) => sponsors.filter((s) => s.tier === tier);

export const institutionalPartners = () => byTier("institucional");
export const mainCollaborators = () => byTier("principal");

/** Los cuatro niveles con sus patrocinadores (la web tiene una seccion por nivel). */
export const sponsorsByTier = () => TIERS.map((tier) => ({ ...tier, sponsors: byTier(tier.key) }));

/** Patrocinadores que aun no tienen nivel del dossier asignado. */
export const untieredSponsors = () => byTier("patrocinador");

/** Cabecera de la home: nivel Platino primero y despues colaboradores principales. */
export const headerSponsors = () => [
  ...sponsors.filter((s) => TIERS.some((t) => t.inHeader && t.key === s.tier)),
  ...mainCollaborators(),
];

/**
 * Carrusel del pie: el resto de patrocinadores (ni cabecera ni institucionales),
 * de mayor a menor aportacion y con el logo mas grande cuanto mayor es el nivel.
 */
export const footerSponsors = () => [
  ...TIERS.filter((t) => !t.inHeader).flatMap((t) =>
    byTier(t.key).map((s) => ({ ...s, logoHeight: t.carouselHeight }))
  ),
  ...untieredSponsors().map((s) => ({ ...s, logoHeight: UNTIERED_CAROUSEL_HEIGHT })),
];

if (import.meta.env.DEV) {
  const known = new Set(["institucional", "principal", "patrocinador", ...paidKeys]);
  const unknown = sponsors.filter((s) => !known.has(s.tier));
  if (unknown.length) {
    console.warn(
      `[sponsors] tier desconocido en public/json/sponsors.json: ` +
        unknown.map((s) => `${s.name} (${s.tier})`).join(", ")
    );
  }
}
