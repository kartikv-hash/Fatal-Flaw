import { useState, useCallback, useMemo, useRef, useEffect } from "react";

const LAYERS = [
  { id: "wetlands", label: "Wetlands (NWI)", color: "#22d3ee", icon: "💧" },
  { id: "floodplains", label: "Floodplains (FEMA)", color: "#60a5fa", icon: "🌊" },
  { id: "transmission", label: "Transmission Lines", color: "#f59e0b", icon: "⚡" },
  { id: "substations", label: "Substations", color: "#f97316", icon: "🔌" },
  { id: "soil", label: "Soil Analysis", color: "#a78bfa", icon: "🪨" },
  { id: "sentiment", label: "Community Sentiment", color: "#fb7185", icon: "👥" },
  { id: "nodes", label: "Pricing Nodes", color: "#34d399", icon: "💲" },
];

const PARCELS = [
  { id: 1, name: "Parcel A — Reeves Co., TX", x: 168, y: 268, w: 62, h: 48, acres: 482, owner: "Bar-T Ranch LLC", zoning: "Agricultural", state: "TX", county: "Reeves",
    wetland: 3, flood: "X", floodCov: 2, soilScore: 91, drainage: "Well drained", hydric: false, pileSuit: "High",
    transLine: 1.8, voltage: "345 kV", substation: 1.2, interco: "High",
    hub: "ERCOT North Hub", hubLMP: 44, node: "REEVES_345_WIND", nodeLMP: 41, basis: -3, congestion: "Low", congFreq: 6, curtail: "Low", revRisk: "Low",
    sentiment: 0.32, oppRisk: "Low", issues: ["Minimal opposition", "Pro-development county"],
    score: 93, projType: "Utility Solar", permitRisk: "Low", revPotential: "High" },
  { id: 2, name: "Parcel B — Kern Co., CA", x: 78, y: 228, w: 55, h: 42, acres: 310, owner: "Sunland Holdings", zoning: "Agricultural", state: "CA", county: "Kern",
    wetland: 8, flood: "AE", floodCov: 10, soilScore: 78, drainage: "Moderately drained", hydric: false, pileSuit: "Moderate",
    transLine: 4.1, voltage: "230 kV", substation: 3.5, interco: "Moderate",
    hub: "CAISO SP15", hubLMP: 52, node: "KERN_230_SOLAR", nodeLMP: 46, basis: -6, congestion: "Medium", congFreq: 14, curtail: "Moderate", revRisk: "Moderate",
    sentiment: -0.18, oppRisk: "Moderate", issues: ["Wildlife concerns", "Visual impact"],
    score: 81, projType: "Utility Solar", permitRisk: "Moderate", revPotential: "High" },
  { id: 3, name: "Parcel C — Logan Co., IL", x: 338, y: 188, w: 50, h: 40, acres: 520, owner: "Heartland Ag Corp", zoning: "Agricultural", state: "IL", county: "Logan",
    wetland: 18, flood: "A", floodCov: 15, soilScore: 62, drainage: "Poorly drained", hydric: true, pileSuit: "Low",
    transLine: 6.8, voltage: "138 kV", substation: 5.4, interco: "Low",
    hub: "MISO Indiana Hub", hubLMP: 36, node: "LOGAN_138_WIND", nodeLMP: 31, basis: -5, congestion: "High", congFreq: 22, curtail: "High", revRisk: "High",
    sentiment: -0.45, oppRisk: "High", issues: ["Strong local opposition", "Wetland advocacy groups", "Township moratorium pending"],
    score: 48, projType: "Not Recommended", permitRisk: "High", revPotential: "Low" },
  { id: 4, name: "Parcel D — Custer Co., OK", x: 258, y: 248, w: 58, h: 44, acres: 640, owner: "Prairie Wind LLC", zoning: "Rural", state: "OK", county: "Custer",
    wetland: 1, flood: "X", floodCov: 0, soilScore: 88, drainage: "Well drained", hydric: false, pileSuit: "High",
    transLine: 2.4, voltage: "345 kV", substation: 1.9, interco: "High",
    hub: "SPP South Hub", hubLMP: 38, node: "CUSTER_345_WIND", nodeLMP: 35, basis: -3, congestion: "Low", congFreq: 8, curtail: "Low", revRisk: "Low",
    sentiment: 0.55, oppRisk: "Low", issues: ["Community supportive", "Existing wind development nearby"],
    score: 90, projType: "Wind Farm", permitRisk: "Low", revPotential: "High" },
  { id: 5, name: "Parcel E — Chautauqua Co., NY", x: 418, y: 148, w: 48, h: 38, acres: 275, owner: "Lake Erie Land Trust", zoning: "Mixed Use", state: "NY", county: "Chautauqua",
    wetland: 12, flood: "AE", floodCov: 8, soilScore: 70, drainage: "Moderately drained", hydric: false, pileSuit: "Moderate",
    transLine: 5.5, voltage: "230 kV", substation: 4.2, interco: "Moderate",
    hub: "NYISO Zone A", hubLMP: 48, node: "CHAUT_230_WIND", nodeLMP: 42, basis: -6, congestion: "Medium", congFreq: 16, curtail: "Moderate", revRisk: "Moderate",
    sentiment: -0.30, oppRisk: "Moderate", issues: ["Lakeshore viewshed concerns", "Active environmental groups"],
    score: 64, projType: "Community Solar", permitRisk: "Moderate", revPotential: "Moderate" },
];

