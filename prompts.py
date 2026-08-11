def build_prompt(name: str, category: str, marketplaces: list, psych: str) -> str:
    mkt = ", ".join(marketplaces) if marketplaces else "Amazon, Shopify"
    
    schema_instruction = """
Look at the image carefully. Then return a single JSON object with these exact keys:
{
  "diagnosis": {
    "score": "A number from 1-10 rating the current photo for marketplace conversion",
    "issues": ["Issue 1 in one sharp sentence", "Issue 2", "Issue 3"],
    "what_is_working": "One sentence on what the photo does well, if anything"
  },
  "photoroom_brief": {
    "scene_1": {
      "label": "Studio clean",
      "instruction": "Specific one-line Photoroom edit instruction: background, lighting, shadow, crop ratio",
      "why": "One sentence on why this scene converts on the target marketplace"
    },
    "scene_2": {
      "label": "Lifestyle context",
      "instruction": "Specific one-line instruction for a lifestyle scene relevant to this product",
      "why": "One sentence on the buyer psychology this scene targets"
    },
    "scene_3": {
      "label": "Detail or texture",
      "instruction": "Specific one-line instruction for a close-up or detail shot",
      "why": "One sentence on why detail shots reduce return rates for this category"
    }
  },
  "marketplace_copy": {
    "amazon": { "title": "Keyword-dense title under 200 chars", "bullets": ["Benefit 1", "Benefit 2", "Benefit 3", "Benefit 4", "Benefit 5"], "description": "2-3 sentence Amazon description" },
    "shopify": { "title": "Brand-voice title", "description": "2-3 sentence Shopify description with lifestyle angle" },
    "etsy": { "title": "Story-driven title", "story": "2-3 sentence Etsy description with craft and maker angle" },
    "ebay": { "title": "Clear specific title", "description": "2-3 sentence eBay description with condition and specs" }
  },
  "captions": {
    "fomo": "Social caption using scarcity or urgency. Under 35 words. No hashtags.",
    "jomo": "Social caption using calm intentional framing. Under 35 words. No hashtags."
  }
}
"""
    return f"You are a senior e-commerce visual strategist.\nProduct Name: {name}\nCategory: {category}\nMarketplaces: {mkt}\nAngle: {psych}\n\n{schema_instruction}\nRules:\n- Only generate entries inside marketplace_copy for: {mkt}. Set others to null.\n- Return only raw valid JSON."
