// Canonical client-diagnostics CLIENT DECK builder (Spice-branded .pptx).
//
// This is the SINGLE source of truth for the client-shared deck. It is fully
// DATA-DRIVEN: every number and every line of client-facing narrative is read
// from `findings.json` + `metrics.json` in the run directory — the SAME
// contract `references/build_report.py` consumes. There are ZERO per-client
// literals in this file. If you find yourself wanting to hardcode a client
// name / dollar figure / store name here, that is a bug: put the value in
// findings.json instead and extend the contract (see report-data-contract.md).
//
// Colour tokens are PARSED at build time from the colocated
// `report_style.css` (Spice Design System) :root block — never hardcoded —
// so the deck and the HTML report can never drift.
//
// Charts are embedded from <run_dir>/charts/*.png when present; any chart
// that is absent is skipped gracefully (no broken image, no crash).
//
// Usage:
//   npm install pptxgenjs            # in the run dir (one-time)
//   node references/build_deck.js <run_dir>
//
// Output: <run_dir>/<client-slug>-deck.pptx
"use strict";

const fs = require("fs");
const path = require("path");

// ----------------------------------------------------------------------- //
// Resolve pptxgenjs from the run dir first (where `npm install` is run per  //
// the SKILL workflow), then fall back to the skill dir / global.            //
// ----------------------------------------------------------------------- //
function loadPptxgen(runDir) {
  const tries = [
    path.join(runDir, "node_modules", "pptxgenjs"),
    path.join(__dirname, "node_modules", "pptxgenjs"),
    "pptxgenjs",
  ];
  for (const t of tries) {
    try { return require(t); } catch (_) { /* keep trying */ }
  }
  throw new Error(
    "pptxgenjs not found. Run `npm install pptxgenjs` in the run dir " +
    "(or the skill references/ dir).");
}

