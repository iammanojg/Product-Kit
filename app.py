"""
Product Kit — a lightweight growth tool for SMB sellers.
Built as a v1 proof-of-concept for the Photoroom Senior Growth Marketing application.
 
Flow:
  1. Seller uploads a product photo and enters product name + category.
  2. Groq analyses the image description and generates:
     - A visual diagnosis of the current photo
     - A styled art-direction brief (before → after)
     - Marketplace-specific copy for selected platforms
     - FOMO vs JOMO caption pair grounded in behavioural science
"""
 
import io
import os
import json
import base64
import urllib.request
from PIL import Image
import streamlit as st
 
# ---------- Page config ----------
st.set_page_config(
    page_title="Product Kit — for SMB sellers",
    page_icon="🛍️",
    layout="wide",
)
 
# ---------- Custom CSS ----------
st.markdown("""
<style>
.diagnosis-box {
    background: #1a1a2e;
    border-left: 4px solid #e74c3c;
    border-radius: 6px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.brief-box {
    background: #0f3460;
    border-left: 4px solid #00d4aa;
    border-radius: 6px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.scene-card {
    background: #16213e;
    border: 1px solid #00d4aa33;
    border-radius: 8px;
    padding: 14px 18px;
    margin-bottom: 10px;
}
.scene-number {
    color: #00d4aa;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    margin-bottom: 4px;
}
.scene-text {
    color: #e8e8e8;
    font-size: 15px;
    line-height: 1.5;
}
.label-pill {
    display: inline-block;
    background: #e74c3c22;
    color: #e74c3c;
    border: 1px solid #e74c3c44;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.label-pill-green {
    display: inline-block;
    background: #00d4aa22;
    color: #00d4aa;
    border: 1px solid #00d4aa44;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.fomo-box {
    background: #2d1b1b;
    border: 1px solid #e74c3c55;
    border-radius: 8px;
    padding: 16px;
    color: #f0a0a0;
    font-size: 15px;
    line-height: 1.6;
}
.jomo-box {
    background: #1b2d2b;
    border: 1px solid #00d4aa55;
    border-radius: 8px;
    padding: 16px;
    color: #a0f0e0;
    font-size: 15px;
    line-height: 1.6;
}
</style>
""", unsafe_allow_html=True)
 
# ---------- Header ----------
st.title("Product Kit")
st.caption(
    "Upload a product photo → get a visual diagnosis, a Photoroom art-direction brief, "
    "marketplace copy, and a FOMO/JOMO caption pair. Built for SMB sellers."
)
 
with st.expander("What this is (and what it isn't)"):
    st.markdown("""
**v1 proof-of-concept.** Built to test one hypothesis: SMB sellers don't need another image editor —
they need a creative director who tells them exactly what to fix and how.
 
This tool produces:
- A **visual diagnosis** of what's holding back the current photo
- A **Photoroom art-direction brief** — three scenes, ready to paste into Photoroom's AI backdrop
- **Platform-specific copy** tuned for Amazon, Shopify, Etsy, or eBay
- A **FOMO vs JOMO caption pair** — two behavioural framings, A/B ready
 
It doesn't compete with Photoroom. It tells the seller what to do *inside* Photoroom.
 
**Roadmap (v2):** Background removal, programmatic SEO pages by product category,
product-URL scraping, live caption A/B tracking, direct Photoroom CTA integration.
    """)
 
# ---------- API key ----------
groq_key = os.getenv("GROQ_API_KEY", "")
if not groq_key:
    st.sidebar.header("Setup")
    groq_key = st.sidebar.text_input(
        "Groq API key",
        type="password",
        help="Free key from console.groq.com — no card required.",
    )
    st.sidebar.markdown("[Get a free Groq key →](https://console.groq.com/keys)")
else:
    st.sidebar.success("✓ API key loaded")
 
# ---------- Inputs ----------
col_left, col_right = st.columns([1, 1])
 
with col_left:
    st.subheader("1. Upload the product photo")
    uploaded = st.file_uploader("PNG or JPG", type=["png", "jpg", "jpeg"])
    if uploaded:
        img = Image.open(uploaded)
        st.image(img, use_container_width=True)
        st.caption("← This is what we're diagnosing")
 
