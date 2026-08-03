#!/usr/bin/env node
// gen-hero-mockup.mjs
// Generates an AI-improved hero image for a restaurant prospect via Replicate Seedream 4.5.
// Used as the visual wedge in cold outreach — paired with the prospect's current hero
// in a before/after comparison inside the audit report.
//
// Usage:
//   REPLICATE_API_TOKEN=... node gen-hero-mockup.mjs <brand-slug> <cuisine-type> [signature-dish]
//
// Examples:
//   node gen-hero-mockup.mjs joes-pizza "New York pizza" "wood-fired margherita"
//   node gen-hero-mockup.mjs sweetgreen-style "fast casual healthy bowls"
//
// Output:
//   ~/Desktop/spice-prospect-pipeline-data/hero-mockups/<brand-slug>-mockup.jpg
//   ~/Desktop/spice-prospect-pipeline-data/hero-mockups/<brand-slug>-mockup.json (metadata)

import fs from 'fs';
import path from 'path';

const TOKEN = process.env.REPLICATE_API_TOKEN;
if (!TOKEN) { console.error('Missing REPLICATE_API_TOKEN'); process.exit(1); }

const [, , brandSlug, cuisineType, signatureDish] = process.argv;
if (!brandSlug || !cuisineType) {
  console.error('Usage: node gen-hero-mockup.mjs <brand-slug> <cuisine-type> [signature-dish]');
  process.exit(1);
}

const HOME = process.env.HOME;
const OUT_DIR = process.env.OUTPUT_DIR || `${HOME}/Desktop/spice-prospect-pipeline-data/hero-mockups`;
fs.mkdirSync(OUT_DIR, { recursive: true });
const OUT_JPG = path.join(OUT_DIR, `${brandSlug}-mockup.jpg`);
const OUT_META = path.join(OUT_DIR, `${brandSlug}-mockup.json`);

if (fs.existsSync(OUT_JPG)) {
  console.log(`Mockup already exists: ${OUT_JPG}`);
  process.exit(0);
}

// Negative prompt — kill all text/logos/watermarks (we want a clean dish shot)
const NEG = 'text, words, letters, typography, logos, signs, watermarks, labels, captions, titles, writing, numbers, digits, fonts, alphabets, characters, inscriptions, banners, posters, signage, packaging, menu boards';

// Build the prompt — emphasis on what makes a great delivery hero
const subjectLine = signatureDish
  ? `signature ${signatureDish}, the hero dish front and center`
  : `the most appetizing signature dish for the cuisine, hero composition`;

const PROMPT = `Stunning hero image for a ${cuisineType} restaurant on a delivery marketplace listing. \
${subjectLine}. Wide cinematic 16:9 composition, commercial food photography, dramatic warm lighting, \
shallow depth of field, magazine-quality, $3,000 production value, the kind of photo that makes someone \
order immediately. Modern clean aesthetic, single hero subject, soft natural background, no people, \
no packaging or text. Critical: absolutely zero text, words, letters, watermarks, or logos.`;

const SIZE = '2048x1152'; // 16:9 hero aspect

async function generate() {
  console.log(`Generating hero mockup for: ${brandSlug}`);
  console.log(`  Cuisine: ${cuisineType}${signatureDish ? ` · Dish: ${signatureDish}` : ''}`);

  for (let attempt = 1; attempt <= 3; attempt++) {
    try {
      // 1. Create prediction
      const create = await fetch('https://api.replicate.com/v1/models/bytedance/seedream-4.5/predictions', {
        method: 'POST',
        headers: { Authorization: `Bearer ${TOKEN}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          input: {
            prompt: PROMPT,
            negative_prompt: NEG,
            image_size: SIZE,
          },
        }),
      });
      if (!create.ok) throw new Error(`Create failed: ${create.status} ${await create.text()}`);
      let pred = await create.json();

      // 2. Poll
      const start = Date.now();
      for (let i = 0; i < 60 && pred.status !== 'succeeded' && pred.status !== 'failed'; i++) {
        await new Promise(r => setTimeout(r, 2000));
        const poll = await fetch(pred.urls.get, { headers: { Authorization: `Bearer ${TOKEN}` } });
        pred = await poll.json();
      }
      if (pred.status !== 'succeeded') throw new Error(`Prediction ${pred.status}: ${pred.error || 'unknown'}`);

      // 3. Download
      const imgUrl = Array.isArray(pred.output) ? pred.output[0] : pred.output;
      const imgRes = await fetch(imgUrl);
      if (!imgRes.ok) throw new Error(`Image download failed: ${imgRes.status}`);
      const buf = Buffer.from(await imgRes.arrayBuffer());
      fs.writeFileSync(OUT_JPG, buf);

      // 4. Save metadata
      fs.writeFileSync(OUT_META, JSON.stringify({
        brand_slug: brandSlug,
        cuisine_type: cuisineType,
        signature_dish: signatureDish || null,
        prompt: PROMPT,
        negative_prompt: NEG,
        image_size: SIZE,
        replicate_prediction_id: pred.id,
        generated_at: new Date().toISOString(),
        elapsed_seconds: Math.round((Date.now() - start) / 1000),
        size_kb: Math.round(buf.length / 1024),
        output_jpg: OUT_JPG,
      }, null, 2));

      console.log(`  ✓ Generated in ${Math.round((Date.now() - start) / 1000)}s (${Math.round(buf.length / 1024)}KB)`);
      console.log(`  Saved: ${OUT_JPG}`);
      console.log(`  Meta:  ${OUT_META}`);
      console.log(`\nNext: pair this with the prospect's current hero in audit HTML side-by-side.`);
      return;
    } catch (e) {
      console.warn(`  Attempt ${attempt}/3 failed: ${e.message}`);
      if (attempt < 3) await new Promise(r => setTimeout(r, 12000));
    }
  }

  console.error('All attempts failed. No mockup generated.');
  process.exit(1);
}

generate();
