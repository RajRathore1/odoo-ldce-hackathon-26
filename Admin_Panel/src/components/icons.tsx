type IconProps = { className?: string };

export function DashboardIcon({ className }: IconProps) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <rect x="3" y="3" width="6" height="6" rx="1.2" />
      <rect x="11" y="3" width="6" height="6" rx="1.2" />
      <rect x="3" y="11" width="6" height="6" rx="1.2" />
      <rect x="11" y="11" width="6" height="6" rx="1.2" />
    </svg>
  );
}

export function UsersIcon({ className }: IconProps) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <circle cx="7" cy="6.5" r="2.5" />
      <path d="M2.5 16c0-2.5 2-4 4.5-4s4.5 1.5 4.5 4" />
      <circle cx="14.5" cy="7" r="2" />
      <path d="M12.8 12.2c1.9.3 3.2 1.6 3.2 3.8" />
    </svg>
  );
}

export function MapPinIcon({ className }: IconProps) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <path d="M10 18s6-5.5 6-10a6 6 0 1 0-12 0c0 4.5 6 10 6 10Z" />
      <circle cx="10" cy="8" r="2" />
    </svg>
  );
}

export function ActivityIcon({ className }: IconProps) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <path d="M2 10h3l2-5 4 10 2-5h5" />
    </svg>
  );
}

export function ChartIcon({ className }: IconProps) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <path d="M3 3v14h14" />
      <path d="M6 14v-4M10 14V6M14 14v-7" />
    </svg>
  );
}

export function SearchIcon({ className }: IconProps) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.7"
      strokeLinecap="round"
      className={className}
      aria-hidden
    >
      <circle cx="9" cy="9" r="6" />
      <path d="m13.5 13.5 3.5 3.5" />
    </svg>
  );
}

export function BellIcon({ className }: IconProps) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <path d="M5 8a5 5 0 0 1 10 0c0 3 1 4 1 5H4c0-1 1-2 1-5Z" />
      <path d="M8 16a2 2 0 0 0 4 0" />
    </svg>
  );
}

export function WalletIcon({ className }: IconProps) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <rect x="2.5" y="5.5" width="15" height="10" rx="1.5" />
      <path d="M2.5 8.5h15" />
      <circle cx="14" cy="11.5" r="1" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function TrendUpIcon({ className }: IconProps) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <path d="M3 13l5-5 3 3 6-6" />
      <path d="M13 5h4v4" />
    </svg>
  );
}

export function SuitcaseIcon({ className }: IconProps) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <rect x="2.5" y="6" width="15" height="10.5" rx="1.5" />
      <path d="M7 6V4.5A1.5 1.5 0 0 1 8.5 3h3A1.5 1.5 0 0 1 13 4.5V6" />
      <path d="M2.5 10.5h15" />
    </svg>
  );
}

export function LogOutIcon({ className }: IconProps) {
  return (
    <svg
      viewBox="0 0 20 20"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden
    >
      <path d="M8 17H5a1.5 1.5 0 0 1-1.5-1.5v-11A1.5 1.5 0 0 1 5 3h3" />
      <path d="M13 14l4-4-4-4M17 10H7" />
    </svg>
  );
}
