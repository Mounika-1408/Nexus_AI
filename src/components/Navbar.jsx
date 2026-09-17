import "../styles/Navbar.css";
import { FaBell, FaUserCircle } from "react-icons/fa";

function Navbar() {
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
          <span>Admin</span>
        </div>

      </div>

    </header>
  );
}

export default Navbar;