with col_right:
    st.subheader("2. Tell us about the product")
    product_name = st.text_input(
        "Product name",
        placeholder="e.g. Handmade ceramic espresso cup",
    )
    product_category = st.selectbox(
        "Category",
        ["Home & kitchen", "Fashion & accessories", "Beauty & personal care",
         "Electronics & gadgets", "Handmade & craft", "Fitness & outdoors",
         "Pet supplies", "Baby & kids", "Other"],
    )
    target_marketplace = st.multiselect(
        "Where will you sell it?",
        ["Amazon", "Shopify", "Etsy", "eBay"],
        default=["Amazon", "Shopify"],
    )
    psychology = st.radio(
        "Caption angle",
        ["Compare both (FOMO vs JOMO)", "FOMO only", "JOMO only"],
        help=(
            "FOMO: scarcity and urgency. JOMO: calm intentionality. "
            "Based on consumer-behaviour research on message type and purchase intent."
        ),
    )
 
run = st.button("Generate the kit", type="primary", use_container_width=True)
 
 
# ---------- Encode image for LLM ----------
def encode_image(image: Image.Image) -> str:
    """Resize and base64-encode image for Groq vision."""
    img = image.copy()
    img.thumbnail((800, 800))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode("utf-8")
 
 
# ---------- Build prompt ----------
def build_prompt(name: str, category: str, marketplaces: list, psych: str) -> str:
    mkt = ", ".join(marketplaces) if marketplaces else "Amazon, Shopify"
    return f"""You are a senior e-commerce visual strategist and growth marketer.
 
A seller has uploaded a product photo. Their product details:
- Name: {name}
- Category: {category}
- Target marketplaces: {mkt}
- Caption angle requested: {psych}
 
Look at the image carefully. Then return a single JSON object with these exact keys:
 
{{
  "diagnosis": {{
    "score": "A number from 1-10 rating the current photo for marketplace conversion",
    "issues": ["Issue 1 in one sharp sentence", "Issue 2", "Issue 3"],
    "what_is_working": "One sentence on what the photo does well, if anything"
  }},
  "photoroom_brief": {{
    "scene_1": {{
      "label": "Studio clean",
      "instruction": "Specific one-line Photoroom edit instruction: background, lighting, shadow, crop ratio",
      "why": "One sentence on why this scene converts on the target marketplace"
    }},
    "scene_2": {{
      "label": "Lifestyle context",
      "instruction": "Specific one-line instruction for a lifestyle scene relevant to this product",
      "why": "One sentence on the buyer psychology this scene targets"
    }},
    "scene_3": {{
      "label": "Detail or texture",
      "instruction": "Specific one-line instruction for a close-up or detail shot",
      "why": "One sentence on why detail shots reduce return rates for this category"
    }}
  }},
  "marketplace_copy": {{
    "amazon": {{ "title": "Keyword-dense title under 200 chars", "bullets": ["Benefit bullet 1", "Benefit bullet 2", "Benefit bullet 3", "Benefit bullet 4", "Benefit bullet 5"], "description": "2-3 sentence Amazon description" }},
    "shopify": {{ "title": "Brand-voice title", "description": "2-3 sentence Shopify description with lifestyle angle" }},
    "etsy": {{ "title": "Story-driven title", "story": "2-3 sentence Etsy description with craft and maker angle" }},
    "ebay": {{ "title": "Clear specific title", "description": "2-3 sentence eBay description with condition and specs" }}
  }},
  "captions": {{
    "fomo": "Social caption using scarcity or urgency. Under 35 words. No hashtags.",
    "jomo": "Social caption using calm intentional framing. Under 35 words. No hashtags."
  }}
}}
 
Rules:
- Only include marketplace_copy for the selected marketplaces ({mkt}); set others to null.
- The diagnosis must be specific to what you actually see in the image — not generic.
- The Photoroom brief instructions must be specific enough to paste directly into Photoroom.
- Return valid JSON only. No prose, no markdown fences, no preamble."""
 
 
# ---------- Groq call with vision ----------
def call_groq(prompt: str, api_key: str, image_b64: str) -> dict | None:
    payload = json.dumps({
        "model": "openai/gpt-oss-120b",
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }],
        "temperature": 0.6,
        "response_format": {"type": "json_object"},
        "max_tokens": 2000,
    }).encode("utf-8")
 
    req = urllib.request.Request(
        "https://api.groq.com/openai/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            content = body["choices"][0]["message"].get("content")
            if isinstance(content, str):
                # Strip accidental markdown fences
                clean = content.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
                return json.loads(clean)
            elif isinstance(content, dict):
                return content
            else:
                st.error("Unexpected response format from Groq.")
                return None
    except json.JSONDecodeError as e:
        st.error(f"JSON parse error: {e}")
        return None
    except Exception as e:
        st.error(f"Generation failed: {e}")
        return None
 
 
# ---------- Render ----------
def render_kit(image: Image.Image, kit: dict, marketplaces: list, psych: str):
    st.divider()
 
    # ── Before → After layout ──────────────────────────────────────
    st.header("Visual diagnosis + Photoroom brief")
    st.caption("What's holding your photo back — and exactly what to do about it inside Photoroom.")
 
    col_before, col_after = st.columns([1, 1])
 
    with col_before:
        st.markdown('<div class="label-pill">BEFORE — Current photo</div>', unsafe_allow_html=True)
        st.image(image, use_container_width=True)
 
        diag = kit.get("diagnosis", {})
        score = diag.get("score", "–")
        st.markdown(f"**Conversion score: {score}/10**")
 
        issues = diag.get("issues", [])
        if issues:
            st.markdown("**What to fix:**")
            for issue in issues:
                st.markdown(f"- {issue}")
 
        working = diag.get("what_is_working", "")
        if working:
            st.markdown(f"**What's working:** {working}")
 
    with col_after:
        st.markdown('<div class="label-pill-green">AFTER — Photoroom brief</div>', unsafe_allow_html=True)
        st.caption("Paste any of these directly into Photoroom's AI backdrop.")
 
        brief = kit.get("photoroom_brief", {})
        for key in ["scene_1", "scene_2", "scene_3"]:
            scene = brief.get(key, {})
            if scene:
                label = scene.get("label", "")
                instruction = scene.get("instruction", "")
                why = scene.get("why", "")
                st.markdown(f"""
<div class="scene-card">
  <div class="scene-number">{label}</div>
  <div class="scene-text">{instruction}</div>
  <div style="color:#888;font-size:13px;margin-top:6px;">{why}</div>
</div>
""", unsafe_allow_html=True)
 
    # ── Marketplace copy ───────────────────────────────────────────
    st.divider()
    st.subheader("Marketplace-optimised copy")
    st.caption("Each platform rewards a different SEO logic and buyer psychology.")
 
    active = [m for m in marketplaces if kit.get("marketplace_copy", {}).get(m.lower())]
    if active:
        tabs = st.tabs(active)
        for tab, market in zip(tabs, active):
            data = kit["marketplace_copy"][market.lower()]
            if not data:
                continue
            with tab:
                if market == "Amazon":
                    st.markdown(f"**Title.**  \n{data.get('title', '')}")
                    st.markdown("**Bullets.**")
                    for b in data.get("bullets", []):
                        st.markdown(f"- {b}")
                    st.markdown(f"**Description.**  \n{data.get('description', '')}")
                elif market == "Etsy":
                    st.markdown(f"**Title.**  \n{data.get('title', '')}")
                    st.markdown(f"**Story.**  \n{data.get('story', '')}")
                else:
                    st.markdown(f"**Title.**  \n{data.get('title', '')}")
                    st.markdown(f"**Description.**  \n{data.get('description', '')}")
 
    # ── FOMO vs JOMO ──────────────────────────────────────────────
    st.divider()
    st.subheader("Caption pair — FOMO vs JOMO")
    st.caption(
        "Two behavioural framings of the same product. "
        "A/B them. Keep whichever converts. "
        "Grounded in consumer-behaviour research on message type and purchase intent."
    )
 
    caps = kit.get("captions", {})
    c1, c2 = st.columns(2)
 
    if psych in ("Compare both (FOMO vs JOMO)", "FOMO only"):
        with c1:
            st.markdown("**FOMO**")
            st.markdown(
                f'<div class="fomo-box">{caps.get("fomo", "")}</div>',
                unsafe_allow_html=True
            )
 
    if psych in ("Compare both (FOMO vs JOMO)", "JOMO only"):
        with c2:
            st.markdown("**JOMO**")
            st.markdown(
                f'<div class="jomo-box">{caps.get("jomo", "")}</div>',
                unsafe_allow_html=True
            )
 
    st.divider()
    st.markdown(
        "**Next step.** Copy a scene brief above → open "
        "[Photoroom](https://www.photoroom.com) → paste into AI backdrop → done."
    )
 
 
# ---------- Main ----------
if run:
    if not uploaded:
        st.warning("Upload a product photo first.")
    elif not product_name:
        st.warning("Add the product name.")
    elif not groq_key:
        st.warning("Add your Groq API key in the sidebar.")
    else:
        image = Image.open(uploaded)
        with st.spinner("Analysing photo and generating kit..."):
            image_b64 = encode_image(image)
            prompt = build_prompt(product_name, product_category, target_marketplace, psychology)
            kit = call_groq(prompt, groq_key, image_b64)
        if kit:
            render_kit(image, kit, target_marketplace, psychology)
 
st.divider()
st.caption(
    "Built by Manoj Kumar Gunasekaran · Photoroom Senior Growth Marketing application · "
    "Stack: Streamlit + Groq vision (Llama 4 Scout) · Zero paid APIs."
)
