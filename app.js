const MOBILE_MQ = window.matchMedia("(max-width: 900px)");

const state = {
  cafes: [],
  filter: "all",
  query: "",
  markers: new Map(),
  activeId: null,
  theme: document.documentElement.dataset.theme === "light" ? "light" : "dark",
  drawerOpen: false,
};

const appEl = document.getElementById("app");
const listEl = document.getElementById("cafe-list");
const searchEl = document.getElementById("search");
const filtersEl = document.getElementById("filters");
const detailEl = document.getElementById("detail");
const sidebarEl = document.getElementById("sidebar");
const backdropEl = document.getElementById("sidebar-backdrop");
const toggleBtn = document.getElementById("toggle-sidebar");
const closeBtn = document.getElementById("sidebar-close");
const themeBtns = [
  document.getElementById("theme-toggle"),
  document.getElementById("theme-toggle-side"),
].filter(Boolean);
const themeColorMeta = document.getElementById("theme-color");

const PLACEHOLDER =
  "data:image/svg+xml," +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" viewBox="0 0 800 600">
      <defs>
        <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="#2c1d12"/>
          <stop offset="100%" stop-color="#4a2f1c"/>
        </linearGradient>
      </defs>
      <rect width="800" height="600" fill="url(#g)"/>
      <circle cx="400" cy="270" r="70" fill="none" stroke="#c9a46a" stroke-width="10"/>
      <path d="M340 270 h120" stroke="#c9a46a" stroke-width="10" stroke-linecap="round"/>
      <text x="400" y="400" text-anchor="middle" fill="#e8d9c4" font-family="Georgia, serif" font-size="28">café</text>
    </svg>`
  );

const map = L.map("map", {
  zoomControl: false,
  attributionControl: true,
}).setView([-34.6, -58.4], 12);

L.control.zoom({ position: "topright" }).addTo(map);

const TILES = {
  dark: [
    {
      url: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
      options: {
        attribution: "Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ",
        maxZoom: 16,
      },
    },
    {
      url: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Reference/MapServer/tile/{z}/{y}/{x}",
      options: {
        attribution: "",
        maxZoom: 16,
        opacity: 0.85,
      },
    },
  ],
  light: [
    {
      url: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
      options: {
        attribution: "Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ",
        maxZoom: 16,
      },
    },
    {
      url: "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}",
      options: {
        attribution: "",
        maxZoom: 16,
        opacity: 0.9,
      },
    },
  ],
};

let tileLayers = [];

function applyTiles(theme) {
  tileLayers.forEach((layer) => map.removeLayer(layer));
  tileLayers = TILES[theme].map((spec) =>
    L.tileLayer(spec.url, spec.options).addTo(map)
  );
}

const markerLayer = L.layerGroup().addTo(map);

function cafeImage(cafe) {
  return cafe.image || PLACEHOLDER;
}

function bindImgFallback(img) {
  img.addEventListener(
    "error",
    () => {
      if (img.dataset.fallbackApplied) return;
      img.dataset.fallbackApplied = "1";
      img.src = PLACEHOLDER;
    },
    { once: true }
  );
}

function matchesFilter(cafe) {
  if (state.filter === "top10") return cafe.rank <= 10;
  return true;
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function mapsUrl(cafe) {
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(
    `${cafe.name} ${cafe.address || cafe.location} Argentina`
  )}`;
}

function matchesQuery(cafe) {
  const q = state.query.trim().toLowerCase();
  if (!q) return true;
  return (
    cafe.name.toLowerCase().includes(q) ||
    cafe.location.toLowerCase().includes(q) ||
    String(cafe.rank) === q
  );
}

function visibleCafes() {
  return state.cafes.filter((c) => matchesFilter(c) && matchesQuery(c));
}

function markerHtml(cafe, active = false) {
  const top = cafe.rank <= 10 ? "top10" : "";
  const act = active ? "active" : "";
  return `<div class="marker-pill ${top} ${act}">${cafe.rank}</div>`;
}