const TRANSMISSION_LINES = [
  { x1: 50, y1: 260, x2: 200, y2: 220 }, { x1: 200, y1: 220, x2: 350, y2: 200 },
  { x1: 350, y1: 200, x2: 480, y2: 160 }, { x1: 150, y1: 300, x2: 300, y2: 270 },
  { x1: 300, y1: 270, x2: 420, y2: 240 }, { x1: 100, y1: 180, x2: 250, y2: 170 },
  { x1: 250, y1: 170, x2: 400, y2: 180 },
];

const SUBSTATIONS = [
  { x: 200, y: 220, name: "Mesa Sub" }, { x: 350, y: 200, name: "Central Sub" },
  { x: 300, y: 270, name: "Plains Sub" }, { x: 150, y: 300, name: "Valley Sub" },
  { x: 420, y: 180, name: "Northeast Sub" },
];

const WETLAND_ZONES = [
  { cx: 345, cy: 195, rx: 30, ry: 22 }, { cx: 430, cy: 155, rx: 18, ry: 14 },
  { cx: 180, cy: 240, rx: 14, ry: 10 },
];

const FLOOD_ZONES = [
  { cx: 100, cy: 250, rx: 45, ry: 25 }, { cx: 430, cy: 155, rx: 25, ry: 18 },
  { cx: 340, cy: 200, rx: 28, ry: 20 },
];

const PRICING_NODES = [
  { x: 175, y: 285, label: "$44" }, { x: 95, y: 240, label: "$52" },
  { x: 345, y: 195, label: "$36" }, { x: 270, y: 260, label: "$38" },
  { x: 425, y: 155, label: "$48" },
];

const SENTIMENT_DOTS = [
  { x: 180, y: 275, s: 0.3 }, { x: 90, y: 235, s: -0.2 },
  { x: 350, y: 190, s: -0.5 }, { x: 265, y: 255, s: 0.5 },
  { x: 435, y: 150, s: -0.3 },
];

const riskColor = (v) => v === "Low" ? "#22c55e" : v === "Moderate" || v === "Medium" ? "#f59e0b" : "#ef4444";
const scoreColor = (s) => s >= 80 ? "#22c55e" : s >= 60 ? "#f59e0b" : "#ef4444";

function Badge({ children, color }) {
  return <span style={{ background: color + "22", color, border: `1px solid ${color}44`, borderRadius: 6, padding: "2px 8px", fontSize: 11, fontWeight: 600 }}>{children}</span>;
}

function ScoreBar({ value, max = 100, color }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <div style={{ flex: 1, height: 8, background: "#1e293b", borderRadius: 4, overflow: "hidden" }}>
        <div style={{ width: `${(value / max) * 100}%`, height: "100%", background: color, borderRadius: 4, transition: "width 0.5s" }} />
      </div>
      <span style={{ fontSize: 12, fontWeight: 700, color, minWidth: 32, textAlign: "right" }}>{value}</span>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 16 }}>
      <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: "#94a3b8", marginBottom: 8 }}>{title}</div>
      {children}
    </div>
  );
}

