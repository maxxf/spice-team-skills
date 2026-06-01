#!/usr/bin/env python3
"""
Storefront Audit Browser Automation
Navigates Uber Eats, DoorDash, Grubhub to collect storefront data and screenshots.

Usage:
    python3 audit_storefront.py "Restaurant Name" "City, State" --platforms uber doordash grubhub

Requirements:
    pip install playwright
    playwright install chromium
"""

import argparse
import json
import os
import re
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, Page, Browser

# Output directory for screenshots and data
OUTPUT_DIR = Path("./audit_output")


class StorefrontAuditor:
    """Automates storefront data collection across delivery platforms."""
    
    def __init__(self, brand: str, market: str):
        self.brand = brand
        self.market = market
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_path = OUTPUT_DIR / f"{self._slug(brand)}_{self.timestamp}"
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.results = {
            "brand": brand,
            "market": market,
            "timestamp": self.timestamp,
            "platforms": {}
        }
    
    def _slug(self, text: str) -> str:
        return re.sub(r'[^a-z0-9]+', '_', text.lower()).strip('_')
    
    async def run(self, platforms: list[str]):
        """Execute audit across specified platforms."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)  # Set True for headless
            context = await browser.new_context(
                viewport={"width": 1440, "height": 900},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            )
            page = await context.new_page()
            
            for platform in platforms:
                print(f"\n{'='*50}")
                print(f"Auditing {self.brand} on {platform.upper()}")
                print('='*50)
                
                if platform == "uber":
                    await self.audit_uber_eats(page)
                elif platform == "doordash":
                    await self.audit_doordash(page)
                elif platform == "grubhub":
                    await self.audit_grubhub(page)
                
            await browser.close()
        
        # Save consolidated results
        self._save_results()
        return self.results
    
    async def audit_uber_eats(self, page: Page):
        """Audit storefront on Uber Eats."""
        platform_data = {
            "platform": "uber_eats",
            "found": False,
            "locations": [],
            "discovery_log": []
        }
        
        try:
            # Navigate to Uber Eats
            await page.goto("https://www.ubereats.com/")
            await page.wait_for_load_state("networkidle")
            platform_data["discovery_log"].append("Loaded Uber Eats homepage")
            
            # Set delivery address
            address_input = page.locator('[data-testid="location-typeahead-input"], input[placeholder*="address"], input[placeholder*="delivery"]').first
            if await address_input.is_visible():
                await address_input.click()
                await address_input.fill(self.market)
                await page.wait_for_timeout(1500)
                await page.keyboard.press("ArrowDown")
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(2000)
                platform_data["discovery_log"].append(f"Set delivery address: {self.market}")
            
            # Search for restaurant
            search_input = page.locator('[data-testid="search-input"], input[placeholder*="Search"], input[aria-label*="Search"]').first
            await search_input.click()
            await search_input.fill(self.brand)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3000)
            platform_data["discovery_log"].append(f"Searched for: {self.brand}")
            
            # Screenshot search results
            await page.screenshot(
                path=self.output_path / "uber_eats_search_results.png",
                full_page=False
            )
            
            # Click first matching result
            restaurant_card = page.locator(f'a:has-text("{self.brand}")').first
            if await restaurant_card.is_visible():
                await restaurant_card.click()
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(2000)
                platform_data["found"] = True
                platform_data["discovery_log"].append("Found and opened storefront")
                
                # Collect storefront data
                location_data = await self._extract_uber_data(page)
                platform_data["locations"].append(location_data)
                
                # Screenshot hero area
                await page.screenshot(
                    path=self.output_path / "uber_eats_hero.png",
                    full_page=False
                )
                
                # Scroll and screenshot menu
                await page.evaluate("window.scrollBy(0, 600)")
                await page.wait_for_timeout(1000)
                await page.screenshot(
                    path=self.output_path / "uber_eats_menu.png",
                    full_page=False
                )
                
            else:
                platform_data["discovery_log"].append("Restaurant not found in search results")
                
        except Exception as e:
            platform_data["discovery_log"].append(f"Error: {str(e)}")
            platform_data["error"] = str(e)
        
        self.results["platforms"]["uber_eats"] = platform_data
    
    async def _extract_uber_data(self, page: Page) -> dict:
        """Extract storefront data from Uber Eats page."""
        data = {
            "url": page.url,
            "screenshots": ["uber_eats_hero.png", "uber_eats_menu.png"]
        }
        
        # Extract rating
        rating_el = page.locator('[data-testid="store-rating"], [class*="rating"]').first
        if await rating_el.is_visible():
            data["rating"] = await rating_el.text_content()
        
        # Extract review count
        reviews_el = page.locator('text=/\\d+\\+?\\s*ratings?/i').first
        if await reviews_el.is_visible():
            data["review_count"] = await reviews_el.text_content()
        
        # Check hero image
        hero_img = page.locator('header img, [class*="hero"] img, [class*="cover"] img').first
        data["hero_image_present"] = await hero_img.is_visible() if hero_img else False
        
        # Count menu categories
        categories = await page.locator('[data-testid="menu-category"], h2, h3').all()
        data["category_count"] = len([c for c in categories if await c.is_visible()])
        
        # Check for promos
        promo_el = page.locator('text=/free delivery|% off|\\$\\d+ off/i').first
        data["promos_visible"] = await promo_el.is_visible() if promo_el else False
        
        return data
    
    async def audit_doordash(self, page: Page):
        """Audit storefront on DoorDash."""
        platform_data = {
            "platform": "doordash",
            "found": False,
            "locations": [],
            "discovery_log": []
        }
        
        try:
            # Navigate to DoorDash
            await page.goto("https://www.doordash.com/")
            await page.wait_for_load_state("networkidle")
            platform_data["discovery_log"].append("Loaded DoorDash homepage")
            
            # Set delivery address
            address_input = page.locator('input[placeholder*="address"], input[data-testid*="address"]').first
            if await address_input.is_visible():
                await address_input.click()
                await address_input.fill(self.market)
                await page.wait_for_timeout(1500)
                await page.keyboard.press("ArrowDown")
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(2000)
                platform_data["discovery_log"].append(f"Set delivery address: {self.market}")
            
            # Search for restaurant
            search_input = page.locator('input[placeholder*="Search"], input[data-testid*="search"]').first
            await search_input.click()
            await search_input.fill(self.brand)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3000)
            platform_data["discovery_log"].append(f"Searched for: {self.brand}")
            
            # Screenshot search results
            await page.screenshot(
                path=self.output_path / "doordash_search_results.png",
                full_page=False
            )
            
            # Click first matching result
            restaurant_card = page.locator(f'a:has-text("{self.brand}"), [data-testid="store-card"]:has-text("{self.brand}")').first
            if await restaurant_card.is_visible():
                await restaurant_card.click()
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(2000)
                platform_data["found"] = True
                platform_data["discovery_log"].append("Found and opened storefront")
                
                # Collect storefront data
                location_data = await self._extract_doordash_data(page)
                platform_data["locations"].append(location_data)
                
                # Screenshot hero area
                await page.screenshot(
                    path=self.output_path / "doordash_hero.png",
                    full_page=False
                )
                
                # Scroll and screenshot menu
                await page.evaluate("window.scrollBy(0, 600)")
                await page.wait_for_timeout(1000)
                await page.screenshot(
                    path=self.output_path / "doordash_menu.png",
                    full_page=False
                )
                
            else:
                platform_data["discovery_log"].append("Restaurant not found in search results")
                
        except Exception as e:
            platform_data["discovery_log"].append(f"Error: {str(e)}")
            platform_data["error"] = str(e)
        
        self.results["platforms"]["doordash"] = platform_data
    
    async def _extract_doordash_data(self, page: Page) -> dict:
        """Extract storefront data from DoorDash page."""
        data = {
            "url": page.url,
            "screenshots": ["doordash_hero.png", "doordash_menu.png"]
        }
        
        # Extract rating
        rating_el = page.locator('[data-testid="rating"], [class*="rating"]').first
        if await rating_el.is_visible():
            data["rating"] = await rating_el.text_content()
        
        # Extract review count
        reviews_el = page.locator('text=/\\(\\d+[\\+k]?\\)/i, text=/\\d+\\s*ratings/i').first
        if await reviews_el.is_visible():
            data["review_count"] = await reviews_el.text_content()
        
        # Check hero image
        hero_img = page.locator('[class*="hero"] img, [class*="cover"] img, header img').first
        data["hero_image_present"] = await hero_img.is_visible() if hero_img else False
        
        # Count menu categories
        categories = await page.locator('[data-testid="menu-category"], h2[class*="category"], h3').all()
        data["category_count"] = len([c for c in categories if await c.is_visible()])
        
        # Check for promos
        promo_el = page.locator('text=/free delivery|% off|\\$\\d+ off/i').first
        data["promos_visible"] = await promo_el.is_visible() if promo_el else False
        
        # Check DashPass
        dashpass_el = page.locator('text=/dashpass/i').first
        data["dashpass_eligible"] = await dashpass_el.is_visible() if dashpass_el else False
        
        return data
    
    async def audit_grubhub(self, page: Page):
        """Audit storefront on Grubhub."""
        platform_data = {
            "platform": "grubhub",
            "found": False,
            "locations": [],
            "discovery_log": []
        }
        
        try:
            # Navigate to Grubhub
            await page.goto("https://www.grubhub.com/")
            await page.wait_for_load_state("networkidle")
            platform_data["discovery_log"].append("Loaded Grubhub homepage")
            
            # Set delivery address
            address_input = page.locator('input[placeholder*="address"], input[name*="address"]').first
            if await address_input.is_visible():
                await address_input.click()
                await address_input.fill(self.market)
                await page.wait_for_timeout(1500)
                await page.keyboard.press("ArrowDown")
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(2000)
                platform_data["discovery_log"].append(f"Set delivery address: {self.market}")
            
            # Search for restaurant
            search_input = page.locator('input[placeholder*="Search"], input[name*="search"]').first
            await search_input.click()
            await search_input.fill(self.brand)
            await page.keyboard.press("Enter")
            await page.wait_for_timeout(3000)
            platform_data["discovery_log"].append(f"Searched for: {self.brand}")
            
            # Screenshot search results
            await page.screenshot(
                path=self.output_path / "grubhub_search_results.png",
                full_page=False
            )
            
            # Click first matching result
            restaurant_card = page.locator(f'a:has-text("{self.brand}")').first
            if await restaurant_card.is_visible():
                await restaurant_card.click()
                await page.wait_for_load_state("networkidle")
                await page.wait_for_timeout(2000)
                platform_data["found"] = True
                platform_data["discovery_log"].append("Found and opened storefront")
                
                # Collect storefront data
                location_data = await self._extract_grubhub_data(page)
                platform_data["locations"].append(location_data)
                
                # Screenshot hero area
                await page.screenshot(
                    path=self.output_path / "grubhub_hero.png",
                    full_page=False
                )
                
                # Scroll and screenshot menu
                await page.evaluate("window.scrollBy(0, 600)")
                await page.wait_for_timeout(1000)
                await page.screenshot(
                    path=self.output_path / "grubhub_menu.png",
                    full_page=False
                )
                
            else:
                platform_data["discovery_log"].append("Restaurant not found in search results")
                
        except Exception as e:
            platform_data["discovery_log"].append(f"Error: {str(e)}")
            platform_data["error"] = str(e)
        
        self.results["platforms"]["grubhub"] = platform_data
    
    async def _extract_grubhub_data(self, page: Page) -> dict:
        """Extract storefront data from Grubhub page."""
        data = {
            "url": page.url,
            "screenshots": ["grubhub_hero.png", "grubhub_menu.png"]
        }
        
        # Extract rating
        rating_el = page.locator('[class*="rating"], [data-testid*="rating"]').first
        if await rating_el.is_visible():
            data["rating"] = await rating_el.text_content()
        
        # Extract review count  
        reviews_el = page.locator('text=/\\d+\\s*ratings/i').first
        if await reviews_el.is_visible():
            data["review_count"] = await reviews_el.text_content()
        
        # Check hero image
        hero_img = page.locator('[class*="hero"] img, [class*="cover"] img').first
        data["hero_image_present"] = await hero_img.is_visible() if hero_img else False
        
        # Count menu categories
        categories = await page.locator('h2[class*="category"], h3[class*="menu"]').all()
        data["category_count"] = len([c for c in categories if await c.is_visible()])
        
        # Check for promos/perks
        promo_el = page.locator('text=/perks|free delivery|% off|\\$\\d+ off/i').first
        data["promos_visible"] = await promo_el.is_visible() if promo_el else False
        
        return data
    
    def _save_results(self):
        """Save consolidated results to JSON."""
        output_file = self.output_path / "audit_data.json"
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n✅ Results saved to: {output_file}")
        print(f"📁 Screenshots saved to: {self.output_path}")


async def main():
    parser = argparse.ArgumentParser(description="Audit restaurant storefronts on delivery platforms")
    parser.add_argument("brand", help="Restaurant brand name")
    parser.add_argument("market", help="Delivery market (e.g., 'Los Angeles, CA')")
    parser.add_argument(
        "--platforms", 
        nargs="+", 
        default=["uber", "doordash", "grubhub"],
        choices=["uber", "doordash", "grubhub"],
        help="Platforms to audit"
    )
    
    args = parser.parse_args()
    
    auditor = StorefrontAuditor(args.brand, args.market)
    results = await auditor.run(args.platforms)
    
    # Print summary
    print("\n" + "="*50)
    print("AUDIT SUMMARY")
    print("="*50)
    for platform, data in results["platforms"].items():
        status = "✅ Found" if data.get("found") else "❌ Not Found"
        print(f"{platform.upper()}: {status}")
        if data.get("locations"):
            loc = data["locations"][0]
            print(f"  Rating: {loc.get('rating', 'N/A')}")
            print(f"  Hero Image: {'Yes' if loc.get('hero_image_present') else 'No'}")
            print(f"  Categories: {loc.get('category_count', 'N/A')}")
            print(f"  Promos Visible: {'Yes' if loc.get('promos_visible') else 'No'}")


if __name__ == "__main__":
    asyncio.run(main())
