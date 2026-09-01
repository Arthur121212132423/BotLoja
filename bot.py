import asyncio
import base64
import io
import json
import os
import uuid
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

import discord
import requests
from discord.ext import commands, tasks
from discord.ui import Modal, TextInput, View


# =========================================================
# CONFIGURAÇÕES
# =========================================================

NOME_LOJA = "Tk Otimização"
LINK_ANYDESK = "https://anydesk.com/pt/downloads"
ARQUIVO_PAGAMENTOS = "pagamentos.json"

FUSO_BRASILIA = ZoneInfo("America/Sao_Paulo")
HORA_ABERTURA = 13
HORA_FECHAMENTO = 21


# =========================================================
# IDS DOS CANAIS
# =========================================================

CANAL_OTIMIZACAO = 1544128197417771098
CANAL_VITALICIA = 1544128250635358240
CANAL_CURSO = 1544128281408839792
CANAL_INFORMACOES = 1544129948359327794
CANAL_FEEDBACK = 1489876080771727473

CANAL_STATUS_LOJA = 1544187237648826408


# =========================================================
# IDS DOS CARGOS
# =========================================================

CARGO_COMUM = 1489876079840591935
CARGO_OTIMIZACAO = 1539751475876597890
CARGO_VITALICIA = 1544129229883445299
CARGO_CURSO = 1544128542487355392

CARGO_ATENDENTE = 1489876080260026461


# =========================================================
# IMAGENS DO TUTORIAL
# =========================================================

TUTORIAL_IMG_1 = (
    "https://media.discordapp.net/attachments/"
    "1544158860149915770/1544159894876463154/image.png"
    "?ex=6a977e78&is=6a962cf8&hm="
    "6c2d05f6e3874d750f4cc88c691f523889f15cdd190462dbaeaad4ee8759892e"
    "&=&format=webp&quality=lossless&width=1280&height=615"
)

TUTORIAL_IMG_2 = (
    "https://media.discordapp.net/attachments/"
    "1544158860149915770/1544159895291437097/image.png"
    "?ex=6a977e78&is=6a962cf8&hm="
    "cb1a80395a1b04d63786ae1b375220bea563499dc831138c2668fb783e9f70f4"
    "&=&format=webp&quality=lossless&width=1280&height=620"
)

TUTORIAL_IMG_3 = (
    "https://media.discordapp.net/attachments/"
    "1544158860149915770/1544159895677304952/image.png"
    "?ex=6a977e78&is=6a962cf8&hm="
    "b2a4056756e7f7d13f243c03a118ab81e2e4201d355b9d6bcdaf5aa847dff483"
    "&=&format=webp&quality=lossless&width=1280&height=683"
)


# =========================================================
# PRODUTOS
# =========================================================

PRODUTOS = {
    "basica": {
        "nome": "Otimização Básica",
        "preco": 15.00,
        "descricao": (
            "Uma otimização focada em melhorar o desempenho "
            "do seu computador e deixar seus jogos mais leves. "
            "São realizados ajustes para buscar melhor estabilidade, "
            "resposta e aproveitamento dos recursos do sistema."
        ),
        "cargos": [CARGO_COMUM, CARGO_OTIMIZACAO],
    },

    "completa": {
        "nome": "Otimização Completa",
        "preco": 30.00,
        "descricao": (
            "Uma otimização mais completa para quem busca extrair "
            "mais desempenho do computador. Inclui ajustes de sistema "
            "e configurações voltadas para desempenho, estabilidade "
            "e uma melhor experiência durante os jogos."
        ),
        "cargos": [CARGO_COMUM, CARGO_OTIMIZACAO],
    },

    "vitalicia": {
        "nome": "Otimização Completa Vitalícia",
        "preco": 60.00,
        "descricao": (
            "Tenha acesso à nossa otimização completa com suporte "
            "para futuras otimizações. Ideal para quem quer manter "
            "o computador sempre ajustado e contar com suporte "
            "quando forem necessárias novas configurações."
        ),
        "cargos": [CARGO_COMUM, CARGO_VITALICIA],
    },

    "curso": {
        "nome": "Aprenda a Otimizar",
        "preco": 100.00,
        "descricao": (
            "Aprenda a realizar suas próprias otimizações e entender "
            "melhor as configurações do computador. O curso foi pensado "
            "para quem quer aprender como melhorar o desempenho do PC "
            "e fazer ajustes de forma mais consciente."
        ),
        "cargos": [CARGO_COMUM, CARGO_CURSO],
    },
}


# =========================================================
# VARIÁVEIS DE AMBIENTE
# =========================================================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN")

if not DISCORD_TOKEN:
    print("❌ ERRO: DISCORD_TOKEN não configurado.")

if not MERCADOPAGO_ACCESS_TOKEN:
    print("⚠️ AVISO: MERCADOPAGO_ACCESS_TOKEN não configurado.")


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
        with open(ARQUIVO_PAGAMENTOS, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)

        return dados if isinstance(dados, dict) else {}

    except Exception as erro:
        print(f"❌ Erro carregando pagamentos: {erro}")
        return {}


pagamentos = carregar_pagamentos()


def salvar_pagamentos():
    try:
        arquivo_temporario = f"{ARQUIVO_PAGAMENTOS}.tmp"

        with open(arquivo_temporario, "w", encoding="utf-8") as arquivo:
            json.dump(
                pagamentos,
                arquivo,
                indent=4,
                ensure_ascii=False,
            )

        os.replace(
            arquivo_temporario,
            ARQUIVO_PAGAMENTOS,
        )

    except Exception as erro:
        print(f"❌ Erro salvando pagamentos: {erro}")