function Row({ label, value, badge }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "3px 0", fontSize: 13 }}>
      <span style={{ color: "#94a3b8" }}>{label}</span>
      {badge ? <Badge color={badge.color}>{value}</Badge> : <span style={{ color: "#e2e8f0", fontWeight: 600 }}>{value}</span>}
    </div>
  );
}

function MapCanvas({ layers, selected, onSelect, hoveredId, setHoveredId }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const cvs = canvasRef.current;
    if (!cvs) return;
    const ctx = cvs.getContext("2d");
    const W = cvs.width, H = cvs.height;
    ctx.clearRect(0, 0, W, H);

    // BG
    const grad = ctx.createLinearGradient(0, 0, W, H);
    grad.addColorStop(0, "#0c1222"); grad.addColorStop(1, "#111827");
    ctx.fillStyle = grad; ctx.fillRect(0, 0, W, H);

    // Grid
    ctx.strokeStyle = "#1e293b33"; ctx.lineWidth = 0.5;
    for (let x = 0; x < W; x += 30) { ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke(); }
    for (let y = 0; y < H; y += 30) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }

    // US outline (simplified)
    ctx.beginPath();
    ctx.moveTo(40,160); ctx.lineTo(60,140); ctx.lineTo(120,130); ctx.lineTo(180,120); ctx.lineTo(240,115);
    ctx.lineTo(320,120); ctx.lineTo(400,110); ctx.lineTo(460,120); ctx.lineTo(490,140);
    ctx.lineTo(485,180); ctx.lineTo(470,200); ctx.lineTo(450,230); ctx.lineTo(430,260);
    ctx.lineTo(400,280); ctx.lineTo(350,300); ctx.lineTo(280,310); ctx.lineTo(220,315);
    ctx.lineTo(160,310); ctx.lineTo(120,300); ctx.lineTo(80,290); ctx.lineTo(50,270);
    ctx.lineTo(35,240); ctx.lineTo(30,200); ctx.closePath();
    ctx.fillStyle = "#1e293b44"; ctx.fill();
    ctx.strokeStyle = "#334155"; ctx.lineWidth = 1.5; ctx.stroke();

    // Flood zones
    if (layers.floodplains) {
      FLOOD_ZONES.forEach(z => {
        ctx.beginPath(); ctx.ellipse(z.cx, z.cy, z.rx, z.ry, 0, 0, Math.PI * 2);
        ctx.fillStyle = "#60a5fa18"; ctx.fill();
        ctx.strokeStyle = "#60a5fa44"; ctx.lineWidth = 1; ctx.stroke();
      });
    }

    // Wetlands
    if (layers.wetlands) {
      WETLAND_ZONES.forEach(z => {
        ctx.beginPath(); ctx.ellipse(z.cx, z.cy, z.rx, z.ry, 0, 0, Math.PI * 2);
        ctx.fillStyle = "#22d3ee18"; ctx.fill();
        ctx.strokeStyle = "#22d3ee55"; ctx.lineWidth = 1; ctx.setLineDash([4, 3]); ctx.stroke(); ctx.setLineDash([]);
      });
    }

    // Soil
    if (layers.soil) {
      PARCELS.forEach(p => {
        const c = p.soilScore >= 80 ? "#a78bfa" : p.soilScore >= 60 ? "#c084fc" : "#e879f9";
        ctx.fillStyle = c + "15";
        ctx.fillRect(p.x - 4, p.y - 4, p.w + 8, p.h + 8);
      });
    }

    // Transmission
    if (layers.transmission) {
      TRANSMISSION_LINES.forEach(l => {
        ctx.beginPath(); ctx.moveTo(l.x1, l.y1); ctx.lineTo(l.x2, l.y2);
        ctx.strokeStyle = "#f59e0b88"; ctx.lineWidth = 2; ctx.stroke();
        // glow
        ctx.strokeStyle = "#f59e0b22"; ctx.lineWidth = 6; ctx.stroke();
      });
    }

    // Substations
    if (layers.substations) {
      SUBSTATIONS.forEach(s => {
        ctx.beginPath(); ctx.arc(s.x, s.y, 6, 0, Math.PI * 2);
        ctx.fillStyle = "#f97316"; ctx.fill();
        ctx.strokeStyle = "#f9731644"; ctx.lineWidth = 8; ctx.stroke();
        ctx.fillStyle = "#f9731699"; ctx.font = "9px system-ui"; ctx.fillText(s.name, s.x + 10, s.y + 3);
      });
    }

    // Pricing nodes
    if (layers.nodes) {
      PRICING_NODES.forEach(n => {
        ctx.beginPath(); ctx.arc(n.x, n.y, 10, 0, Math.PI * 2);
        ctx.fillStyle = "#34d39922"; ctx.fill();
        ctx.strokeStyle = "#34d399"; ctx.lineWidth = 1.5; ctx.stroke();
        ctx.fillStyle = "#34d399"; ctx.font = "bold 10px system-ui"; ctx.textAlign = "center";
        ctx.fillText(n.label, n.x, n.y + 4); ctx.textAlign = "start";
      });
    }

    // Sentiment
    if (layers.sentiment) {
      SENTIMENT_DOTS.forEach(d => {
        const c = d.s > 0 ? "#22c55e" : d.s > -0.3 ? "#f59e0b" : "#ef4444";
        ctx.beginPath(); ctx.arc(d.x, d.y, 14, 0, Math.PI * 2);
        ctx.fillStyle = c + "18"; ctx.fill();
        ctx.strokeStyle = c + "66"; ctx.lineWidth = 1; ctx.setLineDash([3, 2]); ctx.stroke(); ctx.setLineDash([]);
      });
    }

    // Parcels
    PARCELS.forEach(p => {
      const isSel = selected === p.id;
      const isHov = hoveredId === p.id;
      const sc = scoreColor(p.score);
      ctx.fillStyle = isSel ? sc + "44" : isHov ? sc + "28" : sc + "14";
      ctx.fillRect(p.x, p.y, p.w, p.h);
      ctx.strokeStyle = isSel ? sc : isHov ? sc + "aa" : sc + "55";
      ctx.lineWidth = isSel ? 2.5 : isHov ? 2 : 1;
      ctx.strokeRect(p.x, p.y, p.w, p.h);
      // label
      ctx.fillStyle = isSel ? "#fff" : "#cbd5e1";
      ctx.font = `${isSel ? "bold " : ""}10px system-ui`;
      ctx.fillText(p.name.split("—")[0].trim(), p.x + 4, p.y + 13);
      ctx.fillStyle = sc; ctx.font = "bold 11px system-ui";
      ctx.fillText(p.score, p.x + p.w - 18, p.y + p.h - 5);
    });

  }, [layers, selected, hoveredId]);

  const handleClick = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const sx = canvasRef.current.width / rect.width;
    const sy = canvasRef.current.height / rect.height;
    const mx = (e.clientX - rect.left) * sx;
    const my = (e.clientY - rect.top) * sy;
    const hit = PARCELS.find(p => mx >= p.x && mx <= p.x + p.w && my >= p.y && my <= p.y + p.h);
    if (hit) onSelect(hit.id);
  };

  const handleMove = (e) => {
    const rect = canvasRef.current.getBoundingClientRect();
    const sx = canvasRef.current.width / rect.width;
    const sy = canvasRef.current.height / rect.height;
    const mx = (e.clientX - rect.left) * sx;
    const my = (e.clientY - rect.top) * sy;
    const hit = PARCELS.find(p => mx >= p.x && mx <= p.x + p.w && my >= p.y && my <= p.y + p.h);
    setHoveredId(hit ? hit.id : null);
  };

  return (
    <canvas ref={canvasRef} width={530} height={370} onClick={handleClick} onMouseMove={handleMove}
      style={{ width: "100%", height: "100%", cursor: hoveredId ? "pointer" : "crosshair", borderRadius: 12 }} />
  );
}

