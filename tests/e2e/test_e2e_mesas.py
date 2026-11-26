from playwright.sync_api import Page, expect


def abrir_site(page: Page, url: str, nome: str | None) -> None:
    page.goto(url)
    if nome:
        page.get_by_test_id("employee").fill(nome)
        page.get_by_test_id("employee").dispatch_event("change")


def reservar_primeiro_dia(page: Page, mesa: str, periodo: str) -> str:
    page.get_by_test_id(f"desk-{mesa}").click()
    primeiro = page.locator("#desk-days select").first
    dia = primeiro.get_attribute("data-day")
    primeiro.select_option(periodo)
    page.get_by_test_id("desk-book").click()
    return dia


def test_reservar_mesa_o_dia_inteiro_e_ver_em_minhas_reservas(page: Page, server_url):
    abrir_site(page, server_url, "Ana E2E")
    dia = reservar_primeiro_dia(page, "M1-01", "integral")
    expect(page.get_by_test_id("message")).to_contain_text("reservada")
    expect(page.get_by_test_id(f"period-{dia}")).to_have_count(0)
    page.get_by_test_id("tab-mine").click()
    expect(page.get_by_test_id("my-bookings")).to_contain_text("Mesa M1-01")


def test_reserva_de_manha_deixa_so_a_tarde_para_aquele_dia(page: Page, server_url):
    abrir_site(page, server_url, "Bruno E2E")
    dia = reservar_primeiro_dia(page, "M1-02", "manha")
    expect(page.get_by_test_id("message")).to_contain_text("reservada")
    opcoes = page.get_by_test_id(f"period-{dia}").locator("option")
    expect(opcoes).to_have_text(["Não reservar", "Tarde"])


def test_reservar_sem_informar_o_nome_mostra_erro(page: Page, server_url):
    abrir_site(page, server_url, None)
    reservar_primeiro_dia(page, "M1-03", "integral")
    expect(page.get_by_test_id("message")).to_contain_text("Informe o nome")