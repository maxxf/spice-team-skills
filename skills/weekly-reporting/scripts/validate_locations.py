#!/usr/bin/env python3
"""validate_locations.py - Validate and map location names across platform extraction outputs.

Runs between extraction (Phase 3) and aggregation (Phase 4). Reads a structured store map
JSON and each platform's extraction JSON. Produces a flat lookup map for the aggregation
script and flags any unmapped locations.

Usage:
    python validate_locations.py \
        --store-map references/store-maps/goop-kitchen.json \
        --output-dir OUTPUT

Outputs:
    OUTPUT/location_map.json  — flat lookup {platform_name: canonical_name} for aggregation
    stdout                    — warnings for unmapped locations, merge actions, validation summary

Store Map JSON Format (per client):
{
  "client": "Client Name",
  "locations": {
    "Canonical Name": {
      "uber_eats": ["platform name 1", "alt name"],
      "doordash": ["platform name"],
      "grubhub": ["Name|City|Address"]
    }
  },
  "merge_rules": {
    "Source Canonical": "Target Canonical"
  }
}

The merge_rules field handles cases where two canonical locations should be combined
in the tracker (e.g., North Hollywood → Studio City). The validator applies these
merges to the flat map output so aggregation combines them automatically.
"""
import argparse, json, glob, os, re, sys


PLATFORM_KEYS = {
    "uber_eats": "uber_eats",
    "doordash": "doordash",
    "grubhub": "grubhub",
}


def load_store_map(fp):
    with open(fp) as fh:
        return json.load(fh)


def build_flat_lookup(store_map_data):
    """Build {platform_name: canonical_name} from structured store map.

    Also applies merge_rules so that e.g. "North Hollywood" platform names
    map directly to "Studio City" (the tracker canonical).

    Handles extraction agent normalization: agents may strip brand prefixes
    and output just the location part (e.g., "Robertson" instead of
    "goop kitchen (Robertson)"). We extract these short names automatically.
    """
    locations = store_map_data.get("locations", {})
    merge_rules = store_map_data.get("merge_rules", {})
    lookup = {}

    for canonical, platforms in locations.items():
        # Apply merge rule: if this canonical merges into another, use the target
        target = merge_rules.get(canonical, canonical)

        for plat_key, names in platforms.items():
            for name in names:
                if name:
                    lookup[name] = target
                    lookup[name.lower().strip()] = target

                    # Auto-extract short name from "brand (Location)" pattern
                    # e.g., "goop kitchen (Robertson)" → "Robertson"
                    m = re.search(r'\(([^)]+)\)', name)
                    if m:
                        short = m.group(1).strip()
                        # Only add if not already a canonical name (avoid collisions)
                        if short not in lookup:
                            lookup[short] = target
                        if short.lower().strip() not in lookup:
                            lookup[short.lower().strip()] = target

                    # Auto-extract from "Brand (Location @ Suffix)" → "Location"
                    m2 = re.search(r'\(([^@)]+?)(?:\s*@\s*[^)]+)?\)', name)
                    if m2:
                        base = m2.group(1).strip()
                        if base not in lookup:
                            lookup[base] = target
                        if base.lower().strip() not in lookup:
                            lookup[base.lower().strip()] = target

        # Map the canonical name itself
        lookup[canonical] = target
        lookup[canonical.lower().strip()] = target

    return lookup


def build_expected_locations(store_map_data):
    """Build {platform_key: set(canonical_names)} for what we expect from each platform."""
    locations = store_map_data.get("locations", {})
    merge_rules = store_map_data.get("merge_rules", {})
    expected = {}

    for canonical, platforms in locations.items():
        target = merge_rules.get(canonical, canonical)
        for plat_key, names in platforms.items():
            if names:  # Only expect locations that have platform names defined
                expected.setdefault(plat_key, set()).add(target)

    return expected


def normalize_name(name, city=None, address=None):
    """Build lookup keys for a location name, optionally with city/address for GH."""
    keys = [name, name.lower().strip()]
    if city and address:
        # GH composite key: "Name|City|Address"
        composite = f"{name}|{city}|{address}"
        keys.extend([composite, composite.lower().strip()])
        # Also try without the store name (just city|address)
        keys.extend([f"{city}|{address}", f"{city}|{address}".lower().strip()])
    return keys


