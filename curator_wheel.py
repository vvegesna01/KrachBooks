import json
import streamlit as st
import streamlit.components.v1 as components


# ── Colour palette (mirrors styles.css variables) ─────────────────────────────
_WHEEL_COLORS = [
    "#246A73", "#368F8B", "#1E1636",
    "#2d5f68", "#4aabaa", "#162b3a",
]

_WHEEL_HTML = """
<!DOCTYPE html>
<html>
<head>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,700;9..144,900&family=Inter:wght@400;600;700&display=swap');

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: transparent;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 24px 16px 32px;
    font-family: 'Inter', sans-serif;
  }}

  .wheel-wrap {{
    position: relative;
    width: 340px;
    height: 340px;
    margin-bottom: 20px;
  }}

  canvas {{ border-radius: 50%; filter: drop-shadow(0 12px 32px rgba(54,143,139,0.45)); cursor: pointer; }}

  .pointer {{
    position: absolute;
    top: 50%;
    right: -18px;
    transform: translateY(-50%);
    width: 0; height: 0;
    border-top: 18px solid transparent;
    border-bottom: 18px solid transparent;
    border-right: 36px solid #F3DFC1;
    filter: drop-shadow(-2px 0 6px rgba(243,223,193,0.5));
    z-index: 10;
  }}

  .centre-cap {{
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 48px; height: 48px;
    border-radius: 50%;
    background: #160F29;
    border: 3px solid #368F8B;
    z-index: 10;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
  }}

  .result-box {{
    display: none;
    background: rgba(36,106,115,0.18);
    border: 1px solid #368F8B;
    border-radius: 18px;
    padding: 10px 25px;
    text-align: center;
    animation: fadeIn 0.5s ease;
    max-width: 340px;
    width: 100%;
  }}

  .result-box.show {{ display: block; }}

  .result-title {{
    font-family: 'Fraunces', serif;
    font-size: 1rem;
    color: #DDBEA8;
    margin-bottom: 6px;
    letter-spacing: 0.04em;
  }}

  .result-name {{
    font-family: 'Fraunces', serif;
    font-size: 2rem;
    font-weight: 900;
    color: #F3DFC1;
  }}

  .result-emoji {{ font-size: 1.6rem; margin-top: 4px; }}

  @keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
  }}

  .placeholder-msg {{
    color: #DDBEA8;
    font-size: 0.92rem;
    margin-top: 8px;
    opacity: 0.7;
  }}
</style>
</head>
<body>

<div class="wheel-wrap">
  <canvas id="wheel" width="340" height="340"></canvas>
  <div class="pointer"></div>
  <div class="centre-cap">📚</div>
</div>

<div class="result-box" id="resultBox">
  <div class="result-title">🎉 Next Curator</div>
  <div class="result-name" id="resultName"></div>
</div>

<p class="placeholder-msg" id="placeholderMsg"></p>

<script>
  const NAMES        = {names_json};
  const COLORS       = {colors_json};
  const SPIN_TRIGGER = {spin_trigger};

  const canvas = document.getElementById("wheel");
  const ctx    = canvas.getContext("2d");
  const R      = canvas.width / 2;

  let currentAngle = 0;
  let spinning     = false;
  let lastTrigger  = 0;

  const arc = () => (2 * Math.PI) / NAMES.length;

  function drawWheel(rotation) {{
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const n = NAMES.length;
    const a = arc();

    for (let i = 0; i < n; i++) {{
      const start = rotation + i * a;
      const end   = start + a;

      ctx.beginPath();
      ctx.moveTo(R, R);
      ctx.arc(R, R, R - 2, start, end);
      ctx.closePath();
      ctx.fillStyle   = COLORS[i % COLORS.length];
      ctx.fill();
      ctx.strokeStyle = "rgba(243,223,193,0.15)";
      ctx.lineWidth   = 1.5;
      ctx.stroke();

      ctx.save();
      ctx.translate(R, R);
      ctx.rotate(start + a / 2);
      ctx.textAlign    = "right";
      ctx.textBaseline = "middle";
      ctx.fillStyle    = "#F3DFC1";
      ctx.font         = `bold ${{Math.min(15, Math.floor(260 / n))}}px Inter, sans-serif`;
      ctx.shadowColor  = "rgba(0,0,0,0.6)";
      ctx.shadowBlur   = 4;
      const label = NAMES[i].length > 10 ? NAMES[i].slice(0, 9) + "…" : NAMES[i];
      ctx.fillText(label, R - 14, 0);
      ctx.restore();
    }}

    ctx.beginPath();
    ctx.arc(R, R, R - 2, 0, 2 * Math.PI);
    ctx.strokeStyle = "#368F8B";
    ctx.lineWidth   = 3;
    ctx.stroke();
  }}

  function getWinner(finalAngle) {{
    const n    = NAMES.length;
    const norm = ((2 * Math.PI) - (finalAngle % (2 * Math.PI))) % (2 * Math.PI);
    return NAMES[Math.floor(norm / arc()) % n];
  }}

  function spinWheel() {{
    if (spinning || NAMES.length < 2) return;
    spinning = true;
    document.getElementById("resultBox").classList.remove("show");

    const totalDelta = (5 + Math.floor(Math.random() * 4)) * 2 * Math.PI + Math.random() * 2 * Math.PI;
    const duration   = 3500 + Math.random() * 1000;
    const startAngle = currentAngle;
    let   startTime  = null;

    const easeOut = t => 1 - Math.pow(1 - t, 3);

    function frame(ts) {{
      if (!startTime) startTime = ts;
      const progress = Math.min((ts - startTime) / duration, 1);
      currentAngle   = startAngle + totalDelta * easeOut(progress);
      drawWheel(currentAngle);

      if (progress < 1) {{
        requestAnimationFrame(frame);
      }} else {{
        spinning = false;
        document.getElementById("resultName").textContent = getWinner(currentAngle);
        document.getElementById("resultBox").classList.add("show");
      }}
    }}

    requestAnimationFrame(frame);
  }}

  if (NAMES.length >= 2) {{
    drawWheel(currentAngle);
    if (SPIN_TRIGGER > 0 && SPIN_TRIGGER !== lastTrigger) {{
      lastTrigger = SPIN_TRIGGER;
      setTimeout(spinWheel, 200);
    }}
    canvas.addEventListener("click", spinWheel);
  }} else {{
    document.getElementById("placeholderMsg").textContent =
      "Enter at least 2 names above to enable the wheel.";
  }}
</script>
</body>
</html>
"""