// ----------------------------------------------------------------------- //
// Spice Design System tokens — PARSED from report_style.css :root, never    //
// hardcoded, so deck + report share one palette source.                     //
// ----------------------------------------------------------------------- //
function hex6(v) {
  // "#fa4803" -> "FA4803"; "#fff" -> "FFFFFF"
  let h = String(v).trim().replace(/^#/, "");
  if (h.length === 3) h = h.split("").map((c) => c + c).join("");
  return h.toUpperCase();
}

function parseTokens(cssPath) {
  const css = fs.readFileSync(cssPath, "utf8");
  const root = (css.match(/:root\s*\{([\s\S]*?)\}/) || [, ""])[1];
  const vars = {};
  const re = /--([a-z0-9-]+)\s*:\s*([^;]+);/gi;
  let m;
  while ((m = re.exec(root)) !== null) {
    const val = m[2].trim();
    if (/^#[0-9a-f]{3,8}$/i.test(val)) vars[m[1]] = hex6(val);
  }
  const need = (k) => {
    if (!vars[k]) throw new Error(`token --${k} missing from report_style.css`);
    return vars[k];
  };
  return {
    orange: need("spice"),
    orangeTint: need("spice-tint"),
    ink: need("ink-900"),     // headings / dark slides
    ink2: need("ink-700"),    // body
    cream: need("cream"),
    white: need("ink-0"),
    muted: need("ink-500"),
    line: need("ink-200"),
    red: need("err"),
    redBg: need("err-tint"),
    green: need("ok"),
    amber: need("warn"),
  };
}

// ----------------------------------------------------------------------- //
// Small helpers                                                             //
// ----------------------------------------------------------------------- //
const isPresent = (v) =>
  v !== null && v !== undefined && !(typeof v === "string" && !v.trim());

function fmtMoney(v) {
  if (typeof v === "number") return "$" + Math.round(v).toLocaleString("en-US");
  return String(v);
}
function fmtInt(v) {
  if (typeof v === "number") return Math.round(v).toLocaleString("en-US");
  return String(v);
}
// hero slot value: number -> infer money/int by label, string -> verbatim
function heroVal(label, v) {
  if (!isPresent(v)) return "n/a*";
  if (typeof v !== "number") return String(v);
  if (/gross|payout|aov/i.test(label)) return fmtMoney(v);
  return fmtInt(v);
}

// ----------------------------------------------------------------------- //
// Main                                                                      //
// ----------------------------------------------------------------------- //
function main(argv) {
  const runDir = path.resolve(argv[2] || ".");
  const fj = JSON.parse(fs.readFileSync(path.join(runDir, "findings.json")));
  const mj = JSON.parse(fs.readFileSync(path.join(runDir, "metrics.json")));

  // CSS tokens: prefer the run-dir copy (matches the report build), else the
  // skill's canonical references/report_style.css.
  const cssRun = path.join(runDir, "report_style.css");
  const cssRef = path.join(__dirname, "report_style.css");
  const C = parseTokens(fs.existsSync(cssRun) ? cssRun : cssRef);

  // Self-contained brand assets (copied into references/assets — no Cowork
  // path dependency).
  const ASSETS = path.join(__dirname, "assets");
  const LOGO_BADGE = path.join(ASSETS, "spice_wordmark_cream_on_orange_square.png");
  const LOGO_RED = path.join(ASSETS, "spice_wordmark_red.png");
  const hasBadge = fs.existsSync(LOGO_BADGE);
  const hasRed = fs.existsSync(LOGO_RED);

  // Chart resolver — only returns a path if the PNG actually exists.
  const chart = (name) => {
    const p = path.join(runDir, "charts", name);
    return fs.existsSync(p) ? p : null;
  };

  const Pptx = loadPptxgen(runDir);
  const p = new Pptx();
  p.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
  p.author = "Spice Digital";

  const client = fj.client || "Client";
  const window = fj.window || "";
  const cycle = fj.cycle || fj.cycle_label || "Diagnostic";
  const platforms = fj.platforms || "";
  const locsLine = fj.locations_line || (fj.n_locations ? String(fj.n_locations) : "");
  const prepared = fj.prepared_line || "Prepared by Spice Digital";
  const deck = fj.deck || {};
  const footerStr = `Spice Digital  ·  ${client}  ·  ${cycle}`;
  p.title = `${client} — ${cycle}`;

  const W = 13.333, H = 7.5;
  const HF = "Helvetica Neue", BF = "Helvetica Neue"; // Geist substitute
  const sh = () => ({ type: "outer", color: "000000", blur: 7, offset: 2, angle: 135, opacity: 0.10 });

  // Fit an image into a box preserving aspect ratio (centered).
  function imgBox(p2, ar, x, y, maxW, maxH) {
    let w = maxW, h = w / ar;
    if (h > maxH) { h = maxH; w = h * ar; }
    return { path: p2, x: x + (maxW - w) / 2, y: y + (maxH - h) / 2, w, h };
  }

  function lightBase(s, kicker, title) {
    s.background = { color: C.white };
    s.addShape(p.shapes.RECTANGLE, { x: 0, y: 0, w: 0.18, h: H, fill: { color: C.orange } });
    s.addText(String(kicker).toUpperCase(), { x: 0.7, y: 0.42, w: 9, h: 0.3, fontFace: HF,
      fontSize: 12, bold: true, color: C.orange, charSpacing: 3, margin: 0 });
    s.addText(String(title), { x: 0.7, y: 0.72, w: 10.5, h: 0.85, fontFace: HF,
      fontSize: 32, bold: true, color: C.ink, margin: 0 });
    if (hasRed) s.addImage({ path: LOGO_RED, x: 11.55, y: 0.45, w: 1.3, h: 0.563 });
  }
  function footer(s, n, darkbg) {
    const col = darkbg ? C.muted : C.muted;
    s.addText(footerStr, { x: 0.7, y: H - 0.45, w: 9.5, h: 0.3, fontFace: BF,
      fontSize: 9, color: col, margin: 0 });
    s.addText(String(n), { x: W - 1.0, y: H - 0.45, w: 0.5, h: 0.3, fontFace: BF,
      fontSize: 9, color: col, align: "right", margin: 0 });
  }
  // strip a leading emoji/symbol + space from contract strings for clean kicker
  const clean = (t) => String(t || "").replace(/^[^\w$(]+\s*/, "").trim();

  let slideNo = 0;
  const next = () => ++slideNo;

  // 1 — TITLE (dark) ----------------------------------------------------- //
  let s = p.addSlide();
  s.background = { color: C.ink };
  s.addShape(p.shapes.RECTANGLE, { x: 0, y: 0, w: 0.28, h: H, fill: { color: C.orange } });
  if (hasBadge) s.addImage({ path: LOGO_BADGE, x: 11.5, y: 0.6, w: 1.15, h: 1.15 });
  s.addText((deck.title_kicker || "Spice Digital · Delivery Marketplace Diagnostic").toUpperCase(),
    { x: 0.9, y: 1.5, w: 11, h: 0.4, fontFace: HF, fontSize: 14, bold: true,
      color: C.orange, charSpacing: 3, margin: 0 });
  s.addText(String(client), { x: 0.85, y: 2.05, w: 11.5, h: 1.1, fontFace: HF,
    fontSize: 60, bold: true, color: C.white, margin: 0 });
  s.addText(`${cycle}${window ? "  —  " + window : ""}`, { x: 0.9, y: 3.25, w: 11.5,
    h: 0.6, fontFace: HF, fontSize: 24, color: C.cream, margin: 0 });
  const titleLines = [];
  if (locsLine) titleLines.push({ text: `${locsLine} · ${platforms}`.replace(/ · $/, ""), options: { breakLine: true, color: C.cream } });
  if (deck.baseline_note) titleLines.push({ text: deck.baseline_note, options: { breakLine: true, color: C.cream } });
  titleLines.push({ text: prepared, options: { color: C.muted } });
  s.addText(titleLines, { x: 0.9, y: 4.3, w: 11.5, h: 1.6, fontFace: BF,
    fontSize: 15, lineSpacing: 26, margin: 0 });
  next();

  // 2 — 60-SECOND VIEW (hero stat cards) --------------------------------- //
  s = p.addSlide();
  lightBase(s, "The 60-second view", deck.sixty_second_title || "Portfolio at a glance");
  const slots = (fj.hero && fj.hero.slots) || {};
  const cards = Object.keys(slots).map((label) => {
    const slot = slots[label] || {};
    return [heroVal(label, slot.value), slot.sub || label];
  });
  cards.forEach((d, i) => {
    const cx = 0.7 + (i % 3) * 4.05, cy = 1.95 + Math.floor(i / 3) * 2.35;
    s.addShape(p.shapes.RECTANGLE, { x: cx, y: cy, w: 3.8, h: 2.05, fill: { color: C.cream },
      line: { color: C.line, width: 1 }, shadow: sh() });
    s.addShape(p.shapes.RECTANGLE, { x: cx, y: cy, w: 0.09, h: 2.05, fill: { color: C.orange } });
    s.addText(String(d[0]), { x: cx + 0.3, y: cy + 0.35, w: 3.3, h: 0.95, fontFace: HF,
      fontSize: 38, bold: true, color: C.ink, margin: 0 });
    s.addText(String(d[1]), { x: cx + 0.3, y: cy + 1.32, w: 3.3, h: 0.6, fontFace: BF,
      fontSize: 12, color: C.muted, margin: 0 });
  });
  if (fj.hero && fj.hero.na_footnote) {
    s.addText("* " + fj.hero.na_footnote, { x: 0.7, y: H - 0.78, w: 11, h: 0.3,
      fontFace: BF, fontSize: 9, italic: true, color: C.muted, margin: 0 });
  }
  footer(s, next());

  // 3 — BRAND HEALTH RADAR ----------------------------------------------- //
  const radarPng = chart("radar_7dim.png");
  s = p.addSlide();
  lightBase(s, "Brand health",
    deck.radar_title || (isPresent(fj.radar_overall) ? `${fj.radar_overall} / 10` : "Brand Health Radar"));
  if (radarPng) {
    s.addImage(imgBox(radarPng, 1.11, 0.7, 1.75, 6.0, 5.0));
  } else {
    s.addText("Radar chart pending — see full PDF report.", { x: 0.9, y: 3.4, w: 5.6,
      h: 0.6, fontFace: BF, fontSize: 14, italic: true, color: C.muted, margin: 0 });
  }
  const weak = fj.radar_weakest || [];
  if (weak.length) {
    s.addText("Weakest axes", { x: 7.1, y: 1.95, w: 5.4, h: 0.35, fontFace: HF,
      fontSize: 14, bold: true, color: C.red, margin: 0 });
    s.addText(weak.map((w2) => `${w2[0]} ${w2[1] && w2[1].current}`).join("   ·   "),
      { x: 7.1, y: 2.3, w: 5.4, h: 0.5, fontFace: BF, fontSize: 15, color: C.ink, margin: 0 });
  }
  const rnotes = (fj.radar_notes || []).map((n) =>
    ({ text: String(n).replace(/<[^>]+>/g, ""), options: { bullet: true, breakLine: true } }));
  if (rnotes.length) {
    s.addShape(p.shapes.RECTANGLE, { x: 7.1, y: 3.0, w: 5.5, h: 3.1, fill: { color: C.cream },
      line: { color: C.line, width: 1 } });
    s.addText(rnotes, { x: 7.35, y: 3.25, w: 5.0, h: 2.6, fontFace: BF, fontSize: 13,
      color: C.ink, paraSpaceAfter: 8, margin: 0 });
  }
  footer(s, next());

  // 4 — FOUNDATION GATE (only if triggered) ------------------------------ //
  const gate = fj.foundation_gate || {};
  if (gate.triggered) {
    s = p.addSlide();
    s.background = { color: C.white };
    s.addShape(p.shapes.RECTANGLE, { x: 0, y: 0, w: 0.18, h: H, fill: { color: C.red } });
    s.addText("FOUNDATION GATE", { x: 0.7, y: 0.42, w: 9, h: 0.3, fontFace: HF,
      fontSize: 12, bold: true, color: C.red, charSpacing: 3, margin: 0 });
    s.addText(deck.foundation_gate_title || "Foundation gate triggered", { x: 0.7, y: 0.72,
      w: 12, h: 0.85, fontFace: HF, fontSize: 32, bold: true, color: C.ink, margin: 0 });
    const rows = deck.foundation_gate_rows || gate.rows || [];
    rows.forEach((d, i) => {
      const cy = 1.95 + i * 1.05;
      s.addShape(p.shapes.RECTANGLE, { x: 0.7, y: cy, w: 11.9, h: 0.9, fill: { color: C.redBg },
        line: { color: C.line, width: 1 } });
      s.addText(String(d.label || d[0] || ""), { x: 0.95, y: cy + 0.2, w: 2.6, h: 0.5,
        fontFace: HF, fontSize: 17, bold: true, color: C.red, margin: 0 });
      s.addText(String(d.detail || d[1] || ""), { x: 3.7, y: cy + 0.2, w: 8.6, h: 0.5,
        fontFace: BF, fontSize: 15, color: C.ink, margin: 0 });
    });
    if (gate.rule || deck.foundation_gate_rule) {
      s.addText(String(gate.rule || deck.foundation_gate_rule), { x: 0.7, y: 5.6, w: 11.9,
        h: 0.7, fontFace: HF, fontSize: 15, bold: true, color: C.ink, margin: 0 });
    }
    footer(s, next());
  }

  // 5 — HEADLINE FINDING (optional) -------------------------------------- //
  const hl = deck.headline_finding;
  if (hl) {
    s = p.addSlide();
    lightBase(s, "Headline finding", hl.title || "Headline finding");
    if (isPresent(hl.stat)) {
      s.addText(String(hl.stat), { x: 0.7, y: 1.8, w: 3.4, h: 1.0, fontFace: HF,
        fontSize: 44, bold: true, color: C.orange, margin: 0 });
      if (hl.stat_sub) s.addText(String(hl.stat_sub), { x: 0.7, y: 2.78, w: 3.4, h: 0.6,
        fontFace: BF, fontSize: 12, color: C.muted, margin: 0 });
    }
    const bullets = (hl.bullets || []).map((b, j, a) =>
      ({ text: String(b), options: { bullet: true, breakLine: j < a.length - 1 } }));
    if (bullets.length) {
      s.addText(bullets, { x: 0.7, y: 3.45, w: 5.6, h: 2.6, fontFace: BF, fontSize: 14,
        color: C.ink, paraSpaceAfter: 10, margin: 0 });
    }
    const fnPng = chart("funnel_ue.png");
    if (fnPng) s.addImage(imgBox(fnPng, 2.5, 6.6, 1.95, 6.2, 3.9));
    footer(s, next());
  }

  // 6 — FOOTHOLD / RISK / OPPORTUNITY ------------------------------------ //
  const fro = fj.fro || {};
  const froSpec = [
    ["foothold", C.green, "Foothold"],
    ["risk", C.red, "Risk"],
    ["opportunity", C.orange, "Opportunity"],
  ].filter(([k]) => fro[k]);
  if (froSpec.length) {
    s = p.addSlide();
    lightBase(s, "Where we stand", "Foothold · Risk · Opportunity");
    froSpec.forEach(([k, col, tag], i) => {
      const c = fro[k];
      const cx = 0.7 + i * 4.05;
      s.addShape(p.shapes.RECTANGLE, { x: cx, y: 2.0, w: 3.8, h: 3.9, fill: { color: C.cream },
        line: { color: C.line, width: 1 }, shadow: sh() });
      s.addShape(p.shapes.RECTANGLE, { x: cx, y: 2.0, w: 3.8, h: 0.12, fill: { color: col } });
      s.addText(tag, { x: cx + 0.3, y: 2.4, w: 3.2, h: 0.55, fontFace: HF, fontSize: 22,
        bold: true, color: col, margin: 0 });
      const body = String(c.body || "").replace(/<[^>]+>/g, "");
      const fig = c.fig ? `\n\n${String(c.fig).replace(/<[^>]+>/g, "")}` : "";
      s.addText(body + fig, { x: cx + 0.3, y: 3.05, w: 3.2, h: 2.7, fontFace: BF,
        fontSize: 14, color: C.ink, margin: 0 });
    });
    footer(s, next());
  }

  // 7 — TIERS & ECONOMICS ------------------------------------------------ //
  const gmvPng = chart("top15_green_bar.png");
  const psnap = fj.portfolio_snapshot || {};
  const prows = psnap.rows || [];
  if (gmvPng || prows.length) {
    s = p.addSlide();
    lightBase(s, "Locations & economics", "Baseline tiers and platform economics");
    if (gmvPng) s.addImage(imgBox(gmvPng, 1.96, 0.7, 1.85, 6.3, 4.4));
    if (prows.length) {
      const head = ["Platform", "Gross", "Eff. comm."].map((t) =>
        ({ text: t, options: { bold: true, color: C.white, fill: { color: C.ink } } }));
      const tbl = [head];
      prows.forEach((r) => {
        tbl.push([
          String(r.platform || ""),
          typeof r.gross === "number" ? fmtMoney(r.gross) : (r.gross == null ? "n/a*" : String(r.gross)),
          isPresent(r.eff_commission) ? String(r.eff_commission) : "n/a*",
        ]);
      });
      s.addTable(tbl, { x: 7.2, y: 2.0, w: 5.4, colW: [2.2, 1.7, 1.5], fontFace: BF,
        fontSize: 12.5, color: C.ink, border: { pt: 0.5, color: C.line }, rowH: 0.42,
        valign: "middle" });
    }
    if (psnap.narrative) {
      s.addText(String(psnap.narrative).replace(/<[^>]+>/g, ""), { x: 7.2,
        y: 2.2 + 0.42 * (prows.length + 1) + 0.2, w: 5.4, h: 1.4, fontFace: BF,
        fontSize: 12.5, italic: true, color: C.muted, margin: 0 });
    }
    footer(s, next());
  }

  // 8 — WHEN CUSTOMERS ORDER (trend + daypart) --------------------------- //
  const trendPng = chart("trend_overlay.png");
  const daypartPng = chart("daypart_heatmap.png");
  if (trendPng || daypartPng) {
    s = p.addSlide();
    lightBase(s, "When customers order", "Real per-order trend and daypart");
    if (trendPng && daypartPng) {
      s.addImage(imgBox(trendPng, 2.08, 0.7, 1.75, 6.1, 2.45));
      s.addImage(imgBox(daypartPng, 2.48, 0.7, 4.35, 6.1, 2.45));
    } else if (trendPng) {
      s.addImage(imgBox(trendPng, 2.08, 0.7, 2.0, 6.1, 4.9));
    } else {
      s.addImage(imgBox(daypartPng, 2.48, 0.7, 2.0, 6.1, 4.9));
    }
    const dp = mj.daypart || {};
    const pk = dp.peak || {};
    s.addShape(p.shapes.RECTANGLE, { x: 7.1, y: 1.9, w: 5.5, h: 4.3, fill: { color: C.cream },
      line: { color: C.line, width: 1 } });
    if (isPresent(pk.day)) {
      s.addText("Peak demand", { x: 7.35, y: 2.15, w: 5.0, h: 0.4, fontFace: HF,
        fontSize: 14, bold: true, color: C.orange, margin: 0 });
      s.addText(`${pk.day} ${pk.hour}:00`, { x: 7.35, y: 2.5, w: 5.0, h: 0.7,
        fontFace: HF, fontSize: 28, bold: true, color: C.ink, margin: 0 });
    }
    const tnotes = [];
    if (dp.weakest_day) tnotes.push({ text: `Weakest day: ${dp.weakest_day}.`, options: { bullet: true, breakLine: true } });
    const tcap = fj.trend_caption || (mj.trend_weekly && (mj.trend_weekly.caption || mj.trend_weekly.source));
    if (tcap) tnotes.push({ text: String(tcap), options: { bullet: true, breakLine: true } });
    (deck.daypart_bullets || []).forEach((b, j, a) =>
      tnotes.push({ text: String(b), options: { bullet: true, breakLine: j < a.length - 1 } }));
    if (tnotes.length) {
      s.addText(tnotes, { x: 7.35, y: 3.35, w: 5.0, h: 2.7, fontFace: BF, fontSize: 13,
        color: C.ink, paraSpaceAfter: 8, margin: 0 });
    }
    footer(s, next());
  }

  // 9 — ACTION PLAN ------------------------------------------------------ //
  const lanes = deck.action_lanes;
  if (lanes && lanes.length) {
    s = p.addSlide();
    lightBase(s, "Action plan", "Prioritized — with owners");
    const laneColors = [C.red, C.orange, C.ink];
    lanes.slice(0, 3).forEach((d, i) => {
      const cx = 0.7 + i * 4.05;
      const col = laneColors[i] || C.ink;
      s.addShape(p.shapes.RECTANGLE, { x: cx, y: 2.0, w: 3.8, h: 0.62, fill: { color: col } });
      s.addText(String(d.lane || d.when || ""), { x: cx, y: 2.0, w: 3.8, h: 0.62,
        fontFace: HF, fontSize: 17, bold: true, color: C.white, align: "center",
        valign: "middle", margin: 0 });
      s.addShape(p.shapes.RECTANGLE, { x: cx, y: 2.62, w: 3.8, h: 3.35, fill: { color: C.cream },
        line: { color: C.line, width: 1 } });
      const items = (d.items || []).map((t, j, a) =>
        ({ text: String(t), options: { bullet: true, breakLine: j < a.length - 1 } }));
      s.addText(items, { x: cx + 0.28, y: 2.85, w: 3.25, h: 2.95, fontFace: BF,
        fontSize: 13, color: C.ink, paraSpaceAfter: 10, margin: 0 });
    });
    footer(s, next());
  } else {
    // fall back to the report's this_week action_plan list
    const ap = fj.action_plan || {};
    if ((ap.this_week || []).length) {
      s = p.addSlide();
      lightBase(s, "Action plan", clean(ap.this_week_lane) || "This week");
      const items = ap.this_week.map((it, j, a) => ([
        { text: String(it.title || ""), options: { bullet: true, bold: true, breakLine: false } },
        { text: it.meta ? `  —  ${String(it.meta).replace(/<[^>]+>/g, "")}` : "",
          options: { breakLine: j < a.length - 1 } },
      ])).flat();
      s.addText(items, { x: 0.7, y: 2.0, w: 11.9, h: 4.0, fontFace: BF, fontSize: 15,
        color: C.ink, paraSpaceAfter: 12, margin: 0 });
      footer(s, next());
    }
  }

  // 10 — WHAT WE NEED (dark closing) ------------------------------------- //
  const closing = fj.deck && fj.deck.closing;
  s = p.addSlide();
  s.background = { color: C.ink };
  s.addShape(p.shapes.RECTANGLE, { x: 0, y: 0, w: 0.28, h: H, fill: { color: C.orange } });
  if (hasBadge) s.addImage({ path: LOGO_BADGE, x: 11.5, y: 0.7, w: 1.15, h: 1.15 });
  s.addText(((closing && closing.kicker) || "What we need from you").toUpperCase(),
    { x: 0.9, y: 1.05, w: 11, h: 0.4, fontFace: HF, fontSize: 14, bold: true,
      color: C.orange, charSpacing: 3, margin: 0 });
  s.addText((closing && closing.title) || "To move fast", { x: 0.85, y: 1.5, w: 11.5,
    h: 0.95, fontFace: HF, fontSize: 40, bold: true, color: C.white, margin: 0 });
  const asks = ((closing && closing.bullets) || []).map((b, j, a) =>
    ({ text: String(b), options: { bullet: true, breakLine: j < a.length - 1 } }));
  if (asks.length) {
    s.addText(asks, { x: 0.9, y: 2.75, w: 11.5, h: 2.8, fontFace: BF, fontSize: 18,
      color: C.cream, paraSpaceAfter: 14, margin: 0 });
  }
  s.addText(prepared, { x: 0.9, y: 6.4, w: 11.5, h: 0.4, fontFace: BF, fontSize: 12,
    color: C.muted, margin: 0 });
  next();

  // ---------------------------------------------------------------------- //
  const slug = (fj.client_slug ||
    String(client).toLowerCase().replace(/['’]/g, "").replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")) || "client";
  const outPath = path.join(runDir, `${slug}-deck.pptx`);
  return p.writeFile({ fileName: outPath }).then(() => {
    console.log(`${path.basename(outPath)} written: ${slideNo} slides ` +
      `(run dir: ${runDir})`);
    return outPath;
  });
}

if (require.main === module) {
  main(process.argv).catch((e) => {
    console.error("build_deck failed:", e.message);
    process.exit(1);
  });
}

module.exports = { main, parseTokens, hex6 };