def validate_platform(platform_key, platform_label, json_data, flat_lookup, expected):
    """Validate locations in a single platform's extraction output.

    Returns: (mapped_count, unmapped_list, missing_list)
    - mapped_count: number of locations successfully mapped
    - unmapped_list: [{name, revenue, orders}] for locations not in the store map
    - missing_list: canonical names expected but not found in the data
    """
    by_location = json_data.get("by_location", [])
    mapped = 0
    unmapped = []
    found_canonicals = set()

    for loc in by_location:
        raw_name = loc.get("location") or loc.get("store_name") or loc.get("name", "Unknown")
        city = loc.get("city")
        address = loc.get("street_address")
        revenue = loc.get("total_net_sales", 0) or 0
        orders = loc.get("total_orders", 0) or 0

        # Try all name variants
        resolved = None
        for key in normalize_name(raw_name, city, address):
            if key in flat_lookup:
                resolved = flat_lookup[key]
                break

        if resolved:
            mapped += 1
            found_canonicals.add(resolved)
        else:
            unmapped.append({
                "name": raw_name,
                "city": city,
                "address": address,
                "revenue": revenue,
                "orders": orders,
            })

    # Check for expected locations not found in data
    expected_for_platform = expected.get(platform_key, set())
    missing = expected_for_platform - found_canonicals

    return mapped, unmapped, missing


def main():
    p = argparse.ArgumentParser(description="Validate location names across platform extractions")
    p.add_argument("--store-map", required=True, help="Path to structured store map JSON")
    p.add_argument("--output-dir", required=True, help="Directory containing *_results.json files")
    a = p.parse_args()

    if not os.path.exists(a.store_map):
        print(f"ERROR: Store map not found: {a.store_map}")
        sys.exit(1)

    store_map_data = load_store_map(a.store_map)
    client = store_map_data.get("client", "Unknown")
    flat_lookup = build_flat_lookup(store_map_data)
    expected = build_expected_locations(store_map_data)
    merge_rules = store_map_data.get("merge_rules", {})

    print(f"=== Location Validation: {client} ===")
    print(f"Store map: {len(store_map_data.get('locations', {}))} canonical locations")
    if merge_rules:
        print(f"Merge rules: {', '.join(f'{k} → {v}' for k, v in merge_rules.items())}")
    print()

    json_files = glob.glob(os.path.join(a.output_dir, "*_results.json"))
    if not json_files:
        print(f"ERROR: No *_results.json files found in {a.output_dir}")
        sys.exit(1)

    all_unmapped = []
    all_missing = []
    total_mapped = 0
    total_locations = 0
    has_errors = False

    for jf in sorted(json_files):
        with open(jf) as fh:
            data = json.load(fh)

        platform_key = data.get("platform", "")
        platform_label = {"uber_eats": "Uber Eats", "doordash": "DoorDash", "grubhub": "Grubhub"}.get(
            platform_key, platform_key
        )

        loc_count = len(data.get("by_location", []))
        total_locations += loc_count
        mapped, unmapped, missing = validate_platform(platform_key, platform_label, data, flat_lookup, expected)
        total_mapped += mapped

        status = "✓" if not unmapped and not missing else "⚠"
        print(f"{status} {platform_label}: {mapped}/{loc_count} locations mapped")

        if unmapped:
            has_errors = True
            for u in unmapped:
                rev_str = f"${u['revenue']:,.0f}" if u['revenue'] else "$0"
                addr_str = f" ({u.get('city', '')}, {u.get('address', '')})" if u.get('city') else ""
                print(f"  ✗ UNMAPPED: \"{u['name']}\"{addr_str} — {rev_str} revenue, {u['orders']} orders")
                all_unmapped.append({**u, "platform": platform_label})

        if missing:
            for m in sorted(missing):
                print(f"  ? MISSING: Expected \"{m}\" but not found in {platform_label} data")
                all_missing.append({"canonical": m, "platform": platform_label})

    print()
    print(f"Summary: {total_mapped}/{total_locations} locations mapped across all platforms")

    if all_unmapped:
        total_unmapped_rev = sum(u["revenue"] for u in all_unmapped)
        print(f"⚠ {len(all_unmapped)} unmapped locations with ${total_unmapped_rev:,.0f} in revenue")
        print("  → Add these to the store map JSON before running aggregation")
        has_errors = True

    if all_missing:
        print(f"ℹ {len(all_missing)} expected locations not found in data (may be closed/inactive this week)")

    # Write flat lookup map for aggregation script
    map_path = os.path.join(a.output_dir, "location_map.json")
    with open(map_path, "w") as fh:
        # Only write the clean lookup (no lowercase duplicates)
        clean_lookup = {}
        locations = store_map_data.get("locations", {})
        for canonical, platforms in locations.items():
            target = merge_rules.get(canonical, canonical)
            for plat_key, names in platforms.items():
                for name in names:
                    if name:
                        clean_lookup[name] = target
            clean_lookup[canonical] = target
        json.dump(clean_lookup, fh, indent=2)
    print(f"\nWrote {map_path} ({len(clean_lookup)} entries)")

    if has_errors:
        print("\n⚠ UNMAPPED LOCATIONS DETECTED — aggregation will use raw names for unmatched locations.")
        print("  Fix: Add missing names to the store map JSON, then re-run validation.")
        sys.exit(1)
    else:
        print("\n✓ All locations validated. Ready for aggregation.")
        sys.exit(0)


if __name__ == "__main__":
    main()
