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

# Versão dos painéis.
# Só aumente quando quiser forçar uma atualização dos painéis.
VERSAO_PAINEL = 3


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
        "⚠️ AVISO: MERCADOPAGO_ACCESS_TOKEN não configurado."
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

        return dados if isinstance(dados, dict) else {}

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
# COMO FUNCIONA
# =========================================================

COMO_FUNCIONA_TITULO = "🛒 COMO FUNCIONA A LOJA"

COMO_FUNCIONA_DESCRICAO = (
    "Bem-vindo à **Tk Otimização**! 🚀\n\n"

    "Aqui você encontra serviços de otimização "
    "para melhorar a experiência e o desempenho "
    "do seu computador.\n\n"

    "### 🛒 COMO COMPRAR\n\n"

    "1️⃣ **Escolha seu produto**\n"
    "Confira as opções disponíveis nos painéis "
    "abaixo e escolha a que melhor atende às suas "
    "necessidades.\n\n"

    "2️⃣ **Abra seu ticket**\n"
    "Clique no botão do produto desejado. "
    "O sistema criará um ticket privado para "
    "você e nossa equipe.\n\n"

    "3️⃣ **Gere seu PIX**\n"
    "Dentro do ticket, clique em **💳 Pagar com PIX** "
    "e informe seu e-mail para gerar o pagamento.\n\n"

    "4️⃣ **Pague**\n"
    "Faça o pagamento utilizando o QR Code ou "
    "Pix Copia e Cola.\n\n"

    "5️⃣ **Confirmação automática**\n"
    "Assim que o Mercado Pago confirmar o pagamento, "
    "o sistema reconhecerá automaticamente.\n\n"

    "6️⃣ **Atendimento liberado**\n"
    "Depois da confirmação, seu acesso será liberado "
    "e você receberá as instruções necessárias.\n\n"

    "━━━━━━━━━━━━━━━━━━━━\n\n"

    "🕐 **HORÁRIO:** 13:00 às 21:00\n"
    "💳 **PAGAMENTO:** PIX\n"
    "🎫 **ATENDIMENTO:** TICKET PRIVADO\n"
    "🔒 **SEGURANÇA:** Cada ticket é privado "
    "e visível apenas para o cliente e a equipe."
)


def criar_painel_como_funciona():

    embed = discord.Embed(
        title=COMO_FUNCIONA_TITULO,
        description=COMO_FUNCIONA_DESCRICAO,
        color=discord.Color.blurple(),
    )

    embed.set_footer(
        text=NOME_LOJA
    )

    return embed


async def atualizar_painel_como_funciona():

    canal = bot.get_channel(
        CANAL_INFORMACOES
    )

    if canal is None:

        try:
            canal = await bot.fetch_channel(
                CANAL_INFORMACOES
            )

        except discord.NotFound:
            print(
                "❌ Canal Como Funciona não encontrado."
            )
            return

        except discord.Forbidden:
            print(
                "❌ Sem permissão no canal Como Funciona."
            )
            return

        except Exception as erro:
            print(
                f"❌ Erro acessando Como Funciona: {erro}"
            )
            return

    if not isinstance(
        canal,
        discord.TextChannel,
    ):
        return

    embed = criar_painel_como_funciona()

    try:

        painel_existente = None

        async for mensagem in canal.history(
            limit=100
        ):

            if mensagem.author.id != bot.user.id:
                continue

            if not mensagem.embeds:
                continue

            if (
                mensagem.embeds[0].title
                == COMO_FUNCIONA_TITULO
            ):

                painel_existente = mensagem
                break

        if painel_existente:

            await painel_existente.edit(
                embed=embed
            )

            print(
                "✅ Painel Como Funciona atualizado."
            )

        else:

            await canal.send(
                embed=embed
            )

            print(
                "✅ Painel Como Funciona criado."
            )

    except Exception as erro:

        print(
            f"❌ Erro atualizando Como Funciona: {erro}"
        )


# =========================================================
# PAINEL OTIMIZAÇÃO
# =========================================================