def render_curator_wheel() -> None:
    """Renders the curator picker wheel section (name inputs + canvas wheel)."""

    st.markdown(
        '<div class="section-title">'
        '<span class="material-icons">casino</span> Curator Picker</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="page-intro-sm">'
        "Add up to 5 names and spin the wheel to pick next month's curator!</p>",
        unsafe_allow_html=True,
    )

    # ── Name inputs ───────────────────────────────────────────────────────────
    if "wheel_names" not in st.session_state:
        st.session_state.wheel_names = [""] * 5

    for i, col in enumerate(st.columns(5)):
        with col:
            st.session_state.wheel_names[i] = st.text_input(
                f"Name {i + 1}",
                value=st.session_state.wheel_names[i],
                key=f"wheel_name_{i}",
                placeholder=f"Name {i + 1}",
            )

    active_names = [n.strip() for n in st.session_state.wheel_names if n.strip()]

    # ── Spin button ───────────────────────────────────────────────────────────
    if st.button("🎡 Spin the Wheel!", disabled=len(active_names) < 2):
        st.session_state["wheel_spin_trigger"] = (
            st.session_state.get("wheel_spin_trigger", 0) + 1
        )

    # ── Wheel canvas ──────────────────────────────────────────────────────────
    html = _WHEEL_HTML.format(
        names_json=json.dumps(active_names),
        colors_json=json.dumps(_WHEEL_COLORS),
        spin_trigger=st.session_state.get("wheel_spin_trigger", 0),
    )
    components.html(html, height=480, scrolling=False)