# =========================================================
# STATUS AUTOMÁTICO DA LOJA
# =========================================================

def loja_esta_aberta():
    agora = datetime.now(FUSO_BRASILIA)

    return (
        HORA_ABERTURA
        <= agora.hour
        < HORA_FECHAMENTO
    )


async def atualizar_status_loja():
    canal = bot.get_channel(CANAL_STATUS_LOJA)

    if canal is None:
        try:
            canal = await bot.fetch_channel(
                CANAL_STATUS_LOJA
            )

        except Exception as erro:
            print(
                f"❌ Não consegui encontrar o canal de status: {erro}"
            )
            return

    if not isinstance(canal, discord.TextChannel):
        print(
            f"❌ O ID {CANAL_STATUS_LOJA} não é um canal de texto."
        )
        return

    if loja_esta_aberta():
        novo_nome = "✅│Loja-on"
    else:
        novo_nome = "❌│Loja-off"

    if canal.name == novo_nome:
        return

    try:
        await canal.edit(
            name=novo_nome,
            reason="Atualização automática do funcionamento da loja",
        )

        agora = datetime.now(FUSO_BRASILIA)

        print(
            f"🏪 Status da loja atualizado: {novo_nome} | "
            f"{agora.strftime('%d/%m/%Y %H:%M:%S')} Brasília"
        )

    except discord.Forbidden:
        print(
            "❌ Não tenho permissão para alterar o nome "
            "do canal de funcionamento."
        )

    except discord.NotFound:
        print(
            "❌ Canal de funcionamento não encontrado."
        )

    except Exception as erro:
        print(
            f"❌ Erro atualizando status da loja: {erro}"
        )


@tasks.loop(seconds=30)
async def atualizar_status_loja_loop():
    await atualizar_status_loja()


@atualizar_status_loja_loop.before_loop
async def antes_de_atualizar_status_loja():
    await bot.wait_until_ready()


# =========================================================
# MERCADO PAGO — CRIAR PIX
# =========================================================

def criar_pagamento_pix(
    produto: str,
    preco: float,
    canal_id: int,
    usuario_id: int,
    email: str,
):
    if not MERCADOPAGO_ACCESS_TOKEN:
        print(
            "❌ MERCADOPAGO_ACCESS_TOKEN não configurado."
        )
        return None

    email = email.strip().lower()

    if "@" not in email:
        print("❌ E-mail inválido.")
        return None

    parte_dominio = email.split("@", 1)[1]

    if "." not in parte_dominio:
        print("❌ E-mail inválido.")
        return None

    url = "https://api.mercadopago.com/v1/payments"

    external_reference = (
        f"discord-{canal_id}-{usuario_id}-"
        f"{uuid.uuid4().hex}"
    )

    idempotency_key = str(uuid.uuid4())

    headers = {
        "Authorization": (
            f"Bearer {MERCADOPAGO_ACCESS_TOKEN}"
        ),
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-Idempotency-Key": idempotency_key,
    }

    dados = {
        "transaction_amount": float(
            f"{float(preco):.2f}"
        ),
        "description": str(produto)[:250],
        "payment_method_id": "pix",
        "external_reference": external_reference,
        "payer": {
            "email": email
        },
    }

    print("========================================")
    print("💳 CRIANDO PIX NO MERCADO PAGO")
    print(f"📦 Produto: {produto}")
    print(f"💰 Valor: R${preco:.2f}")
    print(f"📧 E-mail: {email}")
    print(f"🔑 Idempotency: {idempotency_key}")
    print(f"🔗 Referência: {external_reference}")
    print("========================================")

    try:
        resposta = requests.post(
            url,
            headers=headers,
            json=dados,
            timeout=30,
        )

    except requests.RequestException as erro:
        print(
            f"❌ Erro de conexão com Mercado Pago: {erro}"
        )
        return None

    print(
        f"📡 Mercado Pago HTTP: {resposta.status_code}"
    )

    try:
        pagamento = resposta.json()

    except ValueError:
        print(
            "❌ Mercado Pago retornou JSON inválido."
        )
        print(resposta.text)
        return None

    if resposta.status_code not in (200, 201):
        print("❌ ERRO MERCADO PAGO:")

        print(
            json.dumps(
                pagamento,
                indent=4,
                ensure_ascii=False,
            )
        )

        return None

    payment_id = pagamento.get("id")

    if not payment_id:
        print(
            "❌ Mercado Pago não retornou o ID do pagamento."
        )
        return None

    point_of_interaction = pagamento.get(
        "point_of_interaction",
        {},
    )

    transaction_data = point_of_interaction.get(
        "transaction_data",
        {},
    )

    pix_copia_cola = transaction_data.get(
        "qr_code"
    )

    qr_code_base64 = transaction_data.get(
        "qr_code_base64"
    )

    ticket_url = transaction_data.get(
        "ticket_url"
    )

    print(f"💳 Payment ID: {payment_id}")
    print(
        f"📊 Status: {pagamento.get('status')}"
    )
    print(
        f"📊 Status detail: "
        f"{pagamento.get('status_detail')}"
    )

    print(
        f"📋 QR Code/Pix Copia e Cola: "
        f"{bool(pix_copia_cola)}"
    )

    print(
        f"🖼️ QR Base64: "
        f"{bool(qr_code_base64)}"
    )

    print(
        f"🔗 Ticket URL: "
        f"{bool(ticket_url)}"
    )

    if not pix_copia_cola:
        print(
            "❌ Mercado Pago não retornou "
            "o Pix Copia e Cola."
        )

        print(
            json.dumps(
                pagamento,
                indent=4,
                ensure_ascii=False,
            )
        )

        return None

    return {
        "id": str(payment_id),
        "status": pagamento.get(
            "status",
            "pending",
        ),
        "status_detail": pagamento.get(
            "status_detail"
        ),
        "external_reference": external_reference,
        "qr_code": pix_copia_cola,
        "qr_code_base64": qr_code_base64,
        "ticket_url": ticket_url,
    }