def criar_painel_otimizacao():

    embed = discord.Embed(
        title="⚙️ TK OTIMIZAÇÃO",
        description=(
            "🚀 **DEIXE SEU COMPUTADOR MAIS OTIMIZADO!**\n\n"

            "Nossa equipe realiza uma configuração "
            "voltada para melhorar o desempenho do seu "
            "computador e proporcionar uma experiência "
            "mais estável durante o uso e nos jogos.\n\n"

            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "⚙️ **OTIMIZAÇÃO BÁSICA — R$15,00**\n\n"
            "Uma opção para quem procura uma otimização "
            "mais acessível, com ajustes essenciais "
            "no sistema.\n\n"

            "🚀 **OTIMIZAÇÃO COMPLETA — R$30,00**\n\n"
            "Uma otimização mais completa, com uma "
            "quantidade maior de ajustes para buscar "
            "um melhor desempenho geral do computador.\n\n"

            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "🎫 Após escolher seu produto, um **ticket "
            "privado** será criado automaticamente.\n\n"

            "💳 O pagamento é realizado via **PIX**.\n"
            "🤖 A confirmação do pagamento é automática.\n\n"

            "⚠️ **IMPORTANTE:** Escolha o produto que "
            "corresponde ao serviço que deseja adquirir."
        ),
        color=discord.Color.blurple(),
    )

    embed.set_footer(
        text=f"{NOME_LOJA} • Painel v{VERSAO_PAINEL}"
    )

    return embed


# =========================================================
# PAINEL VITALÍCIA
# =========================================================

def criar_painel_vitalicia():

    embed = discord.Embed(
        title="♾️ OTIMIZAÇÃO COMPLETA VITALÍCIA",
        description=(
            "🔥 **OTIMIZE SEU COMPUTADOR SEM LIMITE!**\n\n"

            "Com a **Otimização Completa Vitalícia**, "
            "você garante acesso ao serviço de otimização "
            "com a nossa equipe de forma recorrente.\n\n"

            "♾️ **VALOR: R$60,00**\n\n"

            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "### ♾️ COMO FUNCIONA?\n\n"

            "Você compra a Vitalícia **uma única vez** "
            "e pode solicitar a otimização novamente "
            "quando quiser.\n\n"

            "📅 **Exemplo:**\n"
            "Você compra hoje e realiza sua otimização "
            "agora. Se futuramente quiser realizar "
            "outra otimização, poderá solicitar "
            "novamente sem precisar comprar a "
            "Vitalícia outra vez.\n\n"

            "🔁 **O acesso é recorrente.**\n"
            "Não é uma otimização de uso único.\n\n"

            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "🎫 Após clicar no botão, será criado um "
            "ticket privado para seu atendimento.\n\n"

            "💳 Pagamento via **PIX**.\n"
            "🤖 Confirmação automática.\n"
            "♾️ Acesso vitalício ao serviço."
        ),
        color=discord.Color.green(),
    )

    embed.set_footer(
        text=f"{NOME_LOJA} • Painel v{VERSAO_PAINEL}"
    )

    return embed


# =========================================================
# PAINEL CURSO
# =========================================================

def criar_painel_curso():

    embed = discord.Embed(
        title="🎓 APRENDA A OTIMIZAR",
        description=(
            "🧠 **APRENDA A FAZER SUAS PRÓPRIAS OTIMIZAÇÕES!**\n\n"

            "Quer entender melhor como otimizar seu "
            "próprio computador?\n\n"

            "O **Aprenda a Otimizar** foi criado para "
            "quem quer aprender e entender melhor os "
            "ajustes de desempenho do Windows e do PC.\n\n"

            "🎓 **CURSO COMPLETO — R$100,00**\n\n"

            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "📚 Conteúdo voltado para aprendizado.\n"
            "🧠 Aprenda a entender os principais ajustes.\n"
            "⚙️ Aprenda conceitos de otimização.\n"
            "💻 Tenha mais conhecimento para configurar "
            "seu próprio computador.\n\n"

            "━━━━━━━━━━━━━━━━━━━━\n\n"

            "🎫 Após escolher o curso, será criado um "
            "ticket privado para atendimento.\n\n"

            "💳 Pagamento via **PIX**.\n"
            "🤖 Confirmação automática."
        ),
        color=discord.Color.blurple(),
    )

    embed.set_footer(
        text=f"{NOME_LOJA} • Painel v{VERSAO_PAINEL}"
    )

    return embed


