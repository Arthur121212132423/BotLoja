import discord
from discord.ext import commands, tasks
from discord.ui import View, Modal, TextInput
import requests
import io
import json
import os
import uuid
import asyncio
import base64


# =========================================================
# TOKENS — CONFIGURAR NAS ENVIRONMENT VARIABLES
# =========================================================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN")


# =========================================================
# CONFIGURAÇÕES
# =========================================================

NOME_LOJA = "Tk Otimização"

LINK_ANYDESK = "https://anydesk.com/pt/downloads"

ARQUIVO_PAGAMENTOS = "pagamentos.json"


# =========================================================
# IMAGENS DO TUTORIAL
#
# COLOQUE AQUI OS LINKS DAS IMAGENS
#
# Se deixar "" o bot simplesmente não mostra aquela imagem.
# =========================================================

TUTORIAL_IMG_1 = ""
TUTORIAL_IMG_2 = ""
TUTORIAL_IMG_3 = ""


# =========================================================
# CANAIS
# =========================================================

CANAL_OTIMIZACAO = 1544128197417771098
CANAL_VITALICIA = 1544128250635358240
CANAL_CURSO = 1544128281408839792
CANAL_INFORMACOES = 1544129948359327794
CANAL_FEEDBACK = 1489876080771727473


# =========================================================
# CARGOS
# =========================================================

CARGO_COMUM = 1489876079840591935

CARGO_OTIMIZACAO = 1539751475876597890
CARGO_VITALICIA = 1544129229883445299
CARGO_CURSO = 1544128542487355392


# =========================================================
# PRODUTOS
# =========================================================

PRODUTOS = {
    "basica": {
        "nome": "Otimização Básica",
        "preco": 15.00,
        "cargos": [
            CARGO_COMUM,
            CARGO_OTIMIZACAO
        ]
    },

    "completa": {
        "nome": "Otimização Completa",
        "preco": 30.00,
        "cargos": [
            CARGO_COMUM,
            CARGO_OTIMIZACAO
        ]
    },

    "vitalicia": {
        "nome": "Otimização Completa Vitalícia",
        "preco": 60.00,
        "cargos": [
            CARGO_COMUM,
            CARGO_VITALICIA
        ]
    },

    "curso": {
        "nome": "Aprenda a Otimizar",
        "preco": 100.00,
        "cargos": [
            CARGO_COMUM,
            CARGO_CURSO
        ]
    }
}


# =========================================================
# INTENTS
# =========================================================

intents = discord.Intents.default()

intents.guilds = True
intents.members = True
intents.message_content = True


# =========================================================
# PAGAMENTOS
# =========================================================

def carregar_pagamentos():

    if not os.path.exists(ARQUIVO_PAGAMENTOS):
        return {}

    try:

        with open(
            ARQUIVO_PAGAMENTOS,
            "r",
            encoding="utf-8"
        ) as arquivo:

            return json.load(arquivo)

    except Exception as erro:

        print(
            "❌ Erro carregando pagamentos:",
            erro
        )

        return {}


pagamentos = carregar_pagamentos()


def salvar_pagamentos():

    try:

        with open(
            ARQUIVO_PAGAMENTOS,
            "w",
            encoding="utf-8"
        ) as arquivo:

            json.dump(
                pagamentos,
                arquivo,
                indent=4,
                ensure_ascii=False
            )

    except Exception as erro:

        print(
            "❌ Erro salvando pagamentos:",
            erro
        )


# =========================================================
# MERCADO PAGO — CRIAR PIX
# =========================================================