# =========================================================
# MERCADO PAGO — CONSULTAR PAGAMENTO
# =========================================================

def consultar_pagamento(payment_id: str):
    if not MERCADOPAGO_ACCESS_TOKEN:
        return None

    url = (
        "https://api.mercadopago.com/v1/payments/"
        f"{payment_id}"
    )

    headers = {
        "Authorization": (
            f"Bearer {MERCADOPAGO_ACCESS_TOKEN}"
        ),
        "Accept": "application/json",
    }

    try:
        resposta = requests.get(
            url,
            headers=headers,
            timeout=20,
        )

    except requests.RequestException as erro:
        print(
            f"❌ Erro consultando pagamento "
            f"{payment_id}: {erro}"
        )
        return None

    if resposta.status_code != 200:
        print(
            f"❌ Erro consultando pagamento "
            f"{payment_id}: "
            f"{resposta.status_code}"
        )
        return None

    try:
        dados = resposta.json()

    except ValueError:
        print(
            f"❌ JSON inválido no pagamento "
            f"{payment_id}."
        )
        return None

    return {
        "status": dados.get("status"),
        "status_detail": dados.get(
            "status_detail"
        ),
    }


# =========================================================
# IDENTIFICAR PRODUTO
# =========================================================

def identificar_produto_do_canal(
    canal: discord.TextChannel,
) -> Optional[str]:

    topic = canal.topic or ""

    for chave in PRODUTOS:

        if f"ProdutoID: {chave}" in topic:
            return chave

    return None


# =========================================================
# MODAL DE E-MAIL
# =========================================================

class EmailPagamentoModal(Modal):

    def __init__(self, produto_id: str):
        super().__init__(
            title="Pagamento via PIX"
        )

        self.produto_id = produto_id

        self.email = TextInput(
            label="Seu e-mail",
            placeholder="exemplo@email.com",
            required=True,
            max_length=100,
        )

        self.add_item(self.email)

    async def on_submit(
        self,
        interaction: discord.Interaction,
    ):
        produto = PRODUTOS.get(
            self.produto_id
        )

        if not produto:
            await interaction.response.send_message(
                "❌ Produto não encontrado.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        resultado = await asyncio.to_thread(
            criar_pagamento_pix,
            produto["nome"],
            produto["preco"],
            interaction.channel.id,
            interaction.user.id,
            self.email.value,
        )

        if not resultado:
            await interaction.followup.send(
                "❌ Não consegui gerar o PIX.\n\n"
                "Verifique o Access Token do Mercado Pago "
                "e o e-mail informado.",
                ephemeral=True,
            )
            return

        pagamento_id = resultado["id"]
        pix = resultado.get("qr_code")

        if not pix:
            await interaction.followup.send(
                "❌ O Mercado Pago criou o pagamento, "
                "mas não retornou o Pix Copia e Cola.",
                ephemeral=True,
            )
            return

        pagamentos[pagamento_id] = {
            "payment_id": pagamento_id,
            "channel_id": interaction.channel.id,
            "user_id": interaction.user.id,
            "produto_id": self.produto_id,
            "produto": produto["nome"],
            "preco": produto["preco"],
            "status": resultado.get(
                "status",
                "pending",
            ),
            "status_detail": resultado.get(
                "status_detail"
            ),
            "entregue": False,
        }

        salvar_pagamentos()

        embed = discord.Embed(
            title="💳 PAGAMENTO VIA PIX",
            description=(
                f"📦 **Produto:** "
                f"{produto['nome']}\n\n"
                f"💰 **Valor:** "
                f"R${produto['preco']:.2f}\n\n"
                "🟡 **Status:** Aguardando pagamento\n\n"
                "Escaneie o **QR Code** ou use o "
                "**Pix Copia e Cola**.\n\n"
                "Após o pagamento, a confirmação "
                "será automática."
            ),
            color=discord.Color.gold(),
        )

        embed.add_field(
            name="📋 Pix Copia e Cola",
            value=(
                f"```text\n{pix}\n```"
            ),
            inline=False,
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

                if (
                    qr_base64.startswith(
                        "data:image"
                    )
                    and "," in qr_base64
                ):
                    qr_base64 = qr_base64.split(
                        ",",
                        1
                    )[1]

                imagem = base64.b64decode(
                    qr_base64,
                    validate=True,
                )

                arquivo = discord.File(
                    io.BytesIO(imagem),
                    filename="pix.png",
                )

                embed.set_image(
                    url="attachment://pix.png"
                )

            except Exception as erro:
                print(
                    f"❌ Erro processando QR Code: "
                    f"{erro}"
                )

        try:

            if arquivo:

                await interaction.channel.send(
                    embed=embed,
                    file=arquivo,
                )

            else:

                await interaction.channel.send(
                    embed=embed
                )

        except discord.Forbidden:

            await interaction.followup.send(
                "❌ Não tenho permissão para enviar "
                "o PIX neste ticket.",
                ephemeral=True,
            )
            return

        except Exception as erro:

            print(
                f"❌ Erro enviando PIX: {erro}"
            )

            await interaction.followup.send(
                "❌ O PIX foi criado, mas não consegui "
                "enviar a mensagem no ticket.",
                ephemeral=True,
            )
            return

        await interaction.followup.send(
            "✅ **PIX gerado!**\n\n"
            "Realize o pagamento pelo **QR Code** "
            "ou pelo **Pix Copia e Cola**.\n\n"
            "A confirmação será automática.",
            ephemeral=True,
        )


# =========================================================
# VIEW PAGAMENTO
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
        custom_id="pagar_pix",
    )
    async def pagar_pix(
        self,
        interaction,
        button,
    ):

        if not isinstance(
            interaction.channel,
            discord.TextChannel,
        ):
            await interaction.response.send_message(
                "❌ Canal inválido.",
                ephemeral=True,
            )
            return

        produto_id = identificar_produto_do_canal(
            interaction.channel
        )

        if not produto_id:
            await interaction.response.send_message(
                "❌ Não consegui identificar o produto.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(
            EmailPagamentoModal(produto_id)
        )


