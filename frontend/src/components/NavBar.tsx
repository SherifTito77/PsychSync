// // // // src/components/NavBar.tsx
import { Link } from "react-router-dom";
export default function NavBar() {
  return (
    <nav style={{ marginBottom: "1rem" }}>
      <Link to="/teams" style={{ marginRight: "1rem" }}>Teams</Link>
      <Link to="/assessments" style={{ marginRight: "1rem" }}>Assessments</Link>
      <Link to="/login">Login</Link>
    </nav>
  );
}
