"""
Product Kit — a lightweight growth tool for SMB sellers.
Built as a v1 proof-of-concept for the Photoroom Senior Growth Marketing application.

Flow:
  1. Seller uploads a product photo and enters product name + category.
  2. Background is removed locally with rembg (free, no API).
  3. Groq's free LLM generates marketplace-specific copy, a Photoroom edit
     recipe, and a FOMO/JOMO caption pair grounded in behavioural science.
"""

import io
import os
import time
import json
import concurrent.futures
import urllib.request
from PIL import Image
import streamlit as st

# ---------- Page setup ----------
st.set_page_config(
    page_title="Product Kit — for SMB sellers",
    page_icon="🛍️",
    layout="wide",
)

st.title("Product Kit")
st.caption(
    "Turn a product photo into a marketplace-ready kit. "
    "Background stripped, copy generated, edit recipe handed off to Photoroom."
)

with st.expander("What this is (and what it isn't)"):
    st.markdown(
        """
        **v1 proof-of-concept**, built in an afternoon to test one hypothesis:
        SMB sellers need raw marketing materials fast, not finished graphics.

        This tool produces the **raw materials** — clean cutout, platform-specific
        copy, and a hand-off recipe telling the seller exactly what to do next
        inside Photoroom. It does not compete with Photoroom; it feeds it.

        **Roadmap (v2):** programmatic category landing pages, product-URL
        scraping, live A/B tests on caption variants, referral loop back to
        Photoroom sign-up.
        """
    )

# ---------- Sidebar: API key ----------
st.sidebar.header("Setup")
groq_key = st.sidebar.text_input(
    "Groq API key",
    type="password",
    help="Free key from console.groq.com. Not stored anywhere.",
    value=os.getenv("GROQ_API_KEY", ""),
)
st.sidebar.markdown(
    "[Get a free Groq key →](https://console.groq.com/keys)"
)

# ---------- Inputs ----------
col_input_left, col_input_right = st.columns([1, 1])

with col_input_left:
    st.subheader("1. Upload the product photo")
    uploaded = st.file_uploader(
        "PNG or JPG, ideally on a plain background",
        type=["png", "jpg", "jpeg"],
    )

with col_input_right:
    st.subheader("2. Tell us about the product")
    product_name = st.text_input(
        "Product name",
        placeholder="e.g. Handmade ceramic espresso cup",
    )
    product_category = st.selectbox(
        "Category",
        [
            "Home & kitchen",
            "Fashion & accessories",
            "Beauty & personal care",
            "Electronics & gadgets",
            "Handmade & craft",
            "Fitness & outdoors",
            "Pet supplies",
            "Baby & kids",
            "Other",
        ],
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
            "Behavioural framing. FOMO uses scarcity and urgency; "
            "JOMO uses calm and intentionality. Based on consumer-behaviour "
            "research on message type and purchase intent."
        ),
    )

run = st.button("Generate the kit", type="primary", use_container_width=True)


# ---------- Background removal ----------
def remove_background(image_bytes: bytes, timeout_seconds: int = 60) -> Image.Image | None:
    """Strip background with rembg but don't block longer than timeout_seconds.
    If rembg isn't available or it times out, return the original image."""
    img = Image.open(io.BytesIO(image_bytes))
    try:
        from rembg import remove
    except Exception as e:
        st.info(f"rembg not available: {e}. Using original image.")
        return img

    def worker(i_bytes: bytes):
        # This runs in a thread — keep it simple
        return remove(Image.open(io.BytesIO(i_bytes)))

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
        fut = ex.submit(worker, image_bytes)
        try:
            start = time.time()
            result = fut.result(timeout=timeout_seconds)
            elapsed = time.time() - start
            st.info(f"Background removed in {elapsed:.1f}s")
            return result
        except concurrent.futures.TimeoutError:
            st.warning(f"Background removal timed out after {timeout_seconds}s. Showing original image.")
            return img
        except Exception as e:
            st.info(f"Background removal skipped ({type(e).__name__}): {e}. Showing original image.")
            return img


# ---------- LLM prompt ----------
def build_prompt(name: str, category: str, marketplaces: list[str], psych: str) -> str:
    return f"""You are a senior growth marketer for SMB e-commerce sellers.

A seller has uploaded a product photo. Here are the details:

- Product name: {name}
- Category: {category}
- Target marketplaces: {", ".join(marketplaces) if marketplaces else "Amazon, Shopify"}
- Caption angle: {psych}

Return a single JSON object with these exact keys:

{{
  "marketplace_copy": {{
    "amazon": {{ "title": "...", "bullets": ["...", "...", "...", "...", "..."], "description": "..." }},
    "shopify": {{ "title": "...", "description": "..." }},
    "etsy": {{ "title": "...", "story": "..." }},
    "ebay": {{ "title": "...", "description": "..." }}
  }},
  "photoroom_recipe": {{
    "scene_1": "One-line edit recipe: background, lighting, crop, use-case",
    "scene_2": "One-line edit recipe: different context",
    "scene_3": "One-line edit recipe: different context"
  }},
  "captions": {{
    "fomo": "One social caption using scarcity and urgency. Under 40 words.",
    "jomo": "One social caption using calm, intentional framing. Under 40 words."
  }}
}}

Only include marketplace copy for the marketplaces the seller selected;
set the others to null. Amazon rewards keyword density in titles.
Etsy rewards story and craft. Shopify rewards brand voice.
eBay rewards clarity and specificity. Return valid JSON only, no prose."""