# =========================================================
# TRANSCRIPT
# =========================================================

async def gerar_transcript(
    canal: discord.TextChannel,
):

    linhas = [
        "==================================================",
        f"TRANSCRIPT — {NOME_LOJA}",
        f"Canal: #{canal.name}",
        f"ID do canal: {canal.id}",
        "==================================================",
        "",
    ]

    try:

        async for mensagem in canal.history(
            limit=None,
            oldest_first=True,
        ):

            data = mensagem.created_at.strftime(
                "%d/%m/%Y %H:%M:%S"
            )

            autor = (
                f"{mensagem.author} "
                f"(ID: {mensagem.author.id})"
            )

            linhas.append(
                f"[{data}] {autor}"
            )

            if mensagem.content:
                linhas.append(
                    mensagem.content
                )

            for anexo in mensagem.attachments:

                linhas.append(
                    f"[Anexo] "
                    f"{anexo.filename}: "
                    f"{anexo.url}"
                )

            if mensagem.embeds:

                linhas.append(
                    f"[Embed] "
                    f"{len(mensagem.embeds)} embed(s)"
                )

            for sticker in mensagem.stickers:

                linhas.append(
                    f"[Sticker] {sticker.name}"
                )

            linhas.append("")

    except Exception as erro:

        linhas.append(
            f"[ERRO AO LER MENSAGENS] {erro}"
        )

        print(
            f"❌ Erro gerando transcript: {erro}"
        )

    linhas.extend(
        [
            "==================================================",
            "Fim do transcript.",
        ]
    )

    arquivo = io.BytesIO(
        "\n".join(linhas).encode("utf-8")
    )

    arquivo.seek(0)

    return arquivo


# =========================================================
# FECHAR TICKET
# =========================================================

async def fechar_ticket(
    canal: discord.TextChannel,
    interaction: discord.Interaction,
):

    topic = canal.topic or ""

    cliente_id = None

    for parte in topic.split("|"):

        parte = parte.strip()

        if parte.startswith("Cliente:"):

            try:

                cliente_id = int(
                    parte.split(
                        ":",
                        1
                    )[1].strip()
                )

            except ValueError:

                cliente_id = None

            break

    if not cliente_id:

        await interaction.edit_original_response(
            content=(
                "❌ Não consegui identificar "
                "o cliente deste ticket.\n"
                "O canal não será excluído."
            )
        )

        return

    cliente = interaction.guild.get_member(
        cliente_id
    )

    if not cliente:

        try:

            cliente = (
                await interaction.guild.fetch_member(
                    cliente_id
                )
            )

        except Exception:

            cliente = None

    if not cliente:

        await interaction.edit_original_response(
            content=(
                "⚠️ Não consegui encontrar "
                "o cliente deste ticket.\n\n"
                "O ticket não será excluído."
            )
        )

        return

    await interaction.edit_original_response(
        content=(
            "📄 Gerando o transcript do ticket..."
        )
    )

    arquivo = await gerar_transcript(
        canal
    )

    arquivo.seek(0)

    try:

        await cliente.send(
            content=(
                f"📄 **Transcript do seu ticket — "
                f"{NOME_LOJA}**\n\n"
                "Seu ticket foi encerrado pela equipe.\n"
                "O transcript completo do atendimento "
                "está anexado abaixo."
            ),
            file=discord.File(
                arquivo,
                filename=(
                    f"transcript-{canal.id}.txt"
                ),
            ),
        )

    except discord.Forbidden:

        await interaction.edit_original_response(
            content=(
                "⚠️ **Não consegui enviar o transcript "
                "no PV do cliente.**\n\n"
                "O ticket **não será excluído** "
                "para não perder o histórico."
            )
        )

        return

    except Exception as erro:

        print(
            f"❌ Erro enviando transcript: {erro}"
        )

        await interaction.edit_original_response(
            content=(
                "⚠️ Ocorreu um erro ao enviar "
                "o transcript no PV.\n\n"
                "O ticket **não será excluído**."
            )
        )

        return

    await interaction.edit_original_response(
        content=(
            "✅ **Transcript enviado no PV do cliente!**\n\n"
            "🗑️ O ticket será excluído em **3 segundos**."
        )
    )

    await asyncio.sleep(3)

    try:

        await canal.delete(
            reason=(
                "Ticket fechado — "
                "transcript enviado ao cliente"
            )
        )

    except discord.NotFound:
        pass

    except discord.Forbidden:

        print(
            "❌ O bot não tem permissão "
            "para excluir o ticket."
        )

    except Exception as erro:

        print(
            f"❌ Erro excluindo ticket: {erro}"
        )


