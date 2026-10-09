"""Abre Chromium, inicia sesión en OMniLeads y deja la consola abierta.

El permiso de micrófono se concede antes de cargar la consola, porque el
agente llama a getUserMedia al arrancar el webphone.
"""
import os

from playwright.sync_api import sync_playwright

APP_ORIGIN = os.getenv("OML_ORIGIN", "https://omnileads.sephir.tech")
USERNAME = os.getenv("OML_USERNAME", "ag1")
PASSWORD = os.getenv("OML_PASSWORD", "098098ZZZ")


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            headless=False,
            args=[
                "--use-fake-ui-for-media-stream",
                "--autoplay-policy=no-user-gesture-required",
            ],
        )
        context = browser.new_context(ignore_https_errors=True)
        context.grant_permissions(["microphone"], origin=APP_ORIGIN)
        page = context.new_page()
        page.on("dialog", lambda dialog: dialog.accept())

        page.goto(f"{APP_ORIGIN}/accounts/login/")
        page.locator("#id_username").fill(USERNAME)
        page.locator("#id_password").fill(PASSWORD)
        page.locator("button[type='submit']").click()

        # Algunas instalaciones muestran un paso extra de método de login.
        extra = page.get_by_text("User Password Log In")
        try:
            extra.wait_for(state="visible", timeout=1500)
            extra.click()
        except Exception:
            pass

        page.locator("#numberToCall").wait_for(state="visible", timeout=60_000)
        print("Sesión abierta. Cerrá el navegador o presioná Ctrl+C para salir.")
        try:
            page.wait_for_event("close", timeout=0)
        except KeyboardInterrupt:
            pass
        finally:
            browser.close()


if __name__ == "__main__":
    main()