def criar_pagamento_pix(
    produto,
    preco,
    canal_id,
    usuario_id,
    email
):

    if not MERCADOPAGO_ACCESS_TOKEN:

        print(
            "❌ MERCADOPAGO_ACCESS_TOKEN não configurado."
        )

        return None

    url = "https://api.mercadopago.com/v1/payments"

    idempotency_key = str(uuid.uuid4())

    headers = {
        "Authorization":
            f"Bearer {MERCADOPAGO_ACCESS_TOKEN}",

        "Content-Type":
            "application/json",

        "X-Idempotency-Key":
            idempotency_key
    }

    external_reference = (
        f"discord_{canal_id}_"
        f"{usuario_id}_"
        f"{uuid.uuid4().hex[:8]}"
    )

    dados = {

        "transaction_amount":
            float(preco),

        "description":
            produto,

        "payment_method_id":
            "pix",

        "external_reference":
            external_reference,

        "payer": {
            "email": email
        }
    }

    try:

        resposta = requests.post(
            url,
            headers=headers,
            json=dados,
            timeout=30
        )

    except requests.RequestException as erro:

        print(
            "❌ Erro de conexão com Mercado Pago:",
            erro
        )

        return None

    if resposta.status_code not in [200, 201]:

        print(
            "❌ ERRO MERCADO PAGO:",
            resposta.status_code
        )

        print(resposta.text)

        return None

    try:

        pagamento = resposta.json()

    except Exception:

        print(
            "❌ Mercado Pago retornou resposta inválida."
        )

        return None

    transaction_data = (
        pagamento
        .get("point_of_interaction", {})
        .get("transaction_data", {})
    )

    return {

        "id":
            str(pagamento["id"]),

        "status":
            pagamento.get(
                "status",
                "pending"
            ),

        "external_reference":
            external_reference,

        "qr_code":
            transaction_data.get(
                "qr_code"
            ),

        "qr_code_base64":
            transaction_data.get(
                "qr_code_base64"
            )
    }


# =========================================================
# CONSULTAR PAGAMENTO
# =========================================================

def consultar_pagamento(payment_id):

    if not MERCADOPAGO_ACCESS_TOKEN:
        return None

    url = (
        "https://api.mercadopago.com/v1/payments/"
        f"{payment_id}"
    )

    headers = {
        "Authorization":
            f"Bearer {MERCADOPAGO_ACCESS_TOKEN}"
    }

    try:

        resposta = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        if resposta.status_code != 200:

            print(
                "❌ Erro consultando pagamento:",
                resposta.status_code,
                resposta.text
            )

            return None

        dados = resposta.json()

        return dados.get("status")

    except Exception as erro:

        print(
            "❌ Erro consultando pagamento:",
            erro
        )

        return None


# =========================================================
# MODAL DE E-MAIL
# =========================================================

class EmailPagamentoModal(Modal):

    def __init__(self, produto_id):

        super().__init__(
            title="Pagamento via PIX"
        )

        self.produto_id = produto_id

        self.email = TextInput(
            label="Seu e-mail",
            placeholder="exemplo@email.com",
            required=True,
            max_length=100
        )

        self.add_item(self.email)

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        produto = PRODUTOS[self.produto_id]

        await interaction.response.defer(
            ephemeral=True
        )

        resultado = await asyncio.to_thread(
            criar_pagamento_pix,
            produto["nome"],
            produto["preco"],
            interaction.channel.id,
            interaction.user.id,
            self.email.value
        )

        if not resultado:

            await interaction.followup.send(
                "❌ Não consegui gerar o PIX.\n\n"
                "Verifique o Access Token do Mercado Pago.",
                ephemeral=True
            )

            return

        pagamento_id = resultado["id"]

        pagamentos[pagamento_id] = {

            "payment_id":
                pagamento_id,

            "channel_id":
                interaction.channel.id,

            "user_id":
                interaction.user.id,

            "produto_id":
                self.produto_id,

            "produto":
                produto["nome"],

            "preco":
                produto["preco"],

            "status":
                "pending"
        }

        salvar_pagamentos()

        pix = resultado.get("qr_code")

        if not pix:

            await interaction.followup.send(
                "❌ O Mercado Pago criou o pagamento, "
                "mas não retornou o código PIX.",
                ephemeral=True
            )

            return

        embed = discord.Embed(

            title="💳 PAGAMENTO VIA PIX",

            description=(
                f"📦 **Produto:** "
                f"{produto['nome']}\n\n"

                f"💰 **Valor:** "
                f"R${produto['preco']:.2f}\n\n"

                "🟡 **Status:** Aguardando pagamento\n\n"

                "Escaneie o QR Code ou use o "
                "**Pix Copia e Cola** abaixo."
            ),

            color=discord.Color.gold()
        )

        embed.add_field(
            name="📋 Pix Copia e Cola",
            value=f"```{pix}```",
            inline=False
        )

        embed.set_footer(
            text="A confirmação do pagamento é automática."
        )

        arquivo = None

        qr_base64 = resultado.get(
            "qr_code_base64"
        )

        if qr_base64:

            try:

                imagem = base64.b64decode(
                    qr_base64
                )

                arquivo = discord.File(
                    io.BytesIO(imagem),
                    filename="pix.png"
                )

                embed.set_image(
                    url="attachment://pix.png"
                )

            except Exception as erro:

                print(
                    "❌ Erro processando QR Code:",
                    erro
                )

        if arquivo:

            await interaction.channel.send(
                embed=embed,
                file=arquivo
            )

        else:

            await interaction.channel.send(
                embed=embed
            )

        await interaction.followup.send(
            "✅ PIX gerado!\n"
            "Agora é só realizar o pagamento.",
            ephemeral=True
        )


