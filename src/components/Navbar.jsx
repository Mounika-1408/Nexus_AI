import "../styles/Navbar.css";
import { FaBell, FaUserCircle } from "react-icons/fa";

function Navbar() {
  let displayName = "Admin";
  try {
    const storedUser = localStorage.getItem("nexusaiUser");
    if (storedUser) {
      const user = JSON.parse(storedUser);
      displayName = user.name || user.email?.split("@")[0] || "Admin";
    }
  } catch {
    displayName = "Admin";
  }

  return (
    <header className="navbar">

      <input
        type="text"
        placeholder="Search..."
        className="search-box"
      />

      <div className="navbar-right">

        <FaBell className="nav-icon" />

        <div className="profile">
          <FaUserCircle className="profile-icon" />
          <span>{displayName}</span>
        </div>

      </div>

    </header>
  );
}

export default Navbar;