function QueryPanel({ onApply }) {
  const [acres, setAcres] = useState(200);
  const [transDist, setTransDist] = useState(10);
  const [nodePrice, setNodePrice] = useState(30);
  const [wetMax, setWetMax] = useState(20);
  const [minScore, setMinScore] = useState(0);
  const sliderStyle = { width: "100%", accentColor: "#6366f1", height: 4, cursor: "pointer" };
  const labelStyle = { display: "flex", justifyContent: "space-between", fontSize: 12, color: "#94a3b8", marginBottom: 2 };
  const valStyle = { color: "#e2e8f0", fontWeight: 700 };
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div><div style={labelStyle}><span>Min Acres</span><span style={valStyle}>{acres}</span></div><input type="range" min={50} max={1000} value={acres} onChange={e => setAcres(+e.target.value)} style={sliderStyle} /></div>
      <div><div style={labelStyle}><span>Max Trans. Distance (mi)</span><span style={valStyle}>{transDist}</span></div><input type="range" min={1} max={20} value={transDist} onChange={e => setTransDist(+e.target.value)} style={sliderStyle} /></div>
      <div><div style={labelStyle}><span>Min Node Price ($/MWh)</span><span style={valStyle}>${nodePrice}</span></div><input type="range" min={10} max={80} value={nodePrice} onChange={e => setNodePrice(+e.target.value)} style={sliderStyle} /></div>
      <div><div style={labelStyle}><span>Max Wetland %</span><span style={valStyle}>{wetMax}%</span></div><input type="range" min={0} max={30} value={wetMax} onChange={e => setWetMax(+e.target.value)} style={sliderStyle} /></div>
      <div><div style={labelStyle}><span>Min Site Score</span><span style={valStyle}>{minScore}</span></div><input type="range" min={0} max={100} value={minScore} onChange={e => setMinScore(+e.target.value)} style={sliderStyle} /></div>
      <button onClick={() => onApply({ acres, transDist, nodePrice, wetMax, minScore })}
        style={{ marginTop: 4, padding: "8px 0", background: "linear-gradient(135deg, #6366f1, #8b5cf6)", color: "#fff", border: "none", borderRadius: 8, fontWeight: 700, fontSize: 13, cursor: "pointer" }}>
        Search Parcels
      </button>
    </div>
  );
}

