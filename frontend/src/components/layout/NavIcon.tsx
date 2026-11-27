// Stroke icons from the Nav3 / DSide boards (24 px grid, 2 px stroke).
export type NavIconName = 'fridge' | 'chef' | 'calories' | 'profile' | 'home' | 'cart' | 'chevron';

const PATHS: Record<NavIconName, JSX.Element> = {
  fridge: (
    <>
      <rect x="5" y="3" width="14" height="18" rx="2" />
      <path d="M5 10h14M9 6v2M9 13v3" />
    </>
  ),
  chef: (
    <>
      <path d="M12 3l1.8 4.7 4.7 1.8-4.7 1.8L12 16l-1.8-4.7-4.7-1.8 4.7-1.8z" />
      <path d="M19 15l.7 1.8 1.8.7-1.8.7L19 20l-.7-1.8-1.8-.7 1.8-.7z" />
    </>
  ),
  calories: <path d="M5 20V11M11 20V5M17 20v-7M3 20h18" />,
  profile: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21c0-4 4-6 8-6s8 2 8 6" />
    </>
  ),
  home: (
    <>
      <path d="M3 11l9-7 9 7" />
      <path d="M5 10v10h14V10" />
    </>
  ),
  cart: (
    <>
      <circle cx="9" cy="20" r="1.5" />
      <circle cx="18" cy="20" r="1.5" />
      <path d="M2 3h3l2.5 12h12l2-8H6.2" />
    </>
  ),
  chevron: <path d="M6 9l6 6 6-6" />,
};

export default function NavIcon({ name }: { name: NavIconName }) {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {PATHS[name]}
    </svg>
  );
}