# =========================================================
# VIEW DO PAGAMENTO
# =========================================================

class PagamentoView(View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Pagar com PIX",
        emoji="💳",
        style=discord.ButtonStyle.success,
        custom_id="pagar_pix"
    )

    async def pagar_pix(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        produto_id = None

        topic = (
            interaction.channel.topic
            or ""
        )

        for chave in PRODUTOS:

            if (
                f"ProdutoID: {chave}"
                in topic
            ):

                produto_id = chave
                break

        if not produto_id:

            await interaction.response.send_message(
                "❌ Não consegui identificar o produto.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            EmailPagamentoModal(produto_id)
        )


# =========================================================
# VIEW DO TICKET
#
# PAGAMENTO + FECHAR TICKET NO MESMO PAINEL
# =========================================================

class TicketView(View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Pagar com PIX",
        emoji="💳",
        style=discord.ButtonStyle.success,
        custom_id="ticket_pagar_pix"
    )

    async def pagar_pix(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        produto_id = None

        topic = (
            interaction.channel.topic
            or ""
        )

        for chave in PRODUTOS:

            if (
                f"ProdutoID: {chave}"
                in topic
            ):

                produto_id = chave
                break

        if not produto_id:

            await interaction.response.send_message(
                "❌ Não consegui identificar o produto.",
                ephemeral=True
            )

            return

        await interaction.response.send_modal(
            EmailPagamentoModal(produto_id)
        )

    @discord.ui.button(
        label="Fechar Ticket",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="ticket_fechar"
    )

    async def fechar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not interaction.user.guild_permissions.manage_channels:

            await interaction.response.send_message(
                "❌ Apenas a equipe pode fechar este ticket.",
                ephemeral=True
            )

            return

        await interaction.response.send_message(
            "🔒 Este ticket será fechado em 5 segundos."
        )

        await asyncio.sleep(5)

        try:

            await interaction.channel.delete(
                reason="Ticket fechado"
            )

        except discord.NotFound:

            pass


# =========================================================
# ANYDESK — INFORMAR ID
# =========================================================

class AnyDeskModal(Modal):

    def __init__(self):

        super().__init__(
            title="Informar ID do AnyDesk"
        )

        self.anydesk_id = TextInput(
            label="ID do AnyDesk",
            placeholder="Ex: 1749 954 265",
            required=True,
            min_length=3,
            max_length=30
        )

        self.add_item(
            self.anydesk_id
        )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):

        embed = discord.Embed(

            title="🖥️ ID DO ANYDESK RECEBIDO",

            description=(
                f"👤 **Cliente:** "
                f"{interaction.user.mention}\n\n"

                f"🔢 **ID do AnyDesk:** "
                f"`{self.anydesk_id.value}`\n\n"

                "✅ Seu ID foi enviado para a equipe.\n"
                "Aguarde o atendimento."
            ),

            color=discord.Color.green()
        )

        await interaction.channel.send(
            embed=embed
        )

        await interaction.response.send_message(
            "✅ Seu ID foi enviado para a equipe!",
            ephemeral=True
        )


# =========================================================
# TUTORIAL ANYDESK
# =========================================================

class AnyDeskTutorialView(View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Baixar AnyDesk",
        emoji="📥",
        style=discord.ButtonStyle.link,
        url=LINK_ANYDESK
    )

    async def baixar_anydesk(
        self,
        interaction,
        button
    ):
        pass

    @discord.ui.button(
        label="Informar meu ID",
        emoji="🔢",
        style=discord.ButtonStyle.primary,
        custom_id="tutorial_informar_id"
    )

    async def informar_id(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.send_modal(
            AnyDeskModal()
        )


# =========================================================
# CRIAR EMBED DO TUTORIAL
# =========================================================

def criar_tutorial_embed():

    embed = discord.Embed(

        title="🖥️ ACESSO LIBERADO — TUTORIAL ANYDESK",

        description=(
            "Seu pagamento foi **confirmado com sucesso!** 🎉\n\n"

            "Agora siga os passos abaixo para realizar "
            "a otimização do seu computador.\n\n"

            "**1️⃣ Baixe o AnyDesk**\n"
            "Clique no botão **Baixar AnyDesk** abaixo "
            "e faça o download pelo site oficial.\n\n"

            "**2️⃣ Abra o AnyDesk**\n"
            "Depois de baixar, abra o programa.\n\n"

            "**3️⃣ Localize seu ID**\n"
            "Na tela principal do AnyDesk aparecerá "
            "um número grande escrito como "
            "**'Este dispositivo'**.\n\n"

            "**4️⃣ Envie seu ID**\n"
            "Clique em **Informar meu ID** e coloque "
            "o número que aparece no seu AnyDesk.\n\n"

            "📌 **Exemplo:**\n"
            "`1749 954 265`\n\n"

            "Depois de enviar, aguarde nossa equipe."
        ),

        color=discord.Color.green()
    )

    embed.add_field(
        name="📥 Download",
        value=(
            "Use o botão abaixo para acessar "
            "o download oficial do AnyDesk."
        ),
        inline=False
    )

    embed.add_field(
        name="🔢 Onde vejo meu ID?",
        value=(
            "Abra o AnyDesk e procure o número grande "
            "na parte principal do programa."
        ),
        inline=False
    )

    embed.add_field(
        name="📋 Depois de encontrar",
        value=(
            "Clique em **Informar meu ID** e envie "
            "o número para nossa equipe."
        ),
        inline=False
    )

    embed.set_footer(
        text=f"{NOME_LOJA} • Atendimento"
    )

    return embed


# =========================================================
# CRIAR TICKET
# =========================================================

async def criar_ticket(
    interaction,
    produto_id
):

    produto = PRODUTOS[produto_id]

    guild = interaction.guild
    membro = interaction.user

    # -----------------------------------------------------
    # VERIFICAR SE JÁ POSSUI TICKET
    # -----------------------------------------------------

    for canal in guild.text_channels:

        if canal.topic:

            if (
                f"Cliente: {membro.id}"
                in canal.topic
            ):

                await interaction.response.send_message(
                    f"❌ Você já possui um ticket: "
                    f"{canal.mention}",
                    ephemeral=True
                )

                return

    # -----------------------------------------------------
    # CATEGORIA
    # -----------------------------------------------------

    categoria = interaction.channel.category

    # -----------------------------------------------------
    # PERMISSÕES
    # -----------------------------------------------------

    overwrites = {

        guild.default_role:
            discord.PermissionOverwrite(
                view_channel=False
            ),

        membro:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            ),

        guild.me:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
                manage_messages=True
            )
    }

    # -----------------------------------------------------
    # CRIAR CANAL
    # -----------------------------------------------------

    canal = await guild.create_text_channel(

        name="🟡・aguardando-pagamento",

        category=categoria,

        topic=(
            f"Cliente: {membro.id} | "
            f"ProdutoID: {produto_id}"
        ),

        overwrites=overwrites,

        reason=f"Compra: {produto['nome']}"
    )

    # -----------------------------------------------------
    # PAINEL DO PEDIDO
    # -----------------------------------------------------

    embed = discord.Embed(

        title="🛒 PEDIDO",

        description=(
            f"Olá, {membro.mention}! 👋\n\n"

            f"📦 **Produto:** "
            f"{produto['nome']}\n"

            f"💰 **Valor:** "
            f"R${produto['preco']:.2f}\n\n"

            "🟡 **Status:** Aguardando pagamento\n\n"

            "Clique em **Pagar com PIX** para gerar "
            "seu pagamento.\n\n"

            "🔒 Caso precise cancelar, a equipe pode "
            "fechar o ticket pelo botão abaixo."
        ),

        color=discord.Color.gold()
    )

    embed.set_footer(
        text=f"{NOME_LOJA} • Pagamento seguro via PIX"
    )

    # -----------------------------------------------------
    # UM ÚNICO PAINEL
    # -----------------------------------------------------

    await canal.send(
        content=membro.mention,
        embed=embed,
        view=TicketView()
    )

    # -----------------------------------------------------
    # CONFIRMAÇÃO
    # -----------------------------------------------------

    await interaction.response.send_message(
        f"✅ Seu ticket foi criado: {canal.mention}",
        ephemeral=True
    )


