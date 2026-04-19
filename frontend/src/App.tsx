import { Routes, Route, NavLink } from "react-router-dom";
import Creator from "./pages/Creator";
import Gallery from "./pages/Gallery";
import "./App.css";

const TODAY = new Date()
  .toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  })
  .toUpperCase();

export default function App() {
  return (
    <div className="app">
      <header>
        <div>
          <div className="eyebrow">Atelier №01 · Reference Sheets</div>
          <h1>
            Canvas <em>Creator</em>
          </h1>
          <nav className="main-nav">
            <NavLink to="/" end className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
              Workbench
            </NavLink>
            <NavLink to="/gallery" className={({ isActive }) => isActive ? "nav-link active" : "nav-link"}>
              Archive
            </NavLink>
          </nav>
          <p className="subtitle">
            A quiet little workbench for arranging references onto a single drawing sheet.
          </p>
        </div>
        <div className="meta">
          <div><strong>{TODAY}</strong></div>
          <div>EST. 2026</div>
        </div>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<Creator />} />
          <Route path="/gallery" element={<Gallery />} />
        </Routes>
      </main>

      <footer className="app-footer">
        <span className="rule" />
        <div className="footer-content">
          <span>ATELIER №01</span>
          <span className="dot">·</span>
          <span>CANVAS CREATOR</span>
        </div>
      </footer>
    </div>
  );
}
