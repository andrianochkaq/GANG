import { Link } from 'react-router-dom';

import AuthIcon from './AuthIcon';

type AuthBackLinkProps = {
  to: string;
  label: string;
};

export default function AuthBackLink({ to, label }: AuthBackLinkProps) {
  return (
    <Link to={to} className="fc-auth__back">
      <AuthIcon name="back" />
      {label}
    </Link>
  );
}
