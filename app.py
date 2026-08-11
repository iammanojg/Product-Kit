import os
import json
from PIL import Image
import streamlit as st

# Import helpers from your modular parts
from utils import encode_image
from prompts import build_prompt

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
st.caption("Upload a product photo → get a visual diagnosis, a Photoroom art-direction brief, marketplace copy, and captions.")
 
# ---------- API key resolution ----------
groq_key = st.secrets.get("GROQ_API_KEY", os.getenv("GROQ_API_KEY", ""))

if not groq_key:
    st.sidebar.header("Setup")
    groq_key = st.sidebar.text_input("Groq API key", type="password")
    st.sidebar.markdown("[Get a free Groq key →](https://groq.com)")
else:
    st.sidebar.success("✓ API key loaded")
 
# ---------- Inputs ----------
st.subheader("💡 Demo Presets")
preset_choice = st.radio(
    "Test with a quick sample profile if you don't have an image ready:",
    ["None — Upload my own photo", "Handmade Ceramic Cup", "Waffle Maker", "Air Fryer"],
    horizontal=True
)

# Setup conditional tracking placeholders based on preset selection
default_name = ""
default_category = "Home & kitchen"
preset_img_path = None

if preset_choice == "Handmade Ceramic Cup":
    default_name = "Handmade ceramic espresso cup"
    default_category = "Handmade & craft"
    preset_img_path = "assets/cup.jpg"
elif preset_choice == "Waffle Maker":
    default_name = "Classic Belgian Waffle Maker"
    default_category = "Home & kitchen"
    preset_img_path = "assets/waffle.jpg"
elif preset_choice == "Air Fryer":
    default_name = "Digital Smart Air Fryer XL"
    default_category = "Home & kitchen"
    preset_img_path = "assets/fryer.jpg"

col_left, col_right = st.columns(2)
 
with col_left:
    st.subheader("1. Product Photo")
    uploaded = st.file_uploader("PNG or JPG", type=["png", "jpg", "jpeg"])
    
    # Core Image Routing Logic: Prioritize uploaded file, fallback to preset choice
    img = None
    if uploaded:
        img = Image.open(uploaded)
        st.image(img, use_container_width=True)
        st.caption("← File uploaded successfully")
    elif preset_img_path and os.path.exists(preset_img_path):
        img = Image.open(preset_img_path)
        st.image(img, use_container_width=True)
        st.caption(f"← Loaded preset image from: {preset_img_path}")
 
with col_right:
    st.subheader("2. Product Metadata")
    product_name = st.text_input(
        "Product name",
        value=default_name,  # Dynamically fills out text input using pre-set choices
        placeholder="e.g. Handmade ceramic espresso cup",
    )
    
    category_list = ["Home & kitchen", "Fashion & accessories", "Beauty & personal care", "Electronics & gadgets", "Handmade & craft", "Other"]
    # Safely compute the index position matching your targeted fallback category
    default_cat_index = category_list.index(default_category) if default_category in category_list else 0
    
    product_category = st.selectbox(
        "Category",
        options=category_list,
        index=default_cat_index  # Auto-selects targeted category element dynamically
    )
    
    target_marketplace = st.multiselect(
        "Where will you sell it?",
        ["Amazon", "Shopify", "Etsy", "eBay"],
        default=["Amazon", "Shopify"],
    )
    psychology = st.radio(
        "Caption angle",
        ["Compare both (FOMO vs JOMO)", "FOMO only", "JOMO only"],
    )
 
run = st.button("Generate the kit", type="primary", use_container_width=True)
 
# ---------- Inference Execution Loop ----------
if run:
    if not groq_key:
        st.error("Please add your Groq API key.")
    elif img is None:
        st.error("Please upload a product photo or select a demo preset.")
    elif not product_name.strip():
        st.error("Please provide a product name.")
    else:
        with st.spinner("Groq Vision is running visual strategy analysis..."):
            try:
                from groq import Groq
                
                client = Groq(api_key=groq_key)
                base64_img = encode_image(img)
                prompt_text = build_prompt(product_name, product_category, target_marketplace, psychology)
                
                response = client.chat.completions.create(
                    model="qwen/qwen3.6-27b",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt_text},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}}
                            ]
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                    max_tokens=4096
                )
                
                result = json.loads(response.choices[0].message.content)
                st.success("✨ Product Growth Kit Generated Successfully!")
                
                # 1. Diagnosis Rendering
                diag = result.get("diagnosis", {})
                st.subheader(f"Visual Score: {diag.get('score', 'N/A')}/10")
                issues_list = "".join([f"<li>{issue}</li>" for issue in diag.get("issues", [])])
                st.markdown(f'<div class="diagnosis-box"><strong>⚠️ Visual Fixes Needed:</strong><ul>{issues_list}</ul><p>💡 <strong>What works:</strong> {diag.get("what_is_working", "")}</p></div>', unsafe_allow_html=True)
                
                # 2. Photoroom Instructions Rendering
                st.subheader("📸 Photoroom Art Direction Brief")
                brief = result.get("photoroom_brief", {})
                for scene_key in ["scene_1", "scene_2", "scene_3"]:
                    scene = brief.get(scene_key, {})
                    if scene:
                        st.markdown(f"""
                        <div class="scene-card">
                            <div class="scene-number">{scene.get('label', 'Scene')}</div>
                            <div class="scene-text"><strong>Instruction:</strong> {scene.get('instruction', '')}</div>
                            <div style="font-size:13px; color:#aaa; margin-top:4px;"><em>Strategy: {scene.get('why', '')}</em></div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # 3. Dynamic Tabs Layout Rendering
                st.subheader("✍️ Marketplace Copywriting")
                copy_data = result.get("marketplace_copy", {})
                active_platforms = [m for m in ["Amazon", "Shopify", "Etsy", "eBay"] if m.lower() in copy_data and copy_data[m.lower()]]
                if active_platforms:
                    tabs = st.tabs(active_platforms)
                    for idx, platform_name in enumerate(active_platforms):
                        with tabs[idx]:
                            m_content = copy_data[platform_name.lower()]
                            st.markdown(f"### {m_content.get('title', '')}")
                            if "bullets" in m_content and m_content["bullets"]:
                                for b in m_content["bullets"]:
                                    st.markdown(f"- {b}")
                            if "description" in m_content:
                                st.write(m_content["description"])
                            if "story" in m_content:
                                st.write(m_content["story"])
                
                # 4. Behavioral Science Captions Rendering
                st.subheader("🧠 Behavioral Science Captions")
                caps = result.get("captions", {})
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**FOMO Angle (Scarcity)**")
                    fomo_text = caps.get('fomo', 'Not generated')
                    st.markdown(f'<div class="fomo-box">{fomo_text}</div>', unsafe_allow_html=True)
                with c2:
                    st.markdown("**JOMO Angle (Intentionality)**")
                    jomo_text = caps.get('jomo', 'Not generated')
                    st.markdown(f'<div class="jomo-box">{jomo_text}</div>', unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"Generation failed: {str(e)}")