function createIcon(cafe, active = false) {
  const size = cafe.rank <= 10 ? 36 : 30;
  return L.divIcon({
    className: "rank-marker",
    html: markerHtml(cafe, active),
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
}

function isMobile() {
  return MOBILE_MQ.matches;
}

function setDrawerX(px) {
  sidebarEl.style.setProperty("--drawer-x", `${px}px`);
}

function setSidebarOpen(open) {
  state.drawerOpen = open;
  sidebarEl.classList.toggle("open", open);
  appEl.classList.toggle("drawer-open", open);
  backdropEl.classList.toggle("visible", open);
  toggleBtn.setAttribute("aria-expanded", String(open));
  toggleBtn.setAttribute("aria-label", open ? "Cerrar lista" : "Abrir lista");
  setDrawerX(0);
  if (isMobile()) {
    map.dragging[open ? "disable" : "enable"]();
  }
}

function openSidebar() {
  setSidebarOpen(true);
}

function closeSidebar() {
  setSidebarOpen(false);
}

function toggleSidebar() {
  if (state.drawerOpen) closeSidebar();
  else openSidebar();
}

function applyTheme(theme) {
  state.theme = theme;
  document.documentElement.dataset.theme = theme;
  try {
    localStorage.setItem("cafe-theme", theme);
  } catch (e) {}
  if (themeColorMeta) {
    themeColorMeta.content = theme === "light" ? "#f4efe6" : "#1a120b";
  }
  const nextLabel = theme === "light" ? "Cambiar a modo oscuro" : "Cambiar a modo claro";
  themeBtns.forEach((btn) => btn.setAttribute("aria-label", nextLabel));
  applyTiles(theme);
}

function toggleTheme() {
  applyTheme(state.theme === "light" ? "dark" : "light");
}

function detailPadding() {
  const size = map.getSize();
  const detailOpen = !detailEl.hidden;
  const cardW = detailOpen ? Math.min(400, size.x * 0.42) + 24 : 24;
  const sideW = isMobile() ? 24 : Math.min(420, size.x * 0.35);
  const bottom = isMobile() && detailOpen ? Math.min(size.y * 0.5, 280) : 48;
  return {
    paddingTopLeft: L.point(sideW + 16, 48),
    paddingBottomRight: L.point(cardW, bottom),
  };
}

function ensureCafeVisible(cafe) {
  const latlng = L.latLng(cafe.lat, cafe.lng);
  const { paddingTopLeft, paddingBottomRight } = detailPadding();
  map.panInside(latlng, {
    paddingTopLeft,
    paddingBottomRight,
    animate: true,
    duration: 0.35,
  });
}

function openDetail(cafe) {
  state.activeId = cafe.rank;

  const img = document.getElementById("detail-image");
  img.dataset.fallbackApplied = "";
  img.src = cafeImage(cafe);
  img.alt = cafe.name;
  bindImgFallback(img);

  document.getElementById("detail-rank").textContent = `#${cafe.rank}`;
  document.getElementById("detail-name").textContent = cafe.name;
  document.getElementById("detail-loc").textContent = cafe.address || cafe.location;
  document.getElementById("detail-desc").textContent = cafe.description;
  document.getElementById("detail-maps").href = mapsUrl(cafe);

  const ig = document.getElementById("detail-ig");
  if (cafe.instagram) {
    ig.hidden = false;
    ig.href = cafe.instagram;
  } else {
    ig.hidden = true;
    ig.removeAttribute("href");
  }

  detailEl.hidden = false;
  appEl.classList.add("detail-open");

  document.querySelectorAll(".cafe-item").forEach((el) => {
    const on = Number(el.dataset.rank) === cafe.rank;
    el.classList.toggle("active", on);
    el.classList.toggle("expanded", on);
  });

  state.markers.forEach((marker, rank) => {
    const c = state.cafes.find((x) => x.rank === rank);
    if (!c) return;
    marker.setIcon(createIcon(c, rank === cafe.rank));
    if (rank === cafe.rank) marker.setZIndexOffset(1000);
    else marker.setZIndexOffset(0);
  });
}

function closeDetail() {
  detailEl.hidden = true;
  appEl.classList.remove("detail-open");
  state.activeId = null;
  document.querySelectorAll(".cafe-item").forEach((el) => {
    el.classList.remove("active", "expanded");
  });
  state.markers.forEach((marker, rank) => {
    const cafe = state.cafes.find((c) => c.rank === rank);
    if (cafe) marker.setIcon(createIcon(cafe, false));
    marker.setZIndexOffset(0);
  });
}

function focusCafe(cafe, { fromList = false, revealMap = false } = {}) {
  map.closePopup();
  openDetail(cafe);

  if (fromList && isMobile() && revealMap) {
    closeSidebar();
    window.setTimeout(() => ensureCafeVisible(cafe), 360);
  } else {
    requestAnimationFrame(() => ensureCafeVisible(cafe));
  }

  if (fromList) {
    renderList();
    const item = listEl.querySelector(`[data-rank="${cafe.rank}"]`);
    if (item) item.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }
}

function renderList() {
  const cafes = visibleCafes();
  listEl.innerHTML = cafes
    .map((cafe) => {
      const open = state.activeId === cafe.rank;
      const ig = cafe.instagram
        ? `<a href="${escapeHtml(cafe.instagram)}" target="_blank" rel="noopener">Instagram</a>`
        : "";
      return `
      <li class="cafe-item ${cafe.rank <= 10 ? "top10" : ""} ${
        open ? "active expanded" : ""
      }" data-rank="${cafe.rank}">
        <div class="cafe-row">
          <img src="${cafeImage(cafe)}" alt="" loading="lazy" />
          <div class="cafe-meta">
            <span class="cafe-rank">#${cafe.rank}</span>
            <p class="cafe-name">${escapeHtml(cafe.name)}</p>
            <p class="cafe-loc">${escapeHtml(cafe.location)}</p>
          </div>
        </div>
        <div class="cafe-extra">
          <p class="cafe-blurb">${escapeHtml(cafe.description)}</p>
          <div class="cafe-extra-links">
            ${ig}
            <a href="${mapsUrl(cafe)}" target="_blank" rel="noopener">Google Maps</a>
            <button type="button" class="cafe-show-map">Ver en el mapa</button>
          </div>
        </div>
      </li>`;
    })
    .join("");

  listEl.querySelectorAll(".cafe-item").forEach((el) => {
    const img = el.querySelector("img");
    if (img) bindImgFallback(img);
    const cafe = state.cafes.find((c) => c.rank === Number(el.dataset.rank));
    if (!cafe) return;
    el.addEventListener("click", (e) => {
      if (e.target.closest("a, button")) return;
      if (state.activeId === cafe.rank) {
        closeDetail();
        return;
      }
      focusCafe(cafe, { fromList: true });
    });
    el.querySelector(".cafe-show-map")?.addEventListener("click", (e) => {
      e.stopPropagation();
      focusCafe(cafe, { fromList: true, revealMap: true });
    });
  });
}

function renderMarkers({ fit = false } = {}) {
  markerLayer.clearLayers();
  state.markers.clear();
  const cafes = visibleCafes();

  cafes.forEach((cafe) => {
    const marker = L.marker([cafe.lat, cafe.lng], {
      icon: createIcon(cafe, state.activeId === cafe.rank),
      riseOnHover: true,
      keyboard: true,
      title: `#${cafe.rank} ${cafe.name}`,
    });

    marker.on("click", (e) => {
      L.DomEvent.stopPropagation(e);
      focusCafe(cafe);
    });

    marker.addTo(markerLayer);
    state.markers.set(cafe.rank, marker);
  });

  if (fit && cafes.length) {
    const bounds = L.latLngBounds(cafes.map((c) => [c.lat, c.lng]));
    map.fitBounds(bounds.pad(0.08), {
      animate: true,
      maxZoom: 12,
      ...detailPadding(),
    });
  }
}

function refresh({ fit = false } = {}) {
  renderList();
  renderMarkers({ fit });
}

searchEl.addEventListener("input", (e) => {
  state.query = e.target.value;
  refresh({ fit: true });
});

filtersEl.addEventListener("click", (e) => {
  const btn = e.target.closest(".chip");
  if (!btn) return;
  state.filter = btn.dataset.filter;
  filtersEl.querySelectorAll(".chip").forEach((c) => c.classList.toggle("active", c === btn));
  refresh({ fit: true });
});

document.getElementById("detail-close").addEventListener("click", closeDetail);

toggleBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  toggleSidebar();
});
closeBtn.addEventListener("click", closeSidebar);
backdropEl.addEventListener("click", closeSidebar);
themeBtns.forEach((btn) => btn.addEventListener("click", toggleTheme));

