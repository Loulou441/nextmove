"use client";

/**
 * Pictogrammes originaux par compétence, dessinés à la main (pas une
 * librairie d'icônes générique) pour coller précisément au geste ou au
 * concept mesuré. Trait fin, hérite de currentColor pour prendre
 * automatiquement la couleur du score (vert/bleu/orange).
 */
import type { SVGProps } from "react";

type IconProps = { size?: number } & SVGProps<SVGSVGElement>;

function Base({ size = 16, children, ...props }: IconProps & { children: React.ReactNode }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      {children}
    </svg>
  );
}

// Service : balle qui s'élève, avec une trace de mouvement courbée derrière elle.
export function ServeIcon(props: IconProps) {
  return (
    <Base {...props}>
      <circle cx="17" cy="6" r="2.2" />
      <path d="M7 20c2-4 3-9 3-13" />
      <path d="M6 9c1.5-1 3-1 4.5 0" />
    </Base>
  );
}

// Retour : flèche qui rebondit et repart en sens inverse.
export function ReturnIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M4 16c3-6 8-9 14-8" />
      <path d="M14 5l4 3-4 3" />
      <circle cx="5" cy="18" r="1.6" />
    </Base>
  );
}

// Troisième balle (pickleball) : trois points en enfilade, le dernier ciblé.
export function ThirdShotIcon(props: IconProps) {
  return (
    <Base {...props}>
      <circle cx="5" cy="18" r="1.4" />
      <circle cx="12" cy="12" r="1.4" />
      <circle cx="19" cy="6" r="2.6" />
      <path d="M19 4v4M17 6h4" />
    </Base>
  );
}

// Dinking : petite balle qui frôle une ligne de filet basse.
export function DinkingIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M4 16h16" />
      <path d="M8 16V9M8 9l-2 2M8 9l2 2" />
      <circle cx="16" cy="11" r="1.8" />
    </Base>
  );
}

// Volée : raquette qui intercepte la balle juste au-dessus du filet.
export function VolleyIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M4 18h16" />
      <ellipse cx="15" cy="8" rx="4" ry="5" transform="rotate(25 15 8)" />
      <path d="M12.5 12l-3 5" />
      <circle cx="7" cy="10" r="1.6" />
    </Base>
  );
}

// Défense : posture basse, jambes fléchies, bras ouverts.
export function DefenseIcon(props: IconProps) {
  return (
    <Base {...props}>
      <circle cx="12" cy="5" r="2" />
      <path d="M12 7v6" />
      <path d="M12 13l-4 6M12 13l4 6" />
      <path d="M12 9l-5 3M12 9l5 3" />
    </Base>
  );
}

// Lob : trajectoire haute en cloche au-dessus du filet.
export function LobIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M4 18c2-10 14-10 16 0" />
      <circle cx="12" cy="6.5" r="1.8" />
      <path d="M4 18h16" />
    </Base>
  );
}

// Smash : éclair qui percute la balle vers le bas.
export function SmashIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M13 3l-5 8h4l-3 10 7-11h-4l3-7z" strokeLinejoin="round" />
    </Base>
  );
}

// Déplacement / positionnement : empreintes de pas.
export function MovementIcon(props: IconProps) {
  return (
    <Base {...props}>
      <ellipse cx="8" cy="7" rx="2" ry="3" />
      <ellipse cx="16" cy="13" rx="2" ry="3" />
      <ellipse cx="8" cy="19" rx="1.6" ry="2.4" />
    </Base>
  );
}

// Régularité : onde régulière, amplitude constante.
export function RegularityIcon(props: IconProps) {
  return (
    <Base {...props}>
      <path d="M3 12c2-4 4-4 6 0s4 4 6 0 4-4 6 0" />
    </Base>
  );
}

export const SKILL_ICONS: Record<string, (props: IconProps) => React.ReactElement> = {
  serve: ServeIcon,
  return: ReturnIcon,
  thirdShot: ThirdShotIcon,
  dinking: DinkingIcon,
  volley: VolleyIcon,
  defense: DefenseIcon,
  lob: LobIcon,
  smash: SmashIcon,
  movement: MovementIcon,
  regularity: RegularityIcon,
};