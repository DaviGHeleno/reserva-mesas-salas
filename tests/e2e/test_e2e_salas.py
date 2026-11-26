from datetime import date, timedelta

from playwright.sync_api import Page, expect

DIA_FUTURO = (date.today() + timedelta(days=7)).isoformat()


def abrir_aba_salas(page: Page, url: str, nome: str) -> None:
    page.goto(url)
    page.get_by_test_id("employee").fill(nome)
    page.get_by_test_id("employee").dispatch_event("change")
    page.get_by_test_id("tab-rooms").click()


def test_sala_com_fim_antes_do_inicio_mostra_erro(page: Page, server_url):
    abrir_aba_salas(page, server_url, "Carla E2E")
    page.get_by_test_id("room-day").fill(DIA_FUTURO)
    page.get_by_test_id("room-start").fill("11:00")
    page.get_by_test_id("room-end").fill("10:00")
    page.get_by_test_id("room-book").click()
    expect(page.get_by_test_id("message")).to_contain_text("fim deve ser depois")


def test_reservar_sala_e_depois_cancelar(page: Page, server_url):
    abrir_aba_salas(page, server_url, "Diego E2E")
    page.get_by_test_id("room-floor").select_option("2")
    expect(page.get_by_test_id("room-select").locator("option")).to_have_count(2)
    page.get_by_test_id("room-select").select_option("S2-1")
    page.get_by_test_id("room-day").fill(DIA_FUTURO)
    page.get_by_test_id("room-start").fill("14:00")
    page.get_by_test_id("room-end").fill("15:00")
    page.get_by_test_id("room-title").fill("Planejamento")
    page.get_by_test_id("room-book").click()
    expect(page.get_by_test_id("message")).to_contain_text("Sala S2-1 reservada")
    expect(page.get_by_test_id("room-schedule")).to_contain_text("14:00–15:00")

    page.get_by_test_id("tab-mine").click()
    minhas = page.get_by_test_id("my-bookings")
    expect(minhas).to_contain_text("Sala S2-1")
    minhas.get_by_role("button", name="Cancelar").first.click()
    expect(page.get_by_test_id("message")).to_contain_text("cancelada")
    expect(minhas).not_to_contain_text("Sala S2-1")