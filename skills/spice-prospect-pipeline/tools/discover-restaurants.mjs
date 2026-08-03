#!/usr/bin/env node
// discover-restaurants.mjs
// Discovers mid-market multi-location restaurants (5-100 locations) via Google Places API.
// Filters out corporate giants, single-unit independents, and existing Spice clients.
//
// Usage:
//   GOOGLE_PLACES_API_KEY=... node discover-restaurants.mjs
//
// Optional env:
//   CITIES (default: "Los Angeles CA|New York NY|Austin TX")
//   MAX_PER_CITY (default: 60)
//   MIN_LOCATIONS (default: 5)
//   MAX_LOCATIONS (default: 100)
//   MIN_RATING (default: 4.0)
//   MIN_REVIEWS (default: 50)
//   EXCLUDE_FILE (default: ./website-biz-data/excluded-brands.json)
//   OUTPUT (default: ./spice-prospect-pipeline-data/discovered.json)

import fs from 'fs';
import path from 'path';

const KEY = process.env.GOOGLE_PLACES_API_KEY;
if (!KEY) { console.error('Missing GOOGLE_PLACES_API_KEY'); process.exit(1); }

const CITIES = (process.env.CITIES || 'Los Angeles CA|New York NY|Austin TX').split('|');
const MAX_PER_CITY = parseInt(process.env.MAX_PER_CITY || '60');
const MIN_LOCATIONS = parseInt(process.env.MIN_LOCATIONS || '5');
const MAX_LOCATIONS = parseInt(process.env.MAX_LOCATIONS || '100');
const MIN_RATING = parseFloat(process.env.MIN_RATING || '4.0');
const MIN_REVIEWS = parseInt(process.env.MIN_REVIEWS || '50');

const HOME = process.env.HOME;
const OUT_DIR = process.env.OUTPUT_DIR || `${HOME}/Desktop/spice-prospect-pipeline-data`;
const OUT_FILE = path.join(OUT_DIR, 'discovered.json');
fs.mkdirSync(OUT_DIR, { recursive: true });

// Brands to skip — corporate giants, gas-station food, fast food, existing Spice clients
const EXCLUDE_DEFAULTS = [
  // Fast food giants (>200 locations)
  "mcdonald's", "starbucks", "subway", "burger king", "wendy's", "taco bell",
  "kfc", "pizza hut", "domino's", "papa john's", "dunkin'", "tim hortons",
  "chick-fil-a", "popeyes", "arby's", "jack in the box", "carl's jr", "hardee's",
  "five guys", "in-n-out", "shake shack", "panera", "chipotle", "qdoba",
  "panda express", "olive garden", "applebee's", "chili's", "outback",
  "red lobster", "ihop", "denny's", "cracker barrel", "buffalo wild wings",
  "sonic", "jersey mike's", "jimmy john's", "panera bread", "moe's",
  // Coffee chains
  "philz coffee", "blue bottle", "peet's", "the coffee bean",
  // Existing Spice clients (don't pitch ourselves)
  'pret', 'pret a manger', 'capriotti', "capriotti's", 'goop kitchen', 'gertrude',
  'fresh kitchen', 'everytable', 'counter service', 'brasa peruvian',
  "tiff's treats", 'westville', 'virgil', "virgil's", 'alicart', 'ahipoki',
  'menya ultra', 'mbfs', "cal's corner", 'puesto', 'dayglow', 'awan', 'teleferic',
  'bacon deliver', 'goop', 'daily grill', "daily's",
  // Gas station / convenience food
  '7-eleven', 'wawa', 'speedway', 'circle k',
];

let excluded = new Set(EXCLUDE_DEFAULTS.map(s => s.toLowerCase()));
const excludeFile = process.env.EXCLUDE_FILE;
if (excludeFile && fs.existsSync(excludeFile)) {
  const extra = JSON.parse(fs.readFileSync(excludeFile, 'utf8'));
  for (const b of extra) excluded.add(String(b).toLowerCase());
}

function shouldExclude(name) {
  const lower = name.toLowerCase();
  for (const ex of excluded) {
    if (lower === ex || lower.startsWith(ex + ' ') || lower.includes(' ' + ex + ' ') || lower.endsWith(' ' + ex)) {
      return true;
    }
  }
  return false;
}

function normalizeBrand(name) {
  // Strip location suffixes like "(Downtown)", "- Brooklyn", numbers, "#3"
  return name
    .replace(/\s*[-–—]\s*[A-Z][a-zA-Z\s]+$/, '')
    .replace(/\s*\([^)]+\)\s*$/, '')
    .replace(/\s*#\d+\s*$/, '')
    .replace(/\s+\d+$/, '')
    .trim();
}