# =========================================================
# VIEW DO TICKET
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
        custom_id="ticket_pagar_pix",
        row=0,
    )
    async def pagar_pix(
        self,
        interaction,
        button,
    ):

        if not isinstance(
            interaction.channel,
            discord.TextChannel,
        ):
            await interaction.response.send_message(
                "❌ Canal inválido.",
                ephemeral=True,
            )
            return

        produto_id = identificar_produto_do_canal(
            interaction.channel
        )

        if not produto_id:
            await interaction.response.send_message(
                "❌ Não consegui identificar o produto.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(
            EmailPagamentoModal(produto_id)
        )

    @discord.ui.button(
        label="Fechar",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="ticket_fechar",
        row=0,
    )
    async def fechar(
        self,
        interaction,
        button,
    ):

        if not interaction.user.guild_permissions.manage_channels:

            await interaction.response.send_message(
                "❌ Apenas a equipe pode fechar este ticket.",
                ephemeral=True,
            )

            return

        await interaction.response.send_message(
            "🔒 Fechando o ticket e preparando "
            "o transcript..."
        )

        if isinstance(
            interaction.channel,
            discord.TextChannel,
        ):

            await fechar_ticket(
                interaction.channel,
                interaction,
            )


# =========================================================
# ANYDESK — MODAL
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
            max_length=30,
        )

        self.add_item(
            self.anydesk_id
        )

    async def on_submit(
        self,
        interaction,
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
            color=discord.Color.green(),
        )

        await interaction.channel.send(
            embed=embed
        )

        await interaction.response.send_message(
            "✅ Seu ID foi enviado para a equipe!",
            ephemeral=True,
        )


# =========================================================
# TUTORIAL ANYDESK
# =========================================================

class AnyDeskTutorialView(View):

    def __init__(self):
        super().__init__(
            timeout=None
        )

        self.add_item(
            discord.ui.Button(
                label="Baixar AnyDesk",
                emoji="📥",
                style=discord.ButtonStyle.link,
                url=LINK_ANYDESK,
                row=0,
            )
        )

    @discord.ui.button(
        label="Informar meu ID",
        emoji="🔢",
        style=discord.ButtonStyle.primary,
        custom_id="tutorial_informar_id",
        row=0,
    )
    async def informar_id(
        self,
        interaction,
        button,
    ):

        await interaction.response.send_modal(
            AnyDeskModal()
        )


# =========================================================
# EMBED TUTORIAL
# =========================================================

def criar_tutorial_embed():

    embed = discord.Embed(
        title="🖥️ ACESSO LIBERADO — TUTORIAL ANYDESK",
        description=(
            "Seu pagamento foi **confirmado com sucesso!** 🎉\n\n"
            "Agora siga o tutorial abaixo para realizar o atendimento.\n\n"
            "**1️⃣ Baixe o AnyDesk**\n"
            "Clique no botão **📥 Baixar AnyDesk** abaixo.\n\n"
            "**2️⃣ Abra o AnyDesk**\n"
            "Depois de baixar, abra o programa.\n\n"
            "**3️⃣ Localize seu ID**\n"
            "Procure o ID exibido na tela principal.\n\n"
            "**4️⃣ Envie seu ID**\n"
            "Clique em **🔢 Informar meu ID** e coloque o número "
            "que aparece no AnyDesk.\n\n"
            "📌 Depois de enviar seu ID, aguarde a equipe."
        ),
        color=discord.Color.green(),
    )

    embed.add_field(
        name="📥 Download do AnyDesk",
        value=(
            "Clique em **📥 Baixar AnyDesk** para acessar "
            "o download oficial."
        ),
        inline=False,
    )

    embed.add_field(
        name="🔢 Enviar ID",
        value=(
            "Depois de abrir o AnyDesk, clique em "
            "**🔢 Informar meu ID**."
        ),
        inline=False,
    )

    embed.set_footer(
        text=f"{NOME_LOJA} • Atendimento"
    )

    return embed


# =========================================================
# CRIAR TICKET
# =========================================================

