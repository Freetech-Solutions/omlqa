# tests/test_attend_dialer.py
import os
import re
import pytest
from playwright.sync_api import sync_playwright, expect, Page, Locator

# ⚠️ Ajusta el origin EXACTO que usas (incluye puerto si aplica)
APP_ORIGIN = "https://localhost"          # p.ej: "https://localhost:8443"
FAKE_AUDIO = os.getenv("FAKE_AUDIO_WAV")  # opcional: ruta a un .wav

# ---------- helpers de selectores ----------

def hangup_btn(page: Page) -> Locator:
    # Preferí data-test o id si existen; último recurso: glifo por rol
    candidates = [
        '[data-test="hangup-btn"]',
        '#Hangup',
        'button#Hangup',
        # glifo:
        lambda p: p.get_by_role("button", name=""),
    ]
    for sel in candidates:
        loc = sel(page) if callable(sel) else page.locator(sel)
        if loc.count() > 0:
            return loc.first
    raise AssertionError("No encontré el botón Hangup (agrega data-test/id).")

def resume_btn(page: Page) -> Locator:
    candidates = [
        '[data-test="resume-btn"]',
        '#Resume',
        'button#Resume',
        # glifo con texto:
        lambda p: p.get_by_role("button", name="Resume"),
    ]
    for sel in candidates:
        loc = sel(page) if callable(sel) else page.locator(sel)
        if loc.count() > 0:
            return loc.first
    raise AssertionError("No encontré el botón Resume (agrega data-test/id).")

def open_user_menu_btn(page: Page) -> Locator:
    candidates = [
        '[data-test="user-menu"]',
        '#dropdownUser',
        'button#dropdownUser',
        lambda p: p.get_by_role("button", name=re.compile(r"Joanne", re.I)),
    ]
    for sel in candidates:
        loc = sel(page) if callable(sel) else page.locator(sel)
        if loc.count() > 0:
            return loc.first
    raise AssertionError("No encontré el botón de menú de usuario.")

def wait_on_call(page: Page, timeout_ms: int = 60_000) -> None:
    """Espera a un ancla de estado 'On Call' (ajustá a lo que muestre tu UI)."""
    anchors = [
        '[data-test="state-oncall"]',
        '#stateOnCall',
        lambda p: p.get_by_text("On Call", exact=False),
        lambda p: p.get_by_text("En llamada", exact=False),
        # agrega acá otro texto/selector confiable si aplica
    ]
    last_err = None
    for sel in anchors:
        try:
            loc = sel(page) if callable(sel) else page.locator(sel)
            expect(loc).to_be_visible(timeout=timeout_ms)
            return
        except Exception as e:
            last_err = e
            continue
    raise AssertionError(f"No se detectó estado 'On Call' con los selectores previstos: {last_err}")

# ---------- fixtures ----------

@pytest.fixture(scope="session")
def pw_browser():
    """Lanza Chromium con flags de WebRTC fake y lo cierra al final de la sesión."""
    with sync_playwright() as p:
        args = ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"]
        if FAKE_AUDIO:
            args.append(f"--use-file-for-fake-audio-capture={FAKE_AUDIO}")
        browser = p.chromium.launch(headless=False, args=args)
        yield p, browser
        browser.close()

@pytest.fixture()
def page(pw_browser):
    """Crea un contexto por test, concede permisos de mic y devuelve la page."""
    p, browser = pw_browser
    ctx = browser.new_context(ignore_https_errors=True)
    ctx.grant_permissions(["microphone"], origin=APP_ORIGIN)  # evita prompt
    page = ctx.new_page()
    yield page
    ctx.close()

# ---------- test ----------

@pytest.mark.parametrize("username,password", [("ag1", "098098ZZZ")])
def test_attend_dialer(page: Page, username, password):
    # Login
    page.goto(f"{APP_ORIGIN}/accounts/login/")
    page.locator("#id_username").fill(username)
    page.locator("#id_password").fill(password)
    page.get_by_role("button", name=re.compile(r"^Log In$", re.I)).click()

    # Paso intermedio (si aparece)
    try:
        expect(page.get_by_text("User Password Log In")).to_be_visible(timeout=1000)
        page.get_by_text("User Password Log In").click()
    except Exception:
        pass

    # Ancla de carga
    page.wait_for_load_state("networkidle")

    # ---- ciclo: Hangup → espera Resume → Resume → espera On Call ----
    HANGUP_RESUME_CYCLES = 4
    for i in range(HANGUP_RESUME_CYCLES):
        # Hangup
        hangup = hangup_btn(page)
        expect(hangup).to_be_visible(timeout=60_000)
        expect(hangup).to_be_enabled(timeout=60_000)
        hangup.click()

        # Resume (espera habilitado)
        resume = resume_btn(page)
        expect(resume).to_be_visible(timeout=60_000)
        expect(resume).to_be_enabled(timeout=60_000)
        resume.click()

        # Esperar a que el softphone vuelva a estado "On Call"
        wait_on_call(page, timeout_ms=60_000)

    # Menú de usuario (3 clicks como en tu flujo)
    user_menu = open_user_menu_btn(page)
    for _ in range(3):
        expect(user_menu).to_be_visible(timeout=30_000)
        user_menu.click()

    # Exit
    page.get_by_role("link", name=re.compile(r"^Exit$", re.I)).click()
