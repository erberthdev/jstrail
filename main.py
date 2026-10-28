from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Input, ListView, ListItem, Label, Static
from textual.widget import Widget
from textual.theme import Theme


COMANDOS = {
    "/help": {
        "tipo": "comando",
        "descricao": "Mostra a lista de comandos",
        "parametros": None,
    },

    "/clear": {
        "tipo": "comando",
        "descricao": "Limpa o terminal",
        "parametros": None,
    },

    "/event": {
        "tipo": "evento",
        "descricao": "Executa um evento",
        "parametros": "<nome>",
    },

    "/scan": {
        "tipo": "comando",
        "descricao": "Inicia uma varredura",
        "parametros": "<alvo>",
    },
}


class Aviso(Widget):

    def render(self):
        return (
            "     ██╗███████╗████████╗██████╗  █████╗ ██╗██╗          \n"
            "     ██║██╔════╝╚══██╔══╝██╔══██╗██╔══██╗██║██║          \n"
            "     ██║███████╗   ██║   ██████╔╝███████║██║██║          \n"
            "██   ██║╚════██║   ██║   ██╔══██╗██╔══██║██║██║          \n"
            "╚█████╔╝███████║   ██║   ██║  ██║██║  ██║██║███████╗\n"
            " ╚════╝ ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚══════╝\n\n"
            "[b]⚠ AVISO DE USO[/b]\n\n"
            "Esta ferramenta deve ser utilizada apenas\n"
            "em sistemas próprios ou com autorização.\n\n"
            "[b]Pressione ENTER para continuar.[/b]"
        )


class jstrailapp(App):

    CSS_PATH = "mensagem.tcss"

    def compose(self) -> ComposeResult:

        yield Header()

        yield Aviso(id="aviso")

        # Área onde aparecem as respostas
        yield Static(
            "",
            id="saida"
        )

        yield Input(
            placeholder="Digite seu comando...",
            id="entrada"
        )

        yield ListView(
            id="sugestoes"
        )

        yield Footer()

    def on_mount(self):

        self.register_theme(
            Theme(
                name="jstrail",
                primary="#ff8c00",
                secondary="#000000",
                accent="#ff8c00",
                warning="#ff8c00",
                error="#ff4500",
                success="#ffa500",
                foreground="#ffffff",
                background="#000000",
                surface="#1a1a1a",
                panel="#111111",
                dark=True,
            )
        )
        self.theme = "jstrail"

        self.aviso_ativo = True

        self.query_one("#entrada").display = False
        self.query_one("#sugestoes").display = False

        # Índice da sugestão selecionada
        self.sugestao_atual = 0

    # -----------------------------------
    # AVISO
    # -----------------------------------

    def on_key(self, event):

        if not self.aviso_ativo:
            return

        if event.key == "enter":

            self.aviso_ativo = False

            self.query_one("#aviso").remove()

            entrada = self.query_one("#entrada")
            entrada.display = True
            entrada.focus()

            event.stop()

    # -----------------------------------
    # AUTOCOMPLETE
    # -----------------------------------

    def on_input_changed(self, event: Input.Changed):

        texto = event.value
        sugestoes = self.query_one("#sugestoes")

        if not texto.startswith("/"):
            sugestoes.display = False
            return

        sugestoes.remove_children()

        encontrados = []

        for comando, dados in COMANDOS.items():

            if comando.startswith(texto):
                encontrados.append((comando, dados))

        if not encontrados:
            sugestoes.display = False
            return

        sugestoes.display = True

        self.sugestao_atual = 0

        for comando, dados in encontrados:

            parametro = dados.get("parametros")

            if parametro:
                nome = f"{comando} {parametro}"
            else:
                nome = comando

            sugestoes.mount(
                ListItem(
                    Label(
                        f"{nome}  "
                        f"[dim]{dados['tipo']}[/dim]  "
                        f"{dados['descricao']}"
                    )
                )
            )

        self.atualizar_selecao()

    # -----------------------------------
    # SELEÇÃO ↑ ↓
    # -----------------------------------

    def on_key(self, event):

        # Enquanto o aviso existir
        if self.aviso_ativo:

            if event.key == "enter":

                self.aviso_ativo = False

                self.query_one("#aviso").remove()

                entrada = self.query_one("#entrada")
                entrada.display = True
                entrada.focus()

                event.stop()

            return

        # Depois do aviso
        sugestoes = self.query_one("#sugestoes")

        if not sugestoes.display:
            return

        quantidade = len(sugestoes.children)

        if quantidade == 0:
            return

        # ↓
        if event.key == "down":

            self.sugestao_atual += 1

            if self.sugestao_atual >= quantidade:
                self.sugestao_atual = 0

            self.atualizar_selecao()

            event.stop()

        # ↑
        elif event.key == "up":

            self.sugestao_atual -= 1

            if self.sugestao_atual < 0:
                self.sugestao_atual = quantidade - 1

            self.atualizar_selecao()

            event.stop()

        # TAB
        elif event.key == "tab":

            self.completar_comando()

            event.stop()

    # -----------------------------------
    # DESTACAR SELEÇÃO
    # -----------------------------------

    def atualizar_selecao(self):

        sugestoes = self.query_one("#sugestoes")

        for i, item in enumerate(sugestoes.children):

            if i == self.sugestao_atual:
                item.add_class("selecionado")
            else:
                item.remove_class("selecionado")

    # -----------------------------------
    # TAB COMPLETA
    # -----------------------------------

    def completar_comando(self):

        sugestoes = self.query_one("#sugestoes")

        if not sugestoes.children:
            return

        item = sugestoes.children[self.sugestao_atual]

        texto = item.query_one(Label).renderable

        # Pega somente o comando
        comando = str(texto).split()[0]

        entrada = self.query_one("#entrada")

        entrada.value = comando
        entrada.cursor_position = len(comando)

    # -----------------------------------
    # ENTER DO INPUT
    # -----------------------------------

    def on_input_submitted(self, event: Input.Submitted):

        texto = event.value.strip()

        if not texto:
            return

        partes = texto.split()

        comando = partes[0]
        parametros = partes[1:]

        # CLEAR
        if comando == "/clear":

            self.query_one("#saida").update("")

            event.input.value = ""

            return

        # TESTE
        saida = self.query_one("#saida")

        saida.update(
            f"[b]Comando:[/b] {comando}\n"
            f"[b]Parâmetros:[/b] {parametros}"
        )

        event.input.value = ""


if __name__ == "__main__":
    jstrailapp().run()