async def criar_ticket(
    interaction: discord.Interaction,
    produto_id: str,
):

    produto = PRODUTOS.get(
        produto_id
    )

    if not produto:

        await interaction.response.send_message(
            "❌ Produto não encontrado.",
            ephemeral=True,
        )

        return

    guild = interaction.guild
    membro = interaction.user

    if guild is None:

        await interaction.response.send_message(
            "❌ Esse botão só pode ser usado "
            "dentro de um servidor.",
            ephemeral=True,
        )

        return

    for canal_existente in guild.text_channels:

        topic = canal_existente.topic or ""

        if f"Cliente: {membro.id}" in topic:

            await interaction.response.send_message(
                f"❌ Você já possui um ticket: "
                f"{canal_existente.mention}",
                ephemeral=True,
            )

            return

    categoria = interaction.channel.category

    bot_member = guild.me

    if bot_member is None:

        try:

            bot_member = await guild.fetch_member(
                bot.user.id
            )

        except Exception:

            bot_member = None

    if bot_member is None:

        await interaction.response.send_message(
            "❌ Não consegui identificar "
            "as permissões do bot.",
            ephemeral=True,
        )

        return

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
                embed_links=True,
            ),

        bot_member:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
                manage_messages=True,
                attach_files=True,
                embed_links=True,
            ),
    }

    cargo_atendente = guild.get_role(
        CARGO_ATENDENTE
    )

    if cargo_atendente:

        overwrites[cargo_atendente] = (
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
            )
        )

    else:

        print(
            f"⚠️ Cargo de atendente "
            f"{CARGO_ATENDENTE} não encontrado."
        )

    try:

        canal = await guild.create_text_channel(
            name="🟡・aguardando-pagamento",
            category=categoria,
            topic=(
                f"Cliente: {membro.id} | "
                f"ProdutoID: {produto_id}"
            ),
            overwrites=overwrites,
            reason=(
                f"Compra: {produto['nome']}"
            ),
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ Não tenho permissão para criar o ticket.",
            ephemeral=True,
        )

        return

    except Exception as erro:

        print(
            f"❌ Erro criando ticket: {erro}"
        )

        await interaction.response.send_message(
            "❌ Ocorreu um erro ao criar o ticket.",
            ephemeral=True,
        )

        return

    embed = discord.Embed(
        title="🛒 PEDIDO",
        description=(
            f"📦 **Produto:** "
            f"{produto['nome']}\n\n"
            f"💰 **Valor:** "
            f"R${produto['preco']:.2f}\n\n"
            f"📋 **Sobre o produto:**\n"
            f"{produto['descricao']}\n\n"
            "🟡 **Status:** Aguardando pagamento\n\n"
            "Clique em **💳 Pagar com PIX** "
            "para gerar seu pagamento.\n\n"
            "Após a confirmação, o acesso será "
            "liberado automaticamente."
        ),
        color=discord.Color.gold(),
    )

    embed.set_footer(
        text=(
            f"{NOME_LOJA} • "
            "Pagamento seguro via PIX"
        )
    )

    try:

        mencao_atendente = (
            cargo_atendente.mention
            if cargo_atendente
            else f"<@&{CARGO_ATENDENTE}>"
        )

        await canal.send(
            content=(
                f"{membro.mention} "
                f"{mencao_atendente}\n\n"
                "📢 **Novo ticket aberto!**\n"
                "A equipe de atendimento foi notificada."
            ),
            embed=embed,
            view=TicketView(),
        )

    except Exception as erro:

        print(
            f"❌ Erro enviando painel do ticket: "
            f"{erro}"
        )

        try:

            await canal.delete(
                reason=(
                    "Erro ao enviar painel do ticket"
                )
            )

        except Exception:
            pass

        await interaction.response.send_message(
            "❌ Não consegui configurar o ticket.",
            ephemeral=True,
        )

        return

    await interaction.response.send_message(
        f"✅ Seu ticket foi criado: "
        f"{canal.mention}",
        ephemeral=True,
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
        custom_id="otimizacao_basica",
    )
    async def basica(
        self,
        interaction,
        button,
    ):

        await criar_ticket(
            interaction,
            "basica"
        )

    @discord.ui.button(
        label="Otimização Completa — R$30,00",
        emoji="🚀",
        style=discord.ButtonStyle.success,
        custom_id="otimizacao_completa",
    )
    async def completa(
        self,
        interaction,
        button,
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
        custom_id="otimizacao_vitalicia",
    )
    async def vitalicia(
        self,
        interaction,
        button,
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
        custom_id="curso_otimizacao",
    )
    async def curso(
        self,
        interaction,
        button,
    ):

        await criar_ticket(
            interaction,
            "curso"
        )


# =========================================================
# PROCESSAR PAGAMENTO APROVADO
# =========================================================