# =========================================================
# ATUALIZAR PAINÉIS
# =========================================================

async def atualizar_painel_produto(
    canal_id: int,
    embed: discord.Embed,
    view: View,
):

    canal = bot.get_channel(
        canal_id
    )

    if canal is None:

        try:
            canal = await bot.fetch_channel(
                canal_id
            )

        except Exception as erro:

            print(
                f"❌ Erro acessando canal {canal_id}: {erro}"
            )
            return

    if not isinstance(
        canal,
        discord.TextChannel,
    ):
        return

    titulo = embed.title

    rodape_atual = (
        f"{NOME_LOJA} • Painel v{VERSAO_PAINEL}"
    )

    painel_atual = None
    paineis_antigos = []

    try:

        async for mensagem in canal.history(
            limit=100
        ):

            if mensagem.author.id != bot.user.id:
                continue

            if not mensagem.embeds:
                continue

            primeiro_embed = mensagem.embeds[0]

            if primeiro_embed.title != titulo:
                continue

            footer_text = (
                primeiro_embed.footer.text
                if primeiro_embed.footer
                else ""
            )

            if footer_text == rodape_atual:

                painel_atual = mensagem
                break

            paineis_antigos.append(
                mensagem
            )

        # =================================================
        # PAINEL ATUAL JÁ EXISTE
        # =================================================

        if painel_atual is not None:

            print(
                f"✅ Painel v{VERSAO_PAINEL} já existe "
                f"em #{canal.name}."
            )

            return

        # =================================================
        # APAGA VERSÕES ANTIGAS
        # =================================================

        apagados = 0

        for mensagem_antiga in paineis_antigos:

            try:

                await mensagem_antiga.delete(
                    reason=(
                        f"Atualização para painel "
                        f"v{VERSAO_PAINEL}"
                    )
                )

                apagados += 1

            except discord.NotFound:
                pass

            except Exception as erro:

                print(
                    f"⚠️ Erro apagando painel antigo: {erro}"
                )

        # =================================================
        # ENVIA NOVO PAINEL
        # =================================================

        nova_mensagem = await canal.send(
            embed=embed,
            view=view,
        )

        print(
            f"🆕 Painel v{VERSAO_PAINEL} criado em "
            f"#{canal.name}. "
            f"Antigos apagados: {apagados}"
        )

    except discord.Forbidden:

        print(
            f"❌ Sem permissão para editar "
            f"#{canal.name}."
        )

    except Exception as erro:

        print(
            f"❌ Erro atualizando #{canal.name}: {erro}"
        )


async def atualizar_paineis_produtos():

    await atualizar_painel_produto(
        CANAL_OTIMIZACAO,
        criar_painel_otimizacao(),
        OtimizacaoView(),
    )

    await atualizar_painel_produto(
        CANAL_VITALICIA,
        criar_painel_vitalicia(),
        VitaliciaView(),
    )

    await atualizar_painel_produto(
        CANAL_CURSO,
        criar_painel_curso(),
        CursoView(),
    )


# =========================================================
# STATUS DA LOJA
# =========================================================