async function searchCity(query, location) {
  const results = [];
  let pageToken = null;
  let pages = 0;

  while (results.length < MAX_PER_CITY && pages < 3) {
    if (pages > 0) await new Promise(r => setTimeout(r, 2500));

    const url = pageToken
      ? `https://maps.googleapis.com/maps/api/place/textsearch/json?pagetoken=${pageToken}&key=${KEY}`
      : `https://maps.googleapis.com/maps/api/place/textsearch/json?query=${encodeURIComponent(query + ' in ' + location)}&type=restaurant&key=${KEY}`;

    const res = await fetch(url);
    const data = await res.json();

    if (data.status !== 'OK' && data.status !== 'ZERO_RESULTS') {
      console.error(`API error in ${location}:`, data.status, data.error_message || '');
      break;
    }

    for (const place of (data.results || [])) {
      results.push({
        place_id: place.place_id,
        name: place.name,
        normalized: normalizeBrand(place.name),
        address: place.formatted_address || '',
        rating: place.rating || null,
        reviews: place.user_ratings_total || 0,
        types: place.types || [],
        city: location,
      });
    }

    pageToken = data.next_page_token;
    if (!pageToken) break;
    pages++;
  }

  return results;
}

async function main() {
  console.log(`Discovering restaurants across ${CITIES.length} cities...`);
  console.log(`  Filter: ${MIN_LOCATIONS}-${MAX_LOCATIONS} locations, rating ≥${MIN_RATING}, reviews ≥${MIN_REVIEWS}\n`);

  const allResults = [];
  for (const city of CITIES) {
    console.log(`Searching: ${city}`);
    const cityResults = await searchCity('restaurants', city);
    console.log(`  Found ${cityResults.length} raw results in ${city}`);
    allResults.push(...cityResults);
  }

  // Group by normalized brand name across all cities
  const byBrand = {};
  for (const r of allResults) {
    if (!byBrand[r.normalized]) byBrand[r.normalized] = [];
    byBrand[r.normalized].push(r);
  }

  // Filter to mid-market chains
  const candidates = [];
  for (const [brand, locs] of Object.entries(byBrand)) {
    if (locs.length < MIN_LOCATIONS) continue;
    if (locs.length > MAX_LOCATIONS) continue;
    if (shouldExclude(brand)) continue;

    // Use highest-review location as the brand exemplar
    const exemplar = locs.sort((a, b) => b.reviews - a.reviews)[0];
    if (!exemplar.rating || exemplar.rating < MIN_RATING) continue;
    if (exemplar.reviews < MIN_REVIEWS) continue;

    // Filter out non-restaurants (the 'type' filter helps but Places sometimes returns hotels, etc.)
    const restaurantTypes = ['restaurant', 'food', 'meal_takeaway', 'meal_delivery', 'cafe', 'bakery'];
    if (!exemplar.types.some(t => restaurantTypes.includes(t))) continue;

    candidates.push({
      brand,
      locations_in_target_cities: locs.length,
      cities: [...new Set(locs.map(l => l.city))],
      exemplar_rating: exemplar.rating,
      exemplar_reviews: exemplar.reviews,
      sample_locations: locs.slice(0, 5).map(l => ({ name: l.name, address: l.address, city: l.city })),
      types: exemplar.types,
      discovered_at: new Date().toISOString(),
    });
  }

  // Sort: prefer multi-city presence, then total reviews
  candidates.sort((a, b) => {
    const cityDiff = b.cities.length - a.cities.length;
    if (cityDiff) return cityDiff;
    return b.exemplar_reviews - a.exemplar_reviews;
  });

  // Merge with existing discovered (don't overwrite)
  let existing = [];
  if (fs.existsSync(OUT_FILE)) existing = JSON.parse(fs.readFileSync(OUT_FILE, 'utf8'));
  const existingBrands = new Set(existing.map(c => c.brand));
  const newOnes = candidates.filter(c => !existingBrands.has(c.brand));
  const merged = [...existing, ...newOnes];
  fs.writeFileSync(OUT_FILE, JSON.stringify(merged, null, 2));

  console.log(`\n✓ Discovery complete`);
  console.log(`  Raw results scanned: ${allResults.length}`);
  console.log(`  Unique brands: ${Object.keys(byBrand).length}`);
  console.log(`  Mid-market candidates (passing filters): ${candidates.length}`);
  console.log(`  New (not previously discovered): ${newOnes.length}`);
  console.log(`  Saved to: ${OUT_FILE}`);

  if (newOnes.length > 0) {
    console.log(`\nTop 10 new candidates:`);
    newOnes.slice(0, 10).forEach((c, i) => {
      console.log(`  ${i + 1}. ${c.brand} — ${c.locations_in_target_cities} locs in ${c.cities.length} cities, ${c.exemplar_rating}★ (${c.exemplar_reviews} reviews)`);
    });
  }

  console.log(`\nNext: review candidates and add chosen brands to Notion Sales Pipeline as Status="Targeted"`);
}

main().catch(e => { console.error(e); process.exit(1); });