async def processar_pagamento_aprovado(
    payment_id: str,
    dados: dict,
):

    if dados.get("entregue") is True:
        return True

    canal_id = dados.get(
        "channel_id"
    )

    user_id = dados.get(
        "user_id"
    )

    produto_id = dados.get(
        "produto_id"
    )

    if not canal_id or not user_id or not produto_id:

        print(
            f"⚠️ Dados incompletos "
            f"no pagamento {payment_id}."
        )

        return False

    produto = PRODUTOS.get(
        produto_id
    )

    if not produto:

        print(
            f"⚠️ Produto inválido: "
            f"{produto_id}"
        )

        return False

    canal = bot.get_channel(
        int(canal_id)
    )

    if canal is None:

        try:

            canal = await bot.fetch_channel(
                int(canal_id)
            )

        except Exception as erro:

            print(
                f"⚠️ Não consegui encontrar "
                f"o canal {canal_id}: {erro}"
            )

            return False

    if not isinstance(
        canal,
        discord.TextChannel,
    ):

        print(
            f"⚠️ Canal {canal_id} "
            "não é canal de texto."
        )

        return False

    guild = canal.guild

    membro = guild.get_member(
        int(user_id)
    )

    if membro is None:

        try:

            membro = await guild.fetch_member(
                int(user_id)
            )

        except Exception as erro:

            print(
                f"⚠️ Não consegui encontrar "
                f"o cliente {user_id}: {erro}"
            )

            return False

    cargos = []
    falhou_cargo = False

    for cargo_id in produto["cargos"]:

        cargo = guild.get_role(
            cargo_id
        )

        if not cargo:

            print(
                f"⚠️ Cargo não encontrado: "
                f"{cargo_id}"
            )

            falhou_cargo = True
            continue

        try:

            if cargo not in membro.roles:

                await membro.add_roles(
                    cargo,
                    reason=(
                        "Pagamento PIX aprovado — "
                        f"{produto['nome']}"
                    ),
                )

            cargos.append(
                cargo.mention
            )

        except discord.Forbidden:

            print(
                f"❌ Não consegui entregar "
                f"o cargo {cargo.name}. "
                "Verifique a hierarquia/permissão."
            )

            falhou_cargo = True

        except Exception as erro:

            print(
                f"❌ Erro entregando cargo "
                f"{cargo.name}: {erro}"
            )

            falhou_cargo = True

    if falhou_cargo:

        print(
            f"⚠️ Pagamento {payment_id} aprovado, "
            "mas a entrega de cargo falhou."
        )

        return False

    try:

        await canal.edit(
            name="🟢・pago"
        )

    except Exception as erro:

        print(
            f"⚠️ Erro alterando nome "
            f"do ticket: {erro}"
        )

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
            "Abaixo está o painel para baixar "
            "o AnyDesk e seguir o tutorial."
        ),
        color=discord.Color.green(),
    )

    if cargos:

        embed.add_field(
            name="🎁 Cargos liberados",
            value="\n".join(cargos),
            inline=False,
        )

    embed.set_footer(
        text=(
            f"{NOME_LOJA} • "
            "Pagamento confirmado"
        )
    )

    try:

        await canal.send(
            embed=embed
        )

    except Exception as erro:

        print(
            f"❌ Erro enviando aprovação: "
            f"{erro}"
        )

        return False

    tutorial_embed = (
        criar_tutorial_embed()
    )

    if TUTORIAL_IMG_1:

        tutorial_embed.set_image(
            url=TUTORIAL_IMG_1
        )

    try:

        await canal.send(
            embed=tutorial_embed,
            view=AnyDeskTutorialView(),
        )

    except Exception as erro:

        print(
            f"❌ Erro enviando AnyDesk: "
            f"{erro}"
        )

    if TUTORIAL_IMG_2:

        try:

            imagem_embed = discord.Embed(
                color=discord.Color.blurple()
            )

            imagem_embed.set_image(
                url=TUTORIAL_IMG_2
            )

            await canal.send(
                embed=imagem_embed
            )

        except Exception as erro:

            print(
                f"❌ Erro enviando imagem 2: "
                f"{erro}"
            )

    if TUTORIAL_IMG_3:

        try:

            imagem_embed = discord.Embed(
                color=discord.Color.blurple()
            )

            imagem_embed.set_image(
                url=TUTORIAL_IMG_3
            )

            await canal.send(
                embed=imagem_embed
            )

        except Exception as erro:

            print(
                f"❌ Erro enviando imagem 3: "
                f"{erro}"
            )

    dados["status"] = "approved"
    dados["status_detail"] = "accredited"
    dados["entregue"] = True

    return True


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

        if dados.get("entregue") is True:
            continue

        resultado = await asyncio.to_thread(
            consultar_pagamento,
            payment_id,
        )

        if resultado is None:
            continue

        status = resultado.get(
            "status"
        )

        status_detail = resultado.get(
            "status_detail"
        )

        print(
            f"🔎 Pagamento {payment_id} → "
            f"{status} / {status_detail}"
        )

        if status != "approved":

            if (
                dados.get("status") != status
                or dados.get("status_detail")
                != status_detail
            ):

                dados["status"] = status
                dados["status_detail"] = (
                    status_detail
                )

                alterou = True

            continue

        sucesso = (
            await processar_pagamento_aprovado(
                payment_id,
                dados,
            )
        )

        if sucesso:
            alterou = True

    if alterou:
        salvar_pagamentos()


@verificar_pagamentos.before_loop
async def antes_de_verificar_pagamentos():
    await bot.wait_until_ready()


# =========================================================
# BOT
# =========================================================

class LojaBot(commands.Bot):

    def __init__(self):

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self):

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
            TicketView()
        )

        self.add_view(
            PagamentoView()
        )

        self.add_view(
            AnyDeskTutorialView()
        )

        print(
            "✅ Views persistentes carregadas."
        )

    async def on_ready(self):

        print(
            "========================================"
        )

        print(
            f"🤖 Bot conectado: {self.user}"
        )

        print(
            f"🆔 ID: {self.user.id}"
        )

        print(
            f"🌐 Servidores: {len(self.guilds)}"
        )

        agora = datetime.now(
            FUSO_BRASILIA
        )

        print(
            f"🕐 Brasília: "
            f"{agora.strftime('%d/%m/%Y %H:%M:%S')}"
        )

        print(
            "========================================"
        )

        await atualizar_status_loja()

        if not atualizar_status_loja_loop.is_running():

            atualizar_status_loja_loop.start()

            print(
                "🏪 Status automático iniciado."
            )

        if not verificar_pagamentos.is_running():

            verificar_pagamentos.start()

            print(
                "💳 Verificação automática "
                "de pagamentos iniciada."
            )

    async def on_disconnect(self):

        print(
            "⚠️ Bot desconectado do Discord."
        )

    async def on_resumed(self):

        print(
            "🔄 Conexão com Discord restaurada."
        )

        await atualizar_status_loja()


bot = LojaBot()