# =========================================================
# PAINEL OTIMIZAÇÃO
# =========================================================

class OtimizacaoView(View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Otimização Básica — R$15,00",
        emoji="⚙️",
        style=discord.ButtonStyle.primary,
        custom_id="otimizacao_basica"
    )

    async def basica(
        self,
        interaction,
        button
    ):

        await criar_ticket(
            interaction,
            "basica"
        )

    @discord.ui.button(
        label="Otimização Completa — R$30,00",
        emoji="🚀",
        style=discord.ButtonStyle.success,
        custom_id="otimizacao_completa"
    )

    async def completa(
        self,
        interaction,
        button
    ):

        await criar_ticket(
            interaction,
            "completa"
        )


# =========================================================
# PAINEL VITALÍCIA
# =========================================================

class VitaliciaView(View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Otimização Completa Vitalícia — R$60,00",
        emoji="♾️",
        style=discord.ButtonStyle.success,
        custom_id="otimizacao_vitalicia"
    )

    async def vitalicia(
        self,
        interaction,
        button
    ):

        await criar_ticket(
            interaction,
            "vitalicia"
        )


# =========================================================
# PAINEL CURSO
# =========================================================

class CursoView(View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Aprenda a Otimizar — R$100,00",
        emoji="🎓",
        style=discord.ButtonStyle.primary,
        custom_id="curso_otimizacao"
    )

    async def curso(
        self,
        interaction,
        button
    ):

        await criar_ticket(
            interaction,
            "curso"
        )