# ---------- Groq call ----------
def call_groq(prompt: str, api_key: str, timeout: int = 30) -> dict | None:
    payload = json.dumps({
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "response_format": {"type": "json_object"},
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
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            st.info(f"Groq raw response length: {len(raw)}")
            body = json.loads(raw)
            # Be resilient: content may already be parsed or may be a JSON string
            content = body["choices"][0]["message"].get("content")
            if isinstance(content, str):
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    st.error("Groq returned invalid JSON content.")
                    return None
            elif isinstance(content, dict):
                return content
            else:
                st.error("Unexpected Groq response format.")
                return None
    except Exception as e:
        st.error(f"Groq request failed: {e}")
        return None


# ---------- Render output ----------
def render_kit(image: Image.Image, kit: dict, marketplaces: list[str], psych: str):
    st.divider()
    st.header("Your product kit")

    left, right = st.columns([1, 1])

    with left:
        st.subheader("Clean cutout")
        st.image(image, use_container_width=True)
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        st.download_button(
            "Download cutout (PNG)",
            data=buf.getvalue(),
            file_name="product_cutout.png",
            mime="image/png",
        )

    with right:
        st.subheader("Photoroom edit recipe")
        st.caption(
            "Three scenes to build from this cutout inside Photoroom. "
            "Copy a recipe, paste it into Photoroom's AI backdrop, and ship."
        )
        recipe = kit.get("photoroom_recipe", {})
        for label, key in [("Scene 1", "scene_1"), ("Scene 2", "scene_2"), ("Scene 3", "scene_3")]:
            if recipe.get(key):
                st.markdown(f"**{label}.** {recipe[key]}")

    st.divider()
    st.subheader("Marketplace-optimised copy")
    st.caption("Each marketplace has a different SEO and buyer-psychology profile.")

    active_tabs = [m for m in marketplaces if kit.get("marketplace_copy", {}).get(m.lower())]
    if active_tabs:
        tabs = st.tabs(active_tabs)
        for tab, market in zip(tabs, active_tabs):
            data = kit["marketplace_copy"][market.lower()]
            with tab:
                if market == "Amazon":
                    st.markdown(f"**Title.** {data.get('title', '')}")
                    st.markdown("**Bullets.**")
                    for b in data.get("bullets", []):
                        st.markdown(f"- {b}")
                    st.markdown(f"**Description.** {data.get('description', '')}")
                elif market == "Etsy":
                    st.markdown(f"**Title.** {data.get('title', '')}")
                    st.markdown(f"**Story.** {data.get('story', '')}")
                else:
                    st.markdown(f"**Title.** {data.get('title', '')}")
                    st.markdown(f"**Description.** {data.get('description', '')}")

    st.divider()
    st.subheader("Caption pair — FOMO vs JOMO")
    st.caption(
        "A/B the same product with two behavioural framings. "
        "FOMO leans on scarcity; JOMO leans on intentionality. "
        "Grounded in consumer-behaviour research on message type and purchase intent."
    )
    caps = kit.get("captions", {})
    c1, c2 = st.columns(2)
    if psych in ("Compare both (FOMO vs JOMO)", "FOMO only"):
        with c1:
            st.markdown("**FOMO caption**")
            st.info(caps.get("fomo", ""))
    if psych in ("Compare both (FOMO vs JOMO)", "JOMO only"):
        with c2:
            st.markdown("**JOMO caption**")
            st.success(caps.get("jomo", ""))

    st.divider()
    st.markdown(
        "**Next step.** Take the cutout and a recipe into "
        "[Photoroom](https://www.photoroom.com) to finish the visual."
    )


# ---------- Main ----------
if run:
    if not uploaded:
        st.warning("Upload a product photo first.")
    elif not product_name:
        st.warning("Add the product name.")
    elif not groq_key:
        st.warning("Add your free Groq API key in the sidebar.")
    else:
        with st.spinner("Stripping background..."):
            clean_image = remove_background(uploaded.read())
        with st.spinner("Generating the kit..."):
            prompt = build_prompt(product_name, product_category, target_marketplace, psychology)
            kit = call_groq(prompt, groq_key)
        if kit and clean_image:
            render_kit(clean_image, kit, target_marketplace, psychology)

st.divider()
st.caption(
    "Built by Manoj Kumar Gunasekaran as a v1 proof-of-concept for the "
    "Photoroom Senior Growth Marketing application. "
    "Stack: Streamlit + rembg + Groq (Llama 3.3 70B). Zero paid APIs."
)