def loja_esta_aberta():

    agora = datetime.now(
        FUSO_BRASILIA
    )

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
                f"❌ Erro encontrando canal de status: {erro}"
            )
            return

    if not isinstance(
        canal,
        discord.TextChannel,
    ):
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
            reason="Atualização automática da loja",
        )

        agora = datetime.now(
            FUSO_BRASILIA
        )

        print(
            f"🏪 Status: {novo_nome} | "
            f"{agora.strftime('%d/%m/%Y %H:%M:%S')}"
        )

    except discord.Forbidden:

        print(
            "❌ Sem permissão para alterar "
            "o canal de status."
        )

    except Exception as erro:

        print(
            f"❌ Erro alterando status: {erro}"
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
            "❌ Mercado Pago não configurado."
        )

        return None

    email = email.strip().lower()

    if "@" not in email:
        return None

    parte_dominio = email.split(
        "@",
        1
    )[1]

    if "." not in parte_dominio:
        return None

    url = (
        "https://api.mercadopago.com/v1/payments"
    )

    external_reference = (
        f"discord-{canal_id}-{usuario_id}-"
        f"{uuid.uuid4().hex}"
    )

    idempotency_key = str(
        uuid.uuid4()
    )

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

    print(
        f"💳 Criando PIX: {produto} | "
        f"R${preco:.2f}"
    )

    try:

        resposta = requests.post(
            url,
            headers=headers,
            json=dados,
            timeout=30,
        )

    except requests.RequestException as erro:

        print(
            f"❌ Erro Mercado Pago: {erro}"
        )

        return None

    try:

        pagamento = resposta.json()

    except ValueError:

        print(
            "❌ Mercado Pago retornou JSON inválido."
        )

        return None

    if resposta.status_code not in (
        200,
        201,
    ):

        print(
            "❌ ERRO MERCADO PAGO:"
        )

        print(
            json.dumps(
                pagamento,
                indent=4,
                ensure_ascii=False,
            )
        )

        return None

    payment_id = pagamento.get(
        "id"
    )

    if not payment_id:
        return None

    point_of_interaction = (
        pagamento.get(
            "point_of_interaction",
            {}
        )
    )

    transaction_data = (
        point_of_interaction.get(
            "transaction_data",
            {}
        )
    )

    pix_copia_cola = (
        transaction_data.get(
            "qr_code"
        )
    )

    qr_code_base64 = (
        transaction_data.get(
            "qr_code_base64"
        )
    )

    ticket_url = (
        transaction_data.get(
            "ticket_url"
        )
    )

    if not pix_copia_cola:

        print(
            "❌ Pix Copia e Cola não retornado."
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
# CONSULTAR PAGAMENTO
# =========================================================

def consultar_pagamento(
    payment_id: str
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

    except requests.RequestException:

        return None

    if resposta.status_code != 200:
        return None

    try:

        dados = resposta.json()

    except ValueError:

        return None

    return {
        "status": dados.get(
            "status"
        ),
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
# ENCONTRAR TICKET DO USUÁRIO
# =========================================================

def encontrar_ticket_usuario(
    guild: discord.Guild,
    usuario_id: int,
):

    for canal in guild.text_channels:

        topic = canal.topic or ""

        cliente = (
            f"Cliente: {usuario_id}"
        )

        produto = "ProdutoID:"

        if (
            cliente in topic
            and produto in topic
        ):

            return canal

    return None


# =========================================================
# MODAL E-MAIL
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
                "❌ Não consegui gerar o PIX.\n\n"
                "Verifique o Mercado Pago e "
                "o e-mail informado.",
                ephemeral=True,
            )

            return

        pagamento_id = resultado["id"]
        pix = resultado.get("qr_code")

        if not pix:

            await interaction.followup.send(
                "❌ O Mercado Pago não retornou "
                "o Pix Copia e Cola.",
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
            value=f"```text\n{pix}\n```",
            inline=False,
        )

        embed.set_footer(
            text="Confirmação automática via Mercado Pago."
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
                    f"❌ Erro QR Code: {erro}"
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

        except Exception as erro:

            print(
                f"❌ Erro enviando PIX: {erro}"
            )

            await interaction.followup.send(
                "❌ O PIX foi criado, mas "
                "não consegui enviar no ticket.",
                ephemeral=True,
            )

            return

        await interaction.followup.send(
            "✅ **PIX gerado!**\n\n"
            "Faça o pagamento pelo QR Code "
            "ou Pix Copia e Cola.\n\n"
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

            for anexo in mensagem.attachments:

                linhas.append(
                    f"[Anexo] {anexo.filename}: "
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
            f"[ERRO] {erro}"
        )

        print(
            f"❌ Erro transcript: {erro}"
        )

    linhas.extend(
        [
            "==================================================",
            "Fim do transcript.",
        ]
    )

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

        if parte.startswith(
            "Cliente:"
        ):

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
                "⚠️ Cliente não encontrado.\n\n"
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
                "⚠️ Não consegui enviar o transcript "
                "no PV do cliente.\n\n"
                "O ticket não será excluído."
            )
        )

        return

    except Exception as erro:

        print(
            f"❌ Erro enviando transcript: {erro}"
        )

        await interaction.edit_original_response(
            content=(
                "⚠️ Erro enviando transcript.\n\n"
                "O ticket não será excluído."
            )
        )

        return

    await interaction.edit_original_response(
        content=(
            "✅ **Transcript enviado no PV!**\n\n"
            "🗑️ O ticket será excluído em **3 segundos**."
        )
    )

    await asyncio.sleep(3)

    try:

        await canal.delete(
            reason=(
                "Ticket fechado — transcript enviado"
            )
        )

    except discord.NotFound:
        pass

    except Exception as erro:

        print(
            f"❌ Erro excluindo ticket: {erro}"
        )


# =========================================================
# VIEW TICKET
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
                "❌ Produto não identificado.",
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
            "🔒 Fechando o ticket e preparando o transcript..."
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
        interaction,
    ):

        embed = discord.Embed(
            title="🖥️ ID DO ANYDESK RECEBIDO",
            description=(
                f"👤 **Cliente:** "
                f"{interaction.user.mention}\n\n"
                f"🔢 **ID:** "
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
            )
        )

    @discord.ui.button(
        label="Informar meu ID",
        emoji="🔢",
        style=discord.ButtonStyle.primary,
        custom_id="tutorial_informar_id",
    )
    async def informar_id(
        self,
        interaction,
        button,
    ):

        await interaction.response.send_modal(
            AnyDeskModal()
        )


def criar_tutorial_embed():

    embed = discord.Embed(
        title="🖥️ ACESSO LIBERADO — TUTORIAL ANYDESK",
        description=(
            "Seu pagamento foi **confirmado com sucesso!** 🎉\n\n"

            "Agora siga as instruções abaixo para "
            "realizar seu atendimento.\n\n"

            "**1️⃣ Baixe o AnyDesk**\n"
            "Clique em **📥 Baixar AnyDesk**.\n\n"

            "**2️⃣ Abra o AnyDesk**\n"
            "Depois de instalar/abrir o programa, "
            "localize a tela principal.\n\n"

            "**3️⃣ Localize seu ID**\n"
            "O AnyDesk exibirá um número de identificação.\n\n"

            "**4️⃣ Envie seu ID**\n"
            "Clique em **🔢 Informar meu ID** e envie "
            "o número para a equipe.\n\n"

            "📌 Depois de enviar, aguarde o atendimento."
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
        name="🔢 Seu ID",
        value=(
            "Clique em **🔢 Informar meu ID**."
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

    if guild is None:

        await interaction.response.send_message(
            "❌ Esse botão só funciona dentro do servidor.",
            ephemeral=True,
        )

        return

    membro = interaction.user

    # =====================================================
    # PROTEÇÃO CONTRA TICKET DUPLICADO
    # =====================================================

    ticket_existente = encontrar_ticket_usuario(
        guild,
        membro.id,
    )

    if ticket_existente:

        await interaction.response.send_message(
            (
                "❌ **Você já possui um ticket aberto!**\n\n"
                f"🎫 Seu ticket: {ticket_existente.mention}\n\n"
                "Finalize ou feche o ticket atual "
                "antes de abrir outro."
            ),
            ephemeral=True,
        )

        print(
            f"⚠️ Ticket duplicado bloqueado: "
            f"{membro} ({membro.id})"
        )

        return

    categoria = (
        interaction.channel.category
        if isinstance(
            interaction.channel,
            discord.TextChannel,
        )
        else None
    )

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
            "❌ Não consegui verificar as permissões do bot.",
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
            "❌ Não tenho permissão para criar tickets.",
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

            "🟡 **Status:** Aguardando pagamento\n\n"

            "Clique em **💳 Pagar com PIX** "
            "para gerar seu pagamento.\n\n"

            "Após o pagamento ser aprovado pelo "
            "Mercado Pago, a confirmação será "
            "**automática**.\n\n"

            "🔒 Este ticket é privado e foi criado "
            "exclusivamente para seu atendimento."
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
                "A equipe foi notificada."
            ),
            embed=embed,
            view=TicketView(),
        )

    except Exception as erro:

        print(
            f"❌ Erro painel ticket: {erro}"
        )

        try:

            await canal.delete(
                reason="Erro ao configurar ticket"
            )

        except Exception:
            pass

        await interaction.response.send_message(
            "❌ Não consegui configurar o ticket.",
            ephemeral=True,
        )

        return

    await interaction.response.send_message(
        f"✅ **Seu ticket foi criado!**\n{canal.mention}",
        ephemeral=True,
    )


# =========================================================
# VIEWS DOS PAINÉIS
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


class VitaliciaView(View):

    def __init__(self):

        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Vitalícia — R$60,00",
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
# PAGAMENTO APROVADO
# =========================================================

async def processar_pagamento_aprovado(
    payment_id: str,
    dados: dict,
):

    if dados.get(
        "entregue"
    ) is True:

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

        return False

    produto = PRODUTOS.get(
        produto_id
    )

    if not produto:

        return False

    canal = bot.get_channel(
        int(canal_id)
    )

    if canal is None:

        try:

            canal = await bot.fetch_channel(
                int(canal_id)
            )

        except Exception:

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

        except Exception:

            return False

    falhou_cargo = False
    cargos = []

    for cargo_id in produto["cargos"]:

        cargo = guild.get_role(
            cargo_id
        )

        if not cargo:

            falhou_cargo = True
            continue

        try:

            if cargo not in membro.roles:

                await membro.add_roles(
                    cargo,
                    reason=(
                        "Pagamento PIX aprovado"
                    ),
                )

            cargos.append(
                cargo.mention
            )

        except Exception as erro:

            print(
                f"❌ Erro entregando cargo: {erro}"
            )

            falhou_cargo = True

    if falhou_cargo:

        return False

    try:

        await canal.edit(
            name="🟢・pago"
        )

    except Exception:
        pass

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

            "🎁 Seu acesso foi liberado.\n\n"

            "Agora siga as instruções abaixo "
            "para continuar o atendimento."
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
        text=f"{NOME_LOJA} • Pagamento confirmado"
    )

    try:

        await canal.send(
            embed=embed
        )

    except Exception:

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
            f"❌ Erro tutorial: {erro}"
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

        except Exception:
            pass

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

        except Exception:
            pass

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

        if dados.get(
            "entregue"
        ) is True:

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

        # Views persistentes.
        # Isso faz os botões continuarem funcionando
        # mesmo depois do bot reiniciar.

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

        # =================================================
        # IMPORTANTE:
        # NÃO CRIA TICKETS NO on_ready.
        #
        # Apenas atualiza os painéis/status.
        # Tickets existentes continuam onde estão.
        # =================================================

        await atualizar_status_loja()

        await atualizar_painel_como_funciona()

        await atualizar_paineis_produtos()

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
            "🔄 Conexão restaurada."
        )

        await atualizar_status_loja()

        await atualizar_painel_como_funciona()

        await atualizar_paineis_produtos()


bot = LojaBot()


# =========================================================
# PING
# =========================================================

@bot.command(
    name="ping"
)
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
# COMANDO PAINEL OTIMIZAÇÃO
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

    await ctx.send(
        embed=criar_painel_otimizacao(),
        view=OtimizacaoView(),
    )


# =========================================================
# COMANDO PAINEL VITALÍCIA
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

    await ctx.send(
        embed=criar_painel_vitalicia(),
        view=VitaliciaView(),
    )


# =========================================================
# COMANDO PAINEL CURSO
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

    await ctx.send(
        embed=criar_painel_curso(),
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
            "Configure DISCORD_TOKEN no Laplace."
        )

    elif not MERCADOPAGO_ACCESS_TOKEN:

        print(
            "❌ BOT NÃO INICIADO!"
        )

        print(
            "Configure MERCADOPAGO_ACCESS_TOKEN no Laplace."
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
                f"❌ Erro fatal: {erro}"
            )
