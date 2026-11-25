// Stroke icons from the auth boards: 24 × 24, stroke 2, round caps, currentColor.
const ICON_PATHS = {
  back: <path d="M15 6l-6 6 6 6" />,
  phone: (
    <>
      <rect x="7" y="2" width="10" height="20" rx="2" />
      <path d="M11 18h2" />
    </>
  ),
  telegram: (
    <>
      <path d="M22 3L2 11l7 3 3 7z" />
      <path d="M9 14l13-11" />
    </>
  ),
  info: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 11v5M12 8h.01" />
    </>
  ),
  mail: (
    <>
      <rect x="3" y="5" width="18" height="14" rx="2" />
      <path d="M3 7l9 6 9-6" />
    </>
  ),
  home: (
    <>
      <path d="M3 11l9-7 9 7" />
      <path d="M5 10v10h14V10" />
    </>
  ),
} as const;

export type AuthIconName = keyof typeof ICON_PATHS;

type AuthIconProps = {
  name: AuthIconName;
};

export default function AuthIcon({ name }: AuthIconProps) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {ICON_PATHS[name]}
    </svg>
  );
}
