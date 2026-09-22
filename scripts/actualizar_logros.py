#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Captura los logros de GitHub del usuario y regenera assets/logros.svg.

Requisitos (solo si quieres actualizacion automatica):
  1. Copiar tu cookie de sesion de github.com en un secreto del repositorio
     llamado GH_SESSION_COOKIE
     (Como obtenerla: DevTools > Application > Cookies > https://github.com >
      copiar el valor de `user_session`)
  2. El workflow .github/workflows/logros.yml correra esta captura cada 6 h.

Sin cookie: el script no hace nada y termina sin error. La imagen que ya esta
en assets/logros.svg se conserva intacta (asi el README nunca queda vacio).
"""
import base64
import os
import sys

GH_USER = "keinergarcia"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "logros.svg")


def build_svg(rows):
    """Arma el panel oscuro con los logros que consiguio capturar."""
    n = len(rows)
    badge_svg = " ".join(
        f'<g transform="translate(0 {i * 44})">'
        '<rect x="620" y="-30" width="150" height="36" rx="18" '
        'fill="#0b1220" stroke="#fbbf24" stroke-opacity="0.35"/>'
        '<text x="695" y="-7" text-anchor="middle" font-size="14" '
        'font-family="Consolas,monospace" font-weight="700" fill="#fde68a">'
        f"ACEPTADO · {i + 1}</text></g>"
        for i in range(n)
    )
    images = "\n".join(
        f'<g transform="translate({150 + (i % 5) * 96} {86 + (i // 5) * 96})">'
        '<circle cx="40" cy="40" r="50" fill="#fbbf24" opacity="0.10">'
        "<animate attributeName=\"opacity\" values=\"0.10;0.28;0.10\" "
        'dur="3s" begin="%ss" repeatCount="indefinite"/></circle>'
        f"<image href=\"data:image/png;base64,{rows[i]}\" width=\"84\" "
        'height="84" preserveAspectRatio="xMidYMid meet"/>'
        '<animateTransform attributeName="transform" type="translate" '
        f'values="0 6;0 0;0 6" dur="4s" begin="{i * 0.3}s" '
        "repeatCount=\"indefinite\"/></g>"
        for i in range(n)
    )
    title = (
        "UN LOGRO GANADO" if n == 1 else f"{n} LOGROS GANADOS"
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 660 520" role="img" aria-label="Logros de GitHub de {GH_USER}">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#020617"/><stop offset="100%" stop-color="#0b1220"/>
    </linearGradient>
    <linearGradient id="brd" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#fbbf24"><animate attributeName="stop-color" values="#fbbf24;#f59e0b;#fbbf24" dur="4s" repeatCount="indefinite"/></stop>
      <stop offset="100%" stop-color="#fde68a"><animate attributeName="stop-color" values="#fde68a;#f59e0b;#fde68a" dur="4s" repeatCount="indefinite"/></stop>
    </linearGradient>
    <filter id="neon" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="2.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  </defs>
  <rect x="0" y="0" width="660" height="520" rx="26" fill="url(#bg)"/>
  <rect x="2" y="2" width="656" height="516" rx="24" fill="none" stroke="url(#brd)" stroke-width="3"/>

  <g font-family="'Segoe UI','Cascadia Code',Consolas,monospace" opacity="0">
    <animate attributeName="opacity" values="0;1" begin="0.3s" dur="0.5s" fill="freeze"/>
    <circle cx="34" cy="28" r="6" fill="#ff5f57"/>
    <circle cx="56" cy="28" r="6" fill="#febc2e"/>
    <circle cx="78" cy="28" r="6" fill="#28c840"/>
    <text x="330" y="34" font-size="14" fill="#64748b" text-anchor="middle" font-weight="600">{GH_USER}@github — ~/logros</text>
  </g>

  <text x="330" y="84" text-anchor="middle" font-size="20" font-weight="800" fill="#fbbf24" filter="url(#neon)" letter-spacing="2" opacity="0">
    <animate attributeName="opacity" values="0;1" begin="0.6s" dur="0.4s" fill="freeze"/>
    {title}
    <animate attributeName="opacity" values="1;0.75;1" begin="2s" dur="3s" repeatCount="indefinite"/>
  </text>

  {images}

  <g font-family="'Segoe UI',Consolas,monospace" font-size="14" opacity="0">
    <animate attributeName="opacity" values="0;1" begin="{1 + n * 0.2}s" dur="0.4s" fill="freeze"/>
    <text x="330" y="{430 + (n // 5) * 96}" text-anchor="middle" fill="#94a3b8">
      {n} logro{n if n == 1 else "s"} ganado{n if n == 1 else "s"} en GitHub · generado por GitHub Actions</text>
  </g>

  {badge_svg}
</svg>
"""


def main():
    cookie = os.environ.get("GH_SESSION_COOKIE", "").strip()
    if not cookie:
        print("Sin GH_SESSION_COOKIE: se conserva assets/logros.svg actual.")
        return 0
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    except ImportError:
        print("playwright no instalado; se conserva la imagen actual.")
        return 0

    rows = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1280, "height": 900})
        ctx.add_cookies([
            {
                "name": "user_session",
                "value": cookie,
                "domain": ".github.com",
                "path": "/",
                "secure": True,
                "httpOnly": True,
            }
        ])
        page = ctx.new_page()
        try:
            page.goto(f"https://github.com/{GH_USER}?tab=achievements", timeout=45000)
            page.wait_for_load_state("domcontentloaded", timeout=45000)
            page.wait_for_timeout(3500)
            title = page.title()
            if "Must sign in" in title or "Sign in" in title:
                print("La cookie no inicio sesion; se conserva la imagen actual.")
                browser.close()
                return 0
            tiles = page.locator(
                "img[src*='achievements'], img[alt*='Badge'], "
                "[data-hovercard-type*='achievement'] img"
            )
            count = tiles.count()
            print(f"Tiles detectados: {count}")
            for i in range(min(count, 12)):
                try:
                    tile = tiles.nth(i)
                    tile.scroll_into_view_if_needed(timeout=5000)
                    page.wait_for_timeout(400)
                    shot = tile.screenshot(timeout=8000)
                    rows.append(base64.b64encode(shot).decode("ascii"))
                except Exception as e:
                    print(f"tile {i} skip: {e}")
        except PWTimeout as e:
            print(f"timeout: {e}")
        finally:
            browser.close()

    if not rows:
        print("No se capturaron logros; se conserva la imagen actual.")
        return 0

    svg = build_svg(rows)
    out = os.path.abspath(OUT)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"OK: {len(rows)} logros -> {out} ({len(svg)} bytes)")


if __name__ == "__main__":
    sys.exit(main())