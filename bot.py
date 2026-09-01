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

CANAL_STATUS_LOJA = 1539753330585112576


# =========================================================
# IDS DOS CARGOS
# =========================================================

CARGO_COMUM = 1489876079840591935
CARGO_OTIMIZACAO = 1539751475876597890
CARGO_VITALICIA = 1544129229883445299
CARGO_CURSO = 1544128542487355392


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
        "cargos": [
            CARGO_COMUM,
            CARGO_OTIMIZACAO,
        ],
    },

    "completa": {
        "nome": "Otimização Completa",
        "preco": 30.00,
        "cargos": [
            CARGO_COMUM,
            CARGO_OTIMIZACAO,
        ],
    },

    "vitalicia": {
        "nome": "Otimização Completa Vitalícia",
        "preco": 60.00,
        "cargos": [
            CARGO_COMUM,
            CARGO_VITALICIA,
        ],
    },

    "curso": {
        "nome": "Aprenda a Otimizar",
        "preco": 100.00,
        "cargos": [
            CARGO_COMUM,
            CARGO_CURSO,
        ],
    },
}


# =========================================================
# VARIÁVEIS DE AMBIENTE
# =========================================================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MERCADOPAGO_ACCESS_TOKEN = os.getenv(
    "MERCADOPAGO_ACCESS_TOKEN"
)

if not DISCORD_TOKEN:
    print("❌ ERRO: DISCORD_TOKEN não configurado.")

if not MERCADOPAGO_ACCESS_TOKEN:
    print(
        "⚠️ AVISO: MERCADOPAGO_ACCESS_TOKEN "
        "não configurado."
    )


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
            encoding="utf-8",
        ) as arquivo:

            dados = json.load(arquivo)

        if isinstance(dados, dict):
            return dados

        return {}

    except Exception as erro:

        print(
            f"❌ Erro carregando pagamentos: {erro}"
        )

        return {}


pagamentos = carregar_pagamentos()


def salvar_pagamentos():

    try:

        arquivo_temporario = (
            f"{ARQUIVO_PAGAMENTOS}.tmp"
        )

        with open(
            arquivo_temporario,
            "w",
            encoding="utf-8",
        ) as arquivo:

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

        print(
            f"❌ Erro salvando pagamentos: {erro}"
        )


# =========================================================
# STATUS DA LOJA
# =========================================================

def loja_esta_aberta():

    agora = datetime.now(FUSO_BRASILIA)

    return (
        HORA_ABERTURA
        <= agora.hour
        < HORA_FECHAMENTO
    )