# =========================================================
# COMANDO PING
# =========================================================

@bot.command(name="ping")
@commands.has_permissions(
    administrator=True
)
async def ping(ctx):

    await ctx.send(
        f"🏓 Pong! "
        f"`{round(bot.latency * 1000)}ms`"
    )


@ping.error
async def ping_error(
    ctx,
    error,
):

    if isinstance(
        error,
        commands.MissingPermissions,
    ):

        await ctx.send(
            "❌ Você precisa ser administrador."
        )


# =========================================================
# PAINEL OTIMIZAÇÃO
# =========================================================

@bot.command(
    name="painel_otimizacao"
)
@commands.has_permissions(
    administrator=True
)
async def painel_otimizacao(
    ctx,
):

    embed = discord.Embed(
        title="⚙️ TK OTIMIZAÇÃO",
        description=(
            "Escolha a otimização que melhor atende "
            "às necessidades do seu computador.\n\n"

            "⚙️ **Otimização Básica — R$15,00**\n"
            "Uma otimização focada em melhorar o desempenho "
            "do sistema, buscando mais estabilidade e uma "
            "melhor experiência nos jogos.\n\n"

            "🚀 **Otimização Completa — R$30,00**\n"
            "Uma otimização mais completa, com ajustes "
            "voltados para desempenho, estabilidade e "
            "melhor aproveitamento do computador.\n\n"

            "🎫 Após escolher um produto, será criado um "
            "ticket privado para realizar o pagamento "
            "e receber o atendimento."
        ),
        color=discord.Color.blurple(),
    )

    embed.set_footer(
        text=NOME_LOJA
    )

    await ctx.send(
        embed=embed,
        view=OtimizacaoView(),
    )


# =========================================================
# PAINEL VITALÍCIA
# =========================================================

@bot.command(
    name="painel_vitalicia"
)
@commands.has_permissions(
    administrator=True
)
async def painel_vitalicia(
    ctx,
):

    embed = discord.Embed(
        title="♾️ OTIMIZAÇÃO COMPLETA VITALÍCIA",
        description=(
            "Tenha acesso à nossa **Otimização Completa** "
            "com suporte para futuras otimizações.\n\n"

            "♾️ **Valor: R$60,00**\n\n"

            "Com a versão vitalícia, você conta com uma "
            "solução completa para melhorar o desempenho "
            "do computador e ainda pode receber suporte "
            "para futuras otimizações quando necessário.\n\n"

            "💳 O pagamento é realizado de forma segura "
            "via PIX, com confirmação automática.\n\n"

            "👇 **Clique no botão abaixo para abrir seu ticket.**"
        ),
        color=discord.Color.green(),
    )

    embed.set_footer(
        text=NOME_LOJA
    )

    await ctx.send(
        embed=embed,
        view=VitaliciaView(),
    )


# =========================================================
# PAINEL CURSO
# =========================================================

@bot.command(
    name="painel_curso"
)
@commands.has_permissions(
    administrator=True
)
async def painel_curso(
    ctx,
):

    embed = discord.Embed(
        title="🎓 APRENDA A OTIMIZAR",
        description=(
            "Quer aprender a fazer suas próprias otimizações?\n\n"

            "🎓 **Curso completo — R$100,00**\n\n"

            "Aprenda a entender melhor as configurações "
            "do computador e como realizar ajustes voltados "
            "para desempenho e estabilidade.\n\n"

            "📚 O objetivo é ensinar você a compreender "
            "as principais configurações e realizar suas "
            "próprias otimizações de maneira mais consciente.\n\n"

            "💳 Após escolher o curso, será criado um ticket "
            "privado para realizar o pagamento e receber "
            "as informações de acesso.\n\n"

            "👇 **Clique no botão abaixo para adquirir o curso.**"
        ),
        color=discord.Color.blurple(),
    )

    embed.set_footer(
        text=NOME_LOJA
    )

    await ctx.send(
        embed=embed,
        view=CursoView(),
    )


# =========================================================
# ERROS
# =========================================================

@bot.event
async def on_command_error(
    ctx,
    error,
):

    if isinstance(
        error,
        commands.CommandNotFound,
    ):
        return

    if isinstance(
        error,
        commands.MissingPermissions,
    ):

        await ctx.send(
            "❌ Você não tem permissão "
            "para usar este comando."
        )

        return

    if isinstance(
        error,
        commands.MissingRequiredArgument,
    ):

        await ctx.send(
            "❌ Está faltando algum argumento."
        )

        return

    print(
        f"❌ Erro no comando: {error}"
    )


# =========================================================
# INICIAR BOT
# =========================================================

if __name__ == "__main__":

    if not DISCORD_TOKEN:

        print(
            "❌ BOT NÃO INICIADO!"
        )

        print(
            "Configure a variável "
            "DISCORD_TOKEN no Laplace."
        )

    elif not MERCADOPAGO_ACCESS_TOKEN:

        print(
            "❌ BOT NÃO INICIADO!"
        )

        print(
            "Configure a variável "
            "MERCADOPAGO_ACCESS_TOKEN no Laplace."
        )

    else:

        try:

            print(
                "🚀 Iniciando BotLoja..."
            )

            bot.run(
                DISCORD_TOKEN
            )

        except discord.LoginFailure:

            print(
                "❌ DISCORD_TOKEN inválido."
            )

        except Exception as erro:

            print(
                f"❌ Erro fatal ao iniciar "
                f"o bot: {erro}"
            )
````