# =========================================================
# VERIFICAR PAGAMENTOS
# =========================================================

@tasks.loop(seconds=10)
async def verificar_pagamentos():

    if not pagamentos:
        return

    alterou = False

    for payment_id, dados in list(
        pagamentos.items()
    ):

        if dados.get("status") == "approved":
            continue

        status = await asyncio.to_thread(
            consultar_pagamento,
            payment_id
        )

        if status != "approved":
            continue

        # -------------------------------------------------
        # PAGAMENTO APROVADO
        # -------------------------------------------------

        dados["status"] = "approved"

        alterou = True

        canal = bot.get_channel(
            int(dados["channel_id"])
        )

        if not canal:
            continue

        guild = canal.guild

        membro = guild.get_member(
            int(dados["user_id"])
        )

        if not membro:
            continue

        produto = PRODUTOS[
            dados["produto_id"]
        ]

        cargos = []

        # -------------------------------------------------
        # ENTREGAR CARGOS
        # -------------------------------------------------

        for cargo_id in produto["cargos"]:

            cargo = guild.get_role(
                cargo_id
            )

            if not cargo:
                print(
                    f"⚠️ Cargo não encontrado: {cargo_id}"
                )

                continue

            try:

                await membro.add_roles(
                    cargo,
                    reason="Pagamento PIX aprovado"
                )

                cargos.append(
                    cargo.mention
                )

            except discord.Forbidden:

                print(
                    f"❌ Não consegui entregar "
                    f"{cargo.name}"
                )

            except Exception as erro:

                print(
                    f"❌ Erro entregando cargo "
                    f"{cargo.name}: {erro}"
                )

        # -------------------------------------------------
        # MUDAR NOME DO TICKET
        # -------------------------------------------------

        try:

            await canal.edit(
                name="🟢・pago"
            )

        except Exception as erro:

            print(
                "❌ Erro alterando nome do canal:",
                erro
            )

        # -------------------------------------------------
        # EMBED DE PAGAMENTO APROVADO
        # -------------------------------------------------

        embed = discord.Embed(

            title="🟢 PAGAMENTO APROVADO!",

            description=(
                f"Parabéns, {membro.mention}! 🎉\n\n"

                "Seu pagamento foi confirmado "
                "**automaticamente**.\n\n"

                f"📦 **Produto:** "
                f"{produto['nome']}\n"

                f"💰 **Valor:** "
                f"R${produto['preco']:.2f}\n\n"

                "🎁 Seu acesso já foi liberado.\n\n"

                "Agora siga o tutorial abaixo para "
                "baixar e configurar o AnyDesk."
            ),

            color=discord.Color.green()
        )

        if cargos:

            embed.add_field(

                name="🎁 Cargos liberados",

                value="\n".join(cargos),

                inline=False
            )

        embed.set_footer(
            text=f"{NOME_LOJA} • Pagamento confirmado"
        )

        try:

            await canal.send(
                embed=embed
            )

        except Exception as erro:

            print(
                "❌ Erro enviando aprovação:",
                erro
            )

        # -------------------------------------------------
        # TUTORIAL ANYDESK
        # -------------------------------------------------

        tutorial_embed = criar_tutorial_embed()

        # -------------------------------------------------
        # IMAGENS
        #
        # Envia até 3 imagens configuradas.
        # -------------------------------------------------

        imagens = [
            TUTORIAL_IMG_1,
            TUTORIAL_IMG_2,
            TUTORIAL_IMG_3
        ]

        imagens_validas = [
            imagem
            for imagem in imagens
            if imagem
        ]

        if imagens_validas:

            # Primeira imagem no próprio embed
            tutorial_embed.set_image(
                url=imagens_validas[0]
            )

        try:

            await canal.send(
                embed=tutorial_embed,
                view=AnyDeskTutorialView()
            )

        except Exception as erro:

            print(
                "❌ Erro enviando tutorial:",
                erro
            )

        # -------------------------------------------------
        # ENVIAR IMAGENS EXTRAS
        # -------------------------------------------------

        for imagem_url in imagens_validas[1:]:

            try:

                imagem_embed = discord.Embed(
                    color=discord.Color.blurple()
                )

                imagem_embed.set_image(
                    url=imagem_url
                )

                await canal.send(
                    embed=imagem_embed
                )

            except Exception as erro:

                print(
                    "❌ Erro enviando imagem do tutorial:",
                    erro
                )

    if alterou:

        salvar_pagamentos()