document.addEventListener("keydown", (e) => {
  if (e.key !== "Escape") return;
  if (state.drawerOpen && isMobile()) closeSidebar();
  else if (!detailEl.hidden) document.getElementById("detail-close").click();
});

let swipe = null;

sidebarEl.addEventListener(
  "touchstart",
  (e) => {
    if (!isMobile() || !state.drawerOpen) return;
    const t = e.touches[0];
    swipe = { x: t.clientX, y: t.clientY, dx: 0, locked: null };
  },
  { passive: true }
);

sidebarEl.addEventListener(
  "touchmove",
  (e) => {
    if (!swipe) return;
    const t = e.touches[0];
    const dx = t.clientX - swipe.x;
    const dy = t.clientY - swipe.y;
    if (swipe.locked == null && (Math.abs(dx) > 8 || Math.abs(dy) > 8)) {
      swipe.locked = Math.abs(dx) > Math.abs(dy) ? "x" : "y";
    }
    if (swipe.locked !== "x") return;
    swipe.dx = Math.min(0, dx);
    sidebarEl.style.transition = "none";
    backdropEl.style.transition = "none";
    setDrawerX(swipe.dx);
    const progress = Math.min(1, Math.abs(swipe.dx) / sidebarEl.getBoundingClientRect().width);
    backdropEl.style.opacity = String(1 - progress);
  },
  { passive: true }
);

function endSwipe() {
  if (!swipe) return;
  const shouldClose = swipe.locked === "x" && swipe.dx < -72;
  sidebarEl.style.transition = "";
  backdropEl.style.transition = "";
  backdropEl.style.opacity = "";
  setDrawerX(0);
  if (shouldClose) closeSidebar();
  swipe = null;
}

sidebarEl.addEventListener("touchend", endSwipe);
sidebarEl.addEventListener("touchcancel", endSwipe);

MOBILE_MQ.addEventListener("change", () => {
  closeSidebar();
  map.dragging.enable();
  requestAnimationFrame(() => map.invalidateSize());
});

window.addEventListener("resize", () => {
  map.invalidateSize();
});

applyTheme(state.theme);

async function boot() {
  const res = await fetch("./data/cafes.json");
  const data = await res.json();
  state.cafes = data.cafes;
  refresh({ fit: true });
  requestAnimationFrame(() => map.invalidateSize());
}

boot().catch((err) => {
  listEl.innerHTML = `<li style="padding:1rem;color:#e2c48a">No se pudo cargar data/cafes.json<br/><small>${err.message}</small></li>`;
});