async def atualizar_status_loja():

    canal = bot.get_channel(
        CANAL_STATUS_LOJA
    )

    if canal is None:

        try:

            canal = await bot.fetch_channel(
                CANAL_STATUS_LOJA
            )

        except Exception as erro:

            print(
                "❌ Não consegui encontrar "
                f"o canal de status: {erro}"
            )

            return

    if not isinstance(
        canal,
        discord.TextChannel,
    ):

        print(
            "❌ O canal de status não é "
            "um canal de texto."
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
            reason="Atualização automática do status da loja",
        )

        agora = datetime.now(
            FUSO_BRASILIA
        )

        print(
            f"🏪 Status atualizado: {novo_nome} | "
            f"{agora.strftime('%d/%m/%Y %H:%M:%S')}"
        )

    except discord.Forbidden:

        print(
            "❌ Sem permissão para alterar "
            "o nome do canal de status."
        )

    except discord.NotFound:

        print(
            "❌ Canal de status não encontrado."
        )

    except Exception as erro:

        print(
            f"❌ Erro atualizando status: {erro}"
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
            "❌ Access Token do Mercado Pago "
            "não configurado."
        )

        return None

    email = email.strip().lower()

    if "@" not in email:

        print("❌ E-mail inválido.")

        return None

    partes_email = email.split("@")

    if len(partes_email) != 2:
        return None

    if "." not in partes_email[1]:
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
        "transaction_amount": round(
            float(preco),
            2,
        ),
        "description": str(produto)[:250],
        "payment_method_id": "pix",
        "external_reference": external_reference,
        "payer": {
            "email": email,
        },
    }

    print("")
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
            "❌ Mercado Pago retornou "
            "uma resposta que não é JSON."
        )

        print(resposta.text)

        return None

    if resposta.status_code not in (200, 201):

        print("❌ ERRO AO CRIAR PIX:")

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
            "❌ Mercado Pago não retornou "
            "o ID do pagamento."
        )

        print(
            json.dumps(
                pagamento,
                indent=4,
                ensure_ascii=False,
            )
        )

        return None

    status = pagamento.get(
        "status",
        "pending",
    )

    status_detail = pagamento.get(
        "status_detail"
    )

    external_reference_retorno = (
        pagamento.get(
            "external_reference"
        )
        or external_reference
    )

    point_of_interaction = pagamento.get(
        "point_of_interaction"
    ) or {}

    transaction_data = (
        point_of_interaction.get(
            "transaction_data"
        )
        or {}
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

    if not ticket_url:

        ticket_url = pagamento.get(
            "ticket_url"
        )

    print(
        f"💳 Payment ID: {payment_id}"
    )

    print(
        f"📊 Status: {status}"
    )

    print(
        f"📊 Status detail: {status_detail}"
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
            "❌ O pagamento foi criado, "
            "mas o Mercado Pago não retornou "
            "o qr_code."
        )

        print(
            "📦 RESPOSTA COMPLETA:"
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
        "status": status,
        "status_detail": status_detail,
        "external_reference": external_reference_retorno,
        "qr_code": pix_copia_cola,
        "qr_code_base64": qr_code_base64,
        "ticket_url": ticket_url,
    }


# =========================================================
# CONSULTAR PAGAMENTO
# =========================================================

def consultar_pagamento(
    payment_id: str,
):

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
            f"❌ Consulta do pagamento "
            f"{payment_id} retornou "
            f"HTTP {resposta.status_code}"
        )

        try:

            print(
                resposta.text
            )

        except Exception:
            pass

        return None

    try:

        dados = resposta.json()

    except ValueError:

        print(
            f"❌ Resposta inválida do pagamento "
            f"{payment_id}."
        )

        return None

    status = dados.get("status")

    status_detail = dados.get(
        "status_detail"
    )

    print(
        f"🔎 Pagamento {payment_id} → "
        f"{status} / {status_detail}"
    )

    return {
        "status": status,
        "status_detail": status_detail,
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

    def __init__(
        self,
        produto_id: str,
    ):

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

        self.add_item(
            self.email
        )

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
                "❌ **Não consegui gerar o PIX.**\n\n"
                "Verifique se o "
                "**MERCADOPAGO_ACCESS_TOKEN** "
                "está correto e se a conta Mercado "
                "Pago está configurada para receber PIX.\n\n"
                "Veja também o console do bot para "
                "o erro retornado pela API.",
                ephemeral=True,
            )

            return

        pagamento_id = resultado["id"]

        pix = resultado.get(
            "qr_code"
        )

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
            "external_reference": resultado.get(
                "external_reference"
            ),
            "ticket_url": resultado.get(
                "ticket_url"
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
                "🟡 **Status:** "
                "Aguardando pagamento\n\n"
                "Escaneie o **QR Code** abaixo "
                "ou use o **Pix Copia e Cola**.\n\n"
                "Após o pagamento, a confirmação "
                "será automática."
            ),
            color=discord.Color.gold(),
        )

        embed.add_field(
            name="📋 PIX COPIA E COLA",
            value=(
                "```text\n"
                f"{pix}\n"
                "```"
            ),
            inline=False,
        )

        ticket_url = resultado.get(
            "ticket_url"
        )

        if ticket_url:

            embed.add_field(
                name="🔗 Pagamento",
                value=(
                    f"[Abrir pagamento do Mercado Pago]"
                    f"({ticket_url})"
                ),
                inline=False,
            )

        embed.set_footer(
            text=(
                "A confirmação do pagamento "
                "é automática."
            )
        )

        arquivo = None

        qr_base64 = resultado.get(
            "qr_code_base64"
        )

        if qr_base64:

            try:

                # Remove prefixo caso a API retorne:
                # data:image/png;base64,...
                if "," in qr_base64:

                    prefixo, conteudo = (
                        qr_base64.split(
                            ",",
                            1,
                        )
                    )

                    if (
                        "base64" in prefixo.lower()
                    ):

                        qr_base64 = conteudo

                qr_base64 = (
                    qr_base64
                    .replace("\n", "")
                    .replace("\r", "")
                    .strip()
                )

                imagem = base64.b64decode(
                    qr_base64,
                    validate=True,
                )

                if not imagem:

                    raise ValueError(
                        "QR Code vazio."
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
                    "❌ Erro processando "
                    f"QR Code Base64: {erro}"
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
                "❌ Não tenho permissão para "
                "enviar o PIX neste ticket.",
                ephemeral=True,
            )

            return

        except Exception as erro:

            print(
                f"❌ Erro enviando PIX: {erro}"
            )

            await interaction.followup.send(
                "❌ O PIX foi criado, mas não "
                "consegui enviar a cobrança "
                "no ticket.",
                ephemeral=True,
            )

            return

        await interaction.followup.send(
            "✅ **PIX gerado com sucesso!**\n\n"
            "Pague pelo **QR Code** ou pelo "
            "**Pix Copia e Cola**.\n\n"
            "💳 Assim que o Mercado Pago "
            "confirmar o pagamento, o bot "
            "liberará os cargos automaticamente.",
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
        interaction: discord.Interaction,
        button: discord.ui.Button,
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

        produto_id = (
            identificar_produto_do_canal(
                interaction.channel
            )
        )

        if not produto_id:

            await interaction.response.send_message(
                "❌ Não consegui identificar "
                "o produto deste ticket.",
                ephemeral=True,
            )

            return

        await interaction.response.send_modal(
            EmailPagamentoModal(
                produto_id
            )
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

            if mensagem.attachments:

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

            if mensagem.stickers:

                for sticker in mensagem.stickers:

                    linhas.append(
                        f"[Sticker] "
                        f"{sticker.name}"
                    )

            linhas.append("")

    except Exception as erro:

        linhas.append(
            f"[ERRO AO LER MENSAGENS] {erro}"
        )

        print(
            f"❌ Erro gerando transcript: {erro}"
        )

    linhas.extend([
        "==================================================",
        "Fim do transcript.",
    ])

    arquivo = io.BytesIO(
        "\n".join(linhas).encode(
            "utf-8"
        )
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
                        1,
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
            "📄 Gerando o transcript "
            "do ticket..."
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
                "O transcript completo está anexado."
            ),
            file=discord.File(
                arquivo,
                filename=f"transcript-{canal.id}.txt",
            ),
        )

    except discord.Forbidden:

        await interaction.edit_original_response(
            content=(
                "⚠️ **Não consegui enviar "
                "o transcript no PV do cliente.**\n\n"
                "O ticket **não será excluído**."
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
                "o transcript.\n\n"
                "O ticket **não será excluído**."
            )
        )

        return

    await interaction.edit_original_response(
        content=(
            "✅ **Transcript enviado no PV!**\n\n"
            "🗑️ O ticket será excluído "
            "em **3 segundos**."
        )
    )

    await asyncio.sleep(3)

    try:

        await canal.delete(
            reason=(
                "Ticket fechado — "
                "transcript enviado"
            )
        )

    except discord.NotFound:
        pass

    except discord.Forbidden:

        print(
            "❌ Sem permissão para excluir ticket."
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
        interaction: discord.Interaction,
        button: discord.ui.Button,
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

        produto_id = (
            identificar_produto_do_canal(
                interaction.channel
            )
        )

        if not produto_id:

            await interaction.response.send_message(
                "❌ Não consegui identificar "
                "o produto.",
                ephemeral=True,
            )

            return

        await interaction.response.send_modal(
            EmailPagamentoModal(
                produto_id
            )
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
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        if not interaction.user.guild_permissions.manage_channels:

            await interaction.response.send_message(
                "❌ Apenas a equipe pode "
                "fechar este ticket.",
                ephemeral=True,
            )

            return

        await interaction.response.send_message(
            "🔒 Fechando o ticket e "
            "preparando o transcript..."
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
# ANYDESK
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
        interaction: discord.Interaction,
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

        botao_download = discord.ui.Button(
            label="Baixar AnyDesk",
            emoji="📥",
            style=discord.ButtonStyle.link,
            url=LINK_ANYDESK,
            row=0,
        )

        self.add_item(
            botao_download
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
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        await interaction.response.send_modal(
            AnyDeskModal()
        )


# =========================================================
# EMBED TUTORIAL
# =========================================================

def criar_tutorial_embed():

    embed = discord.Embed(
        title=(
            "🖥️ ACESSO LIBERADO — "
            "TUTORIAL ANYDESK"
        ),
        description=(
            "Seu pagamento foi "
            "**confirmado com sucesso!** 🎉\n\n"
            "Agora siga o tutorial abaixo.\n\n"
            "**1️⃣ Baixe o AnyDesk**\n"
            "Clique em **📥 Baixar AnyDesk**.\n\n"
            "**2️⃣ Abra o AnyDesk**\n"
            "Depois de baixar, abra o programa.\n\n"
            "**3️⃣ Localize seu ID**\n"
            "Procure o ID exibido na tela principal.\n\n"
            "**4️⃣ Envie seu ID**\n"
            "Clique em **🔢 Informar meu ID**.\n\n"
            "📌 Depois de enviar seu ID, aguarde a equipe."
        ),
        color=discord.Color.green(),
    )

    embed.add_field(
        name="📥 Download",
        value=(
            "Clique em **📥 Baixar AnyDesk**."
        ),
        inline=False,
    )

    embed.add_field(
        name="🔢 Enviar ID",
        value=(
            "Depois de abrir o AnyDesk, "
            "clique em **🔢 Informar meu ID**."
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

            bot_member = (
                await guild.fetch_member(
                    bot.user.id
                )
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

    try:

        canal = await guild.create_text_channel(
            name="🟡・aguardando-pagamento",
            category=categoria,
            topic=(
                f"Cliente: {membro.id} | "
                f"ProdutoID: {produto_id}"
            ),
            overwrites=overwrites,
            reason=f"Compra: {produto['nome']}",
        )

    except discord.Forbidden:

        await interaction.response.send_message(
            "❌ Não tenho permissão "
            "para criar o ticket.",
            ephemeral=True,
        )

        return

    except Exception as erro:

        print(
            f"❌ Erro criando ticket: {erro}"
        )

        await interaction.response.send_message(
            "❌ Ocorreu um erro ao "
            "criar o ticket.",
            ephemeral=True,
        )

        return

    embed = discord.Embed(
        title="🛒 PEDIDO",
        description=(
            f"📦 **Produto:** "
            f"{produto['nome']}\n"
            f"💰 **Valor:** "
            f"R${produto['preco']:.2f}\n"
            "🟡 **Status:** "
            "Aguardando pagamento\n\n"
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
            "Pagamento via PIX"
        )
    )

    try:

        await canal.send(
            content=membro.mention,
            embed=embed,
            view=TicketView(),
        )

    except Exception as erro:

        print(
            f"❌ Erro enviando painel: {erro}"
        )

        try:

            await canal.delete(
                reason="Erro ao enviar painel"
            )

        except Exception:
            pass

        await interaction.response.send_message(
            "❌ Não consegui configurar "
            "o ticket.",
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
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        await criar_ticket(
            interaction,
            "basica",
        )

    @discord.ui.button(
        label="Otimização Completa — R$30,00",
        emoji="🚀",
        style=discord.ButtonStyle.success,
        custom_id="otimizacao_completa",
    )
    async def completa(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        await criar_ticket(
            interaction,
            "completa",
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
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        await criar_ticket(
            interaction,
            "vitalicia",
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
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):

        await criar_ticket(
            interaction,
            "curso",
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

    canal_id = dados.get("channel_id")
    user_id = dados.get("user_id")
    produto_id = dados.get("produto_id")

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
            f"⚠️ Produto inválido: {produto_id}"
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
                f"⚠️ Canal {canal_id} não encontrado: "
                f"{erro}"
            )

            return False

    if not isinstance(
        canal,
        discord.TextChannel,
    ):

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
                f"⚠️ Cliente {user_id} não encontrado: "
                f"{erro}"
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
                f"⚠️ Cargo não encontrado: {cargo_id}"
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
                f"o cargo {cargo.name}."
            )

            falhou_cargo = True

        except Exception as erro:

            print(
                f"❌ Erro entregando cargo "
                f"{cargo.name}: {erro}"
            )

            falhou_cargo = True

    # Não marca como entregue se o bot
    # não conseguiu entregar algum cargo.
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
            f"⚠️ Erro alterando nome do ticket: {erro}"
        )

    embed = discord.Embed(
        title="🟢 PAGAMENTO APROVADO!",
        description=(
            f"Parabéns, "
            f"{membro.mention}! 🎉\n\n"
            "Seu pagamento foi confirmado "
            "**automaticamente pelo Mercado Pago**.\n\n"
            f"📦 **Produto:** "
            f"{produto['nome']}\n"
            f"💰 **Valor:** "
            f"R${produto['preco']:.2f}\n\n"
            "🎁 Seu acesso já foi liberado."
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
            f"❌ Erro enviando aprovação: {erro}"
        )

        return False

    tutorial_embed = criar_tutorial_embed()

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
            f"❌ Erro enviando tutorial: {erro}"
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
                f"❌ Erro imagem 2: {erro}"
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
                f"❌ Erro imagem 3: {erro}"
            )

    dados["status"] = "approved"
    dados["status_detail"] = "accredited"
    dados["entregue"] = True
    dados["approved_at"] = (
        datetime.now(
            FUSO_BRASILIA
        ).isoformat()
    )

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

        consulta = await asyncio.to_thread(
            consultar_pagamento,
            payment_id,
        )

        if not consulta:
            continue

        status = consulta.get(
            "status"
        )

        status_detail = consulta.get(
            "status_detail"
        )

        if (
            dados.get("status") != status
            or dados.get("status_detail") != status_detail
        ):

            dados["status"] = status
            dados["status_detail"] = status_detail

            alterou = True

            salvar_pagamentos()

        if status != "approved":
            continue

        print(
            f"🎉 PAGAMENTO APROVADO: {payment_id}"
        )

        sucesso = (
            await processar_pagamento_aprovado(
                payment_id,
                dados,
            )
        )

        if sucesso:

            alterou = True

            salvar_pagamentos()

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
            "🕐 Brasília: "
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
            "⚠️ Bot desconectado."
        )

    async def on_resumed(self):

        print(
            "🔄 Conexão restaurada."
        )

        await atualizar_status_loja()


bot = LojaBot()


# =========================================================
# PING
# =========================================================

@bot.command(name="ping")
@commands.has_permissions(
    administrator=True
)
async def ping(
    ctx: commands.Context,
):

    await ctx.send(
        f"🏓 Pong! "
        f"`{round(bot.latency * 1000)}ms`"
    )


@ping.error
async def ping_error(
    ctx: commands.Context,
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
    ctx: commands.Context,
):

    embed = discord.Embed(
        title="⚙️ TK OTIMIZAÇÃO",
        description=(
            "Escolha a otimização que "
            "deseja adquirir.\n\n"
            "⚙️ **Otimização Básica** — R$15,00\n"
            "🚀 **Otimização Completa** — R$30,00\n\n"
            "Após escolher, será criado "
            "um ticket privado."
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
    ctx: commands.Context,
):

    embed = discord.Embed(
        title="♾️ OTIMIZAÇÃO VITALÍCIA",
        description=(
            "Tenha acesso à "
            "**Otimização Completa Vitalícia**.\n\n"
            "♾️ **Valor: R$60,00**\n\n"
            "Clique no botão abaixo "
            "para abrir seu ticket."
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
    ctx: commands.Context,
):

    embed = discord.Embed(
        title="🎓 APRENDA A OTIMIZAR",
        description=(
            "Aprenda a otimizar "
            "seu próprio computador.\n\n"
            "🎓 **Curso completo — R$100,00**\n\n"
            "Clique no botão abaixo "
            "para adquirir o curso."
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
    ctx: commands.Context,
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
            "Configure DISCORD_TOKEN."
        )

    elif not MERCADOPAGO_ACCESS_TOKEN:

        print(
            "❌ BOT NÃO INICIADO!"
        )

        print(
            "Configure MERCADOPAGO_ACCESS_TOKEN."
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
                f"❌ Erro fatal ao iniciar bot: "
                f"{erro}"
            )
