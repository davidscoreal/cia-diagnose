#!/usr/bin/env python3
"""Playwright script to update @ A record on Hostinger DNS.
Target: Change @ A record from 2.57.91.91 -> 89.167.122.33
Domain: univercityaiconsult.tech
"""
import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PwTimeout

DOMAIN = "univercityaiconsult.tech"
OLD_IP = "2.57.91.91"
NEW_IP = "89.167.122.33"
DNS_URL = f"https://hpanel.hostinger.com/domain/{DOMAIN}/dns"
USER_DATA = Path.home() / ".hostinger-playwright"


async def main():
    print(f"Goal: Change @ A record {OLD_IP} -> {NEW_IP}")

    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            str(USER_DATA),
            headless=False,
            viewport={"width": 1280, "height": 900},
            slow_mo=200,
        )
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()

        print(f"Navigating to {DNS_URL}")
        try:
            await page.goto(DNS_URL, wait_until="domcontentloaded", timeout=60000)
        except PwTimeout:
            print("Initial load slow, continuing anyway...")

        await asyncio.sleep(5)

        # Check if login needed
        if "login" in page.url or "auth" in page.url:
            print("LOGIN REQUIRED - please log in manually.")
            print("Waiting up to 180s...")
            try:
                await page.wait_for_url("**/domain/**", timeout=180000)
                print("Login detected!")
                # Re-navigate to DNS page after login
                await page.goto(DNS_URL, wait_until="domcontentloaded", timeout=60000)
                await asyncio.sleep(5)
            except PwTimeout:
                print("Login timeout.")
                await ctx.close()
                return False

        # Wait for page to settle
        print("Waiting for DNS page to settle...")
        await asyncio.sleep(8)

        ss = str(USER_DATA / "dns_page.png")
        await page.screenshot(path=ss)
        print(f"Screenshot: {ss}")

        # Check page content
        content = await page.content()
        if NEW_IP in content and OLD_IP not in content:
            print(f"{NEW_IP} already on page, {OLD_IP} gone. Already done!")
            await ctx.close()
            return True

        if OLD_IP not in content:
            print(f"{OLD_IP} not found on page.")
            # Maybe need to scroll down
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            content = await page.content()
            if OLD_IP not in content:
                print("Still not found after scroll. Check screenshot.")
                await page.screenshot(path=str(USER_DATA / "scrolled.png"))
                # Leave browser open for manual intervention
                print("Leaving browser open 5min for manual action...")
                await asyncio.sleep(300)
                await ctx.close()
                return False

        # Found old IP. Now try to edit it.
        print(f"Found {OLD_IP}. Looking for edit mechanism...")

        # Hostinger's DNS table: each record has a 3-dot menu or edit icon
        # Try multiple strategies

        # Strategy 1: Look for edit/pencil/dots button in same row
        old_ip_els = page.locator(f"text='{OLD_IP}'")
        count = await old_ip_els.count()
        print(f"Found {count} elements with {OLD_IP}")

        clicked_edit = False
        for idx in range(count):
            el = old_ip_els.nth(idx)
            # Walk up to find the row container
            for ancestor_sel in [
                "xpath=ancestor::tr[1]",
                "xpath=ancestor::div[contains(@class,'record') or contains(@class,'row') or contains(@class,'item')][1]",
                "xpath=ancestor::div[4]",
            ]:
                try:
                    row = el.locator(ancestor_sel)
                    if await row.count() == 0:
                        continue
                    # Find clickable edit elements in this row
                    for btn_sel in [
                        "button:has-text('Edit')",
                        "button:has-text('Editar')",
                        "[class*='edit']",
                        "[class*='pencil']",
                        "[class*='dots']",
                        "[class*='menu']",
                        "[class*='action'] button",
                        "button:last-of-type",
                        "svg",
                    ]:
                        btns = row.locator(btn_sel)
                        bc = await btns.count()
                        if bc > 0:
                            await btns.first.click()
                            print(f"Clicked: {btn_sel} in row")
                            clicked_edit = True
                            await asyncio.sleep(2)
                            break
                    if clicked_edit:
                        break
                except Exception:
                    continue
            if clicked_edit:
                break

        if not clicked_edit:
            # Strategy 2: Just click the old IP text itself
            print("No edit button found, clicking IP text directly...")
            await old_ip_els.first.click()
            await asyncio.sleep(2)

        await page.screenshot(path=str(USER_DATA / "after_edit_click.png"))

        # Now look for input with old IP value
        print("Looking for input field with old IP...")
        inputs = page.locator("input")
        ic = await inputs.count()
        print(f"Found {ic} input elements")

        ip_changed = False
        for i in range(ic):
            inp = inputs.nth(i)
            try:
                val = await inp.input_value()
                vis = await inp.is_visible()
                if vis and OLD_IP in val:
                    print(f"Input {i}: '{val}' -- replacing")
                    await inp.triple_click()
                    await asyncio.sleep(0.3)
                    await inp.fill(NEW_IP)
                    # Also dispatch input event for React
                    await inp.dispatch_event("input")
                    await inp.dispatch_event("change")
                    ip_changed = True
                    print(f"Changed to {NEW_IP}")
                    break
            except Exception as e:
                continue

        if not ip_changed:
            print("No input with old IP found.")
            # Dump all input values for debugging
            for i in range(min(ic, 20)):
                try:
                    val = await inputs.nth(i).input_value()
                    vis = await inputs.nth(i).is_visible()
                    print(f"  input[{i}]: vis={vis} val='{val[:50]}'")
                except:
                    pass
            await page.screenshot(path=str(USER_DATA / "no_input.png"))
            print("Leaving browser open 5min...")
            await asyncio.sleep(300)
            await ctx.close()
            return False

        await page.screenshot(path=str(USER_DATA / "after_change.png"))

        # Click save/confirm
        print("Looking for save button...")
        await asyncio.sleep(1)

        for sel in [
            "button:has-text('Update')",
            "button:has-text('Actualizar')",
            "button:has-text('Save')",
            "button:has-text('Guardar')",
            "button:has-text('Confirm')",
            "button:has-text('Confirmar')",
            "button[type='submit']",
            "button.btn-primary",
            "button[class*='primary']",
            "button[class*='submit']",
        ]:
            btn = page.locator(sel).first
            try:
                if await btn.is_visible():
                    await btn.click()
                    print(f"Clicked: {sel}")
                    await asyncio.sleep(3)
                    break
            except:
                continue

        await page.screenshot(path=str(USER_DATA / "after_save.png"))

        # Check for confirmation dialog
        await asyncio.sleep(2)
        for sel in [
            "button:has-text('Confirm')",
            "button:has-text('Confirmar')",
            "button:has-text('Yes')",
            "button:has-text('OK')",
            "[class*='modal'] button[class*='primary']",
            "[class*='dialog'] button[class*='primary']",
        ]:
            btn = page.locator(sel).first
            try:
                if await btn.is_visible():
                    await btn.click()
                    print(f"Confirmed: {sel}")
                    await asyncio.sleep(3)
                    break
            except:
                continue

        await page.screenshot(path=str(USER_DATA / "final.png"))

        # Verify
        print("Reloading to verify...")
        await asyncio.sleep(2)
        await page.reload(wait_until="domcontentloaded")
        await asyncio.sleep(8)
        content = await page.content()

        if NEW_IP in content:
            print(f"SUCCESS! {NEW_IP} found after reload.")
            await page.screenshot(path=str(USER_DATA / "verified.png"))
            await ctx.close()
            return True
        else:
            print("Could not verify. Check screenshots.")
            await page.screenshot(path=str(USER_DATA / "unverified.png"))
            await ctx.close()
            return False


if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