const WEIGHTS = { transmission: 25, nodePrice: 15, wetlands: 15, flood: 10, soil: 15, sentiment: 10, landCost: 10 };

export default function App() {
  const [layers, setLayers] = useState({ wetlands: true, floodplains: true, transmission: true, substations: true, soil: false, sentiment: false, nodes: true });
  const [selected, setSelected] = useState(1);
  const [tab, setTab] = useState("analysis");
  const [hoveredId, setHoveredId] = useState(null);
  const [queryResults, setQueryResults] = useState(null);

  const toggleLayer = (id) => setLayers(l => ({ ...l, [id]: !l[id] }));
  const p = PARCELS.find(p => p.id === selected) || PARCELS[0];

  const handleQuery = (q) => {
    const results = PARCELS.filter(p => p.acres >= q.acres && p.transLine <= q.transDist && p.nodeLMP >= q.nodePrice && p.wetland <= q.wetMax && p.score >= q.minScore);
    setQueryResults(results);
    setTab("query");
  };

  const panelBg = "#0f172a"; const cardBg = "#1e293b"; const border = "#334155";

  return (
    <div style={{ display: "flex", height: "100vh", fontFamily: "'Inter', system-ui, sans-serif", background: "#0a0e1a", color: "#e2e8f0", overflow: "hidden" }}>
      {/* Left Sidebar */}
      <div style={{ width: 220, background: panelBg, borderRight: `1px solid ${border}`, display: "flex", flexDirection: "column", flexShrink: 0 }}>
        <div style={{ padding: "16px 16px 12px", borderBottom: `1px solid ${border}` }}>
          <div style={{ fontSize: 15, fontWeight: 800, background: "linear-gradient(135deg, #6366f1, #22d3ee)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>SiteIQ</div>
          <div style={{ fontSize: 10, color: "#64748b", marginTop: 2 }}>Renewable Energy Siting Platform</div>
        </div>
        <div style={{ padding: 12, flex: 1, overflowY: "auto" }}>
          <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: "#64748b", marginBottom: 8 }}>Map Layers</div>
          {LAYERS.map(l => (
            <button key={l.id} onClick={() => toggleLayer(l.id)}
              style={{ display: "flex", alignItems: "center", gap: 8, width: "100%", padding: "7px 10px", marginBottom: 3, background: layers[l.id] ? l.color + "18" : "transparent", border: `1px solid ${layers[l.id] ? l.color + "44" : "transparent"}`, borderRadius: 8, color: layers[l.id] ? l.color : "#64748b", fontSize: 12, cursor: "pointer", textAlign: "left", transition: "all 0.2s" }}>
              <span style={{ fontSize: 13 }}>{l.icon}</span>
              <span style={{ flex: 1 }}>{l.label}</span>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: layers[l.id] ? l.color : "#334155" }} />
            </button>
          ))}
          <div style={{ fontSize: 10, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: "#64748b", margin: "16px 0 8px" }}>Parcels</div>
          {PARCELS.map(pr => (
            <button key={pr.id} onClick={() => { setSelected(pr.id); setTab("analysis"); }}
              style={{ display: "flex", alignItems: "center", justifyContent: "space-between", width: "100%", padding: "7px 10px", marginBottom: 3, background: selected === pr.id ? "#6366f118" : "transparent", border: `1px solid ${selected === pr.id ? "#6366f144" : "transparent"}`, borderRadius: 8, color: selected === pr.id ? "#c7d2fe" : "#94a3b8", fontSize: 11, cursor: "pointer", textAlign: "left", transition: "all 0.2s" }}>
              <span>{pr.name.split("—")[0].trim()}</span>
              <span style={{ fontWeight: 700, color: scoreColor(pr.score) }}>{pr.score}</span>
            </button>
          ))}
        </div>
        <div style={{ padding: 12, borderTop: `1px solid ${border}`, fontSize: 10, color: "#475569" }}>
          Scoring: Transmission 25% · Price 15% · Wetlands 15% · Soil 15% · Flood 10% · Sentiment 10% · Cost 10%
        </div>
      </div>

      {/* Center — Map */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        <div style={{ padding: "10px 16px", borderBottom: `1px solid ${border}`, display: "flex", gap: 12, alignItems: "center", background: panelBg }}>
          {["analysis", "query", "scoring"].map(t => (
            <button key={t} onClick={() => setTab(t)}
              style={{ padding: "5px 14px", borderRadius: 6, border: "none", background: tab === t ? "#6366f1" : "transparent", color: tab === t ? "#fff" : "#94a3b8", fontSize: 12, fontWeight: 600, cursor: "pointer", transition: "all 0.2s" }}>
              {t === "analysis" ? "Site Analysis" : t === "query" ? "Developer Query" : "Score Breakdown"}
            </button>
          ))}
          <div style={{ flex: 1 }} />
          <span style={{ fontSize: 11, color: "#64748b" }}>Click a parcel on the map to analyze</span>
        </div>
        <div style={{ flex: 1, padding: 12, position: "relative" }}>
          <MapCanvas layers={layers} selected={selected} onSelect={(id) => { setSelected(id); setTab("analysis"); }} hoveredId={hoveredId} setHoveredId={setHoveredId} />
          {/* Legend */}
          <div style={{ position: "absolute", bottom: 20, left: 20, background: panelBg + "ee", backdropFilter: "blur(8px)", border: `1px solid ${border}`, borderRadius: 10, padding: "8px 12px", display: "flex", gap: 14, fontSize: 10, color: "#94a3b8" }}>
            <span><span style={{ display: "inline-block", width: 8, height: 8, borderRadius: 2, background: "#22c55e", marginRight: 4 }} />Score ≥80</span>
            <span><span style={{ display: "inline-block", width: 8, height: 8, borderRadius: 2, background: "#f59e0b", marginRight: 4 }} />Score 60-79</span>
            <span><span style={{ display: "inline-block", width: 8, height: 8, borderRadius: 2, background: "#ef4444", marginRight: 4 }} />Score &lt;60</span>
          </div>
        </div>
      </div>

      {/* Right Panel */}
      <div style={{ width: 310, background: panelBg, borderLeft: `1px solid ${border}`, overflowY: "auto", flexShrink: 0 }}>
        <div style={{ padding: 16 }}>
          {tab === "analysis" && (
            <>
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 15, fontWeight: 800, color: "#f1f5f9" }}>{p.name}</div>
                <div style={{ display: "flex", gap: 8, marginTop: 6, flexWrap: "wrap" }}>
                  <Badge color={scoreColor(p.score)}>Score: {p.score}/100</Badge>
                  <Badge color="#6366f1">{p.acres} ac</Badge>
                  <Badge color={riskColor(p.permitRisk)}>{p.projType}</Badge>
                </div>
              </div>
              <Section title="Ownership">
                <Row label="Owner" value={p.owner} />
                <Row label="Zoning" value={p.zoning} />
                <Row label="County" value={`${p.county} Co., ${p.state}`} />
              </Section>
              <Section title="Environmental">
                <Row label="Wetland Coverage" value={`${p.wetland}%`} badge={{ color: p.wetland > 10 ? "#ef4444" : p.wetland > 5 ? "#f59e0b" : "#22c55e" }} />
                <Row label="Flood Zone" value={p.flood} badge={{ color: p.flood === "X" ? "#22c55e" : p.flood === "AE" ? "#f59e0b" : "#ef4444" }} />
                <Row label="Flood Coverage" value={`${p.floodCov}%`} />
              </Section>
              <Section title="Soil Analysis">
                <div style={{ marginBottom: 6 }}><ScoreBar value={p.soilScore} color="#a78bfa" /></div>
                <Row label="Drainage" value={p.drainage} />
                <Row label="Hydric Soil" value={p.hydric ? "Yes" : "No"} badge={{ color: p.hydric ? "#ef4444" : "#22c55e" }} />
                <Row label="Pile Suitability" value={p.pileSuit} badge={{ color: riskColor(p.pileSuit === "High" ? "Low" : p.pileSuit === "Moderate" ? "Moderate" : "High") }} />
              </Section>
              <Section title="Transmission Access">
                <Row label="Nearest Line" value={`${p.transLine} mi`} />
                <Row label="Voltage" value={p.voltage} />
                <Row label="Nearest Substation" value={`${p.substation} mi`} />
                <Row label="Interconnection" value={p.interco} badge={{ color: riskColor(p.interco === "High" ? "Low" : p.interco) }} />
              </Section>
              <Section title="Hub / Node Pricing">
                <Row label="Hub" value={p.hub} />
                <Row label="Hub LMP" value={`$${p.hubLMP}/MWh`} />
                <Row label="Node" value={p.node} />
                <Row label="Node LMP" value={`$${p.nodeLMP}/MWh`} />
                <Row label="Basis" value={`$${p.basis}/MWh`} badge={{ color: Math.abs(p.basis) > 5 ? "#ef4444" : "#f59e0b" }} />
                <Row label="Congestion Risk" value={p.congestion} badge={{ color: riskColor(p.congestion) }} />
              </Section>
              <Section title="Congestion Analytics">
                <Row label="Congestion Freq." value={`${p.congFreq}%`} />
                <Row label="Curtailment Risk" value={p.curtail} badge={{ color: riskColor(p.curtail) }} />
                <Row label="Revenue Risk" value={p.revRisk} badge={{ color: riskColor(p.revRisk) }} />
              </Section>
              <Section title="Community Sentiment">
                <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                  <span style={{ fontSize: 22, fontWeight: 800, color: p.sentiment > 0 ? "#22c55e" : p.sentiment > -0.3 ? "#f59e0b" : "#ef4444" }}>{p.sentiment > 0 ? "+" : ""}{p.sentiment.toFixed(2)}</span>
                  <Badge color={riskColor(p.oppRisk)}>{p.oppRisk} Opposition</Badge>
                </div>
                {p.issues.map((issue, i) => (
                  <div key={i} style={{ fontSize: 12, color: "#94a3b8", padding: "2px 0" }}>• {issue}</div>
                ))}
              </Section>
            </>
          )}

          {tab === "query" && (
            <>
              <div style={{ fontSize: 15, fontWeight: 800, color: "#f1f5f9", marginBottom: 16 }}>Developer Query</div>
              <QueryPanel onApply={handleQuery} />
              {queryResults !== null && (
                <div style={{ marginTop: 16 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: "#64748b", marginBottom: 8 }}>{queryResults.length} Results</div>
                  {queryResults.length === 0 && <div style={{ fontSize: 13, color: "#64748b", padding: 16, textAlign: "center" }}>No parcels match your criteria. Try adjusting filters.</div>}
                  {queryResults.map(r => (
                    <button key={r.id} onClick={() => { setSelected(r.id); setTab("analysis"); }}
                      style={{ display: "block", width: "100%", textAlign: "left", padding: 12, marginBottom: 6, background: cardBg, border: `1px solid ${border}`, borderRadius: 10, cursor: "pointer", color: "#e2e8f0" }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontWeight: 700, fontSize: 13 }}>{r.name}</span>
                        <span style={{ fontWeight: 800, color: scoreColor(r.score) }}>{r.score}</span>
                      </div>
                      <div style={{ display: "flex", gap: 6, marginTop: 6, flexWrap: "wrap" }}>
                        <Badge color="#6366f1">{r.acres} ac</Badge>
                        <Badge color="#f59e0b">{r.transLine} mi</Badge>
                        <Badge color="#34d399">${r.nodeLMP}/MWh</Badge>
                        <Badge color="#22d3ee">{r.wetland}% wet</Badge>
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </>
          )}

          {tab === "scoring" && (
            <>
              <div style={{ fontSize: 15, fontWeight: 800, color: "#f1f5f9", marginBottom: 4 }}>Score Breakdown</div>
              <div style={{ fontSize: 12, color: "#64748b", marginBottom: 16 }}>{p.name}</div>
              <div style={{ textAlign: "center", marginBottom: 20 }}>
                <div style={{ fontSize: 52, fontWeight: 900, color: scoreColor(p.score), lineHeight: 1 }}>{p.score}</div>
                <div style={{ fontSize: 12, color: "#64748b", marginTop: 4 }}>/ 100 Site Score</div>
              </div>
              {[
                { label: "Transmission Proximity", w: 25, val: p.transLine <= 2 ? 95 : p.transLine <= 5 ? 75 : 40 },
                { label: "Node Pricing", w: 15, val: p.nodeLMP >= 40 ? 90 : p.nodeLMP >= 35 ? 70 : 50 },
                { label: "Wetland Risk", w: 15, val: p.wetland <= 5 ? 95 : p.wetland <= 10 ? 65 : 30 },
                { label: "Soil Suitability", w: 15, val: p.soilScore },
                { label: "Flood Risk", w: 10, val: p.flood === "X" ? 95 : p.flood === "AE" ? 60 : 35 },
                { label: "Community Sentiment", w: 10, val: p.sentiment > 0.2 ? 90 : p.sentiment > -0.2 ? 60 : 25 },
                { label: "Land Cost", w: 10, val: 70 },
              ].map((f, i) => (
                <div key={i} style={{ marginBottom: 12 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, color: "#94a3b8", marginBottom: 4 }}>
                    <span>{f.label}</span>
                    <span style={{ color: "#64748b" }}>{f.w}% weight</span>
                  </div>
                  <ScoreBar value={f.val} color={f.val >= 80 ? "#22c55e" : f.val >= 60 ? "#f59e0b" : "#ef4444"} />
                </div>
              ))}
              <div style={{ marginTop: 20, padding: 12, background: cardBg, borderRadius: 10, border: `1px solid ${border}` }}>
                <Row label="Recommended Type" value={p.projType} badge={{ color: p.projType === "Not Recommended" ? "#ef4444" : "#22c55e" }} />
                <Row label="Permit Risk" value={p.permitRisk} badge={{ color: riskColor(p.permitRisk) }} />
                <Row label="Revenue Potential" value={p.revPotential} badge={{ color: riskColor(p.revPotential === "High" ? "Low" : p.revPotential === "Moderate" ? "Moderate" : "High") }} />
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
