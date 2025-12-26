// // // // src/components/NavBar.tsx
import { Link } from "react-router-dom";
export default function NavBar() {
  return (
    <nav
      role="navigation"
      aria-label="Main navigation"
      style={{ marginBottom: "1rem" }}
    >
      <Link
        to="/teams"
        style={{ marginRight: "1rem" }}
        aria-current="false"
      >
        Teams
      </Link>
      <Link
        to="/assessments"
        style={{ marginRight: "1rem" }}
        aria-current="false"
      >
        Assessments
      </Link>
      <Link
        to="/clinical-assessments"
        style={{ marginRight: "1rem" }}
        aria-current="false"
        className="text-blue-600 font-medium"
      >
        Mental Health
      </Link>
      <Link
        to="/login"
        aria-current="false"
      >
        Login
      </Link>
    </nav>
  );
}