# =========================================================
# BOT
# =========================================================

class LojaBot(commands.Bot):

    def __init__(self):

        super().__init__(
            command_prefix="!",
            intents=intents
        )

    async def setup_hook(self):

        # -------------------------------------------------
        # BOTÕES PERSISTENTES
        # -------------------------------------------------

        self.add_view(
            OtimizacaoView()
        )

        self.add_view(
            VitaliciaView()
        )

        self.add_view(
            CursoView()
        )

        self.add_view(
            PagamentoView()
        )

        self.add_view(
            TicketView()
        )

        self.add_view(
            AnyDeskTutorialView()
        )

        # -------------------------------------------------
        # PAGAMENTOS
        # -------------------------------------------------

        if not verificar_pagamentos.is_running():

            verificar_pagamentos.start()

        print(
            "✅ Botões persistentes carregados!"
        )


bot = LojaBot()


# =========================================================
# ON READY
# =========================================================

@bot.event
async def on_ready():

    print("")
    print("========================================")
    print(
        f"🤖 Bot conectado como {bot.user}"
    )
    print("========================================")
    print(
        "💳 Sistema PIX automático online!"
    )
    print(
        "🔄 Verificação de pagamentos a cada 10 segundos."
    )

    if TUTORIAL_IMG_1:
        print("🖼️ Imagem 1 do tutorial configurada.")

    if TUTORIAL_IMG_2:
        print("🖼️ Imagem 2 do tutorial configurada.")

    if TUTORIAL_IMG_3:
        print("🖼️ Imagem 3 do tutorial configurada.")


# =========================================================
# INICIAR
# =========================================================

if __name__ == "__main__":

    if not DISCORD_TOKEN:

        print("")
        print(
            "❌ DISCORD_TOKEN não configurado."
        )

        print(
            "Configure DISCORD_TOKEN nas "
            "Environment Variables."
        )

        print("")

    elif not MERCADOPAGO_ACCESS_TOKEN:

        print("")
        print(
            "❌ MERCADOPAGO_ACCESS_TOKEN "
            "não configurado."
        )

        print(
            "Configure MERCADOPAGO_ACCESS_TOKEN "
            "nas Environment Variables."
        )

        print("")

    else:

        print("")
        print(
            "✅ Token do Discord configurado."
        )

        print(
            "✅ Access Token do Mercado Pago configurado."
        )

        print(
            "🚀 Iniciando bot..."
        )

        print("")

        bot.run(
            DISCORD_TOKEN
        )
