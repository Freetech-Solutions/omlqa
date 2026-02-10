import pytest
from playwright.sync_api import Page, expect

# --- CONFIGURACIÓN: Parámetros de pytest ---
def pytest_addoption(parser):
    """Agrega el parámetro --oml-host para recibir el host desde la línea de comandos"""
    parser.addoption(
        "--oml-host",
        action="store",
        default="localhost",
        help="Host de OML para las pruebas (ej: localhost, oml.example.com)"
    )

@pytest.fixture(scope="function")
def oml_host(request):
    """Fixture que lee el parámetro --oml-host de pytest"""
    return request.config.getoption("--oml-host")

# --- FIXTURE: Configuración del Navegador ---
@pytest.fixture(scope="function")
def context(browser):
    # Creamos un contexto con permisos de micrófono otorgados
    # y argumentos para simular dispositivos de audio (fake audio)
    # ignore_https_errors=True permite aceptar certificados SSL self-signed
    context = browser.new_context(
        permissions=["microphone"],
        user_agent="Playwright-Tester-Bot",
        ignore_https_errors=True
    )
    yield context
    context.close()

@pytest.fixture(scope="function")
def page(context, oml_host):
    page = context.new_page()
    # Ir a la URL de login
    login_url = f"https://{oml_host}/accounts/login/"
    page.goto(login_url)
    
    # --- LOGIN ---
    # Llenar campo de usuario
    page.fill("#id_username", "ag1")
    # Llenar campo de contraseña
    page.fill("#id_password", "098098ZZZ")
    # Hacer click en el botón de submit
    page.click("button[type='submit']")
    
    # Esperar a que se complete el login y redirija a la consola de agente
    # Esperamos a que el webphone esté disponible
    page.wait_for_selector("#numberToCall", timeout=10000)
    
    return page

# --- HELPER FUNCTIONS (Page Object Model simplificado) ---
def dial_number(page: Page, number: str):
    """Escribe el número y presiona llamar"""
    # Limpiar input si existe
    dial_input = page.locator("#numberToCall")
    dial_input.clear()
    dial_input.fill(number)
    
    # Click en botón llamar
    page.click("#call")

def assert_status(page: Page, status_text: str, timeout=5000):
    """Verifica que aparezca un estado en la pantalla (Ringing, Busy, etc)"""
    # Intentar primero con #CallStatus, si no existe usar #SipStatus
    status_display = page.locator("#CallStatus, #SipStatus").first()
    expect(status_display).to_contain_text(status_text, timeout=timeout)

# --- ESCENARIOS DE PRUEBA ---

def test_dial_and_cancel(page: Page):
    """
    Escenario 1: Discar 123456785 y cancelar la llamada
    """
    target_number = "123456785"
    
    print(f"📞 Discando {target_number}...")
    dial_number(page, target_number)
    
    # Esperar que esté sonando
    assert_status(page, "Ringing") 
    
    # Esperar 2 segundos simulando que el usuario se arrepiente
    page.wait_for_timeout(2000)
    
    print("❌ Cancelando llamada...")
    page.click("#endCall") # Botón de colgar
    
    # Verificar que volvimos al estado inicial o idle
    assert_status(page, "Ready")

def test_dial_and_no_answer_bye(page: Page):
    """
    Escenario 2: Discar 123456785 y esperar el BYE del otro lado (Timeout)
    """
    target_number = "123456785"
    
    dial_number(page, target_number)
    assert_status(page, "Ringing")
    
    print("⏳ Esperando que el sistema corte (Simulando No Answer)...")
    # Aquí esperamos que el backend mande el BYE o un 408 Request Timeout
    # Aumentamos el timeout porque esto puede tardar (ej. 30 seg)
    assert_status(page, "Call Ended", timeout=35000) 

def test_dial_busy(page: Page):
    """
    Escenario 3: Discar 123456780 y esperar BUSY
    """
    target_number = "123456780"
    
    dial_number(page, target_number)
    
    print("⏳ Esperando señal de Ocupado...")
    # El cambio de estado debe ser casi inmediato o en pocos segundos
    assert_status(page, "Busy")
    
    # Opcional: Verificar si reproduce tono de ocupado o muestra mensaje de error
    # expect(page.locator(".error-msg")).to_have_text("User Busy")

def test_short_call(page: Page):
    """
    Escenario 4: Discar 123456781, conectar y esperar corte (Short Call)
    """
    target_number = "123456781"
    
    dial_number(page, target_number)
    
    # Esperar conexión
    assert_status(page, "Connected")
    print("✅ Llamada conectada")
    
    # Esperar que el audio termine o el otro lado corte
    assert_status(page, "Call Ended", timeout=10000)

def test_dial_and_hangup_after_10s(page: Page):
    """
    Escenario 5: Discar 123456784 y colgar después de 10 segundos
    """
    target_number = "123456784"
    
    print(f"📞 Discando {target_number}...")
    dial_number(page, target_number)
    
    # Esperar a que aparezca algún estado de llamada (Ringing o Connected)
    # Usamos un timeout corto para verificar que la llamada inició
    try:
        assert_status(page, "Ringing", timeout=5000)
        print("🔔 Llamada sonando...")
    except:
        # Si no aparece Ringing, puede que ya esté Connected
        try:
            assert_status(page, "Connected", timeout=5000)
            print("✅ Llamada conectada...")
        except:
            print("⚠️ No se pudo verificar el estado inicial de la llamada")
    
    # Esperar 10 segundos
    print("⏳ Esperando 10 segundos...")
    page.wait_for_timeout(10000)
    
    # Colgar la llamada
    print("❌ Colgando llamada...")
    page.click("#endCall")
    
    # Verificar que la llamada terminó
    assert_status(page, "Ready", timeout=5000)
    print("✅ Llamada finalizada correctamente")