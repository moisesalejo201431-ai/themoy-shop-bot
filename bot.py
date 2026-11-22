import asyncio
import sqlite3
import time
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
)

# ================= CONFIGURACIÓN =================
TOKEN = "9288338809:AAHwkYmVqmb29kAfjUOIB18ZINm0OYWwNYg"
ADMIN_IDS = {7922103965}
ADMIN_PASSWORD = "tupapi31"

BANNER_PATH = "banner_themoy.jpg"
DB_PATH = "bot_data.db"

REQUIRED_CHANNEL = "@CPMSTOREVIP"
REQUIRED_CHANNEL_URL = "https://t.me/CPMSTOREVIP"
REQUIRED_BOT_USERNAME = "TheMoyShop_bot"
REQUIRED_BOT_URL = "https://t.me/TheMoyShop_bot"

DEFAULT_FREE_COOLDOWN = 180  # 3 minutos en plan gratis


# ================= ESTADOS FSM =================
class RedeemStates(StatesGroup):
  waiting_for_code = State()


class AdminAuthStates(StatesGroup):
  waiting_password = State()


class AdminStates(StatesGroup):
  waiting_bulk_accounts = State()
  waiting_new_code = State()
  waiting_grant_vip = State()


# ================= IDIOMAS (6) =================
LANGUAGES = {
    "es": "🇪🇸 Español",
    "en": "🇺🇸 English",
    "pt": "🇧🇷 Português",
    "fr": "🇫🇷 Français",
    "ru": "🇷🇺 Русский",
    "ar": "🇸🇦 العربية",
}

TEXTS = {
    "es": {
        "choose_lang": (
            "🌐 <b>Selecciona tu idioma / Choose your language:</b>\n\n"
            "Todos los textos del bot aparecerán en el idioma que elijas."
        ),
        "lang_saved": "✅ Idioma configurado en <b>Español</b>.",
        "join_req": (
            "🔒 <b>REQUISITOS PARA EL PLAN GRATIS — THEMOY SHOP</b>\n\n"
            "Para activar y reclamar cuentas gratis debes:\n"
            "1. Unirte a nuestro canal: <a href='{ch_url}'>{ch_name}</a>\n"
            "2. Abrir e iniciar nuestro bot: <a href='{bot_url}'>@{bot_user}</a>\n\n"
            "Luego toca <b>✅ Ya cumplí los requisitos</b>."
        ),
        "btn_channel": "📢 Unirse al canal",
        "btn_bot": "🤖 Abrir @TheMoyShop_bot",
        "btn_check": "✅ Ya cumplí los requisitos",
        "not_in_channel": (
            "⚠️ Aún no detectamos que estés unido a <b>{ch_name}</b>."
        ),
        "not_started_bot": (
            "⚠️ Recuerda abrir y presionar /start en <b>@{bot_user}</b> y"
            " confirmar aquí."
        ),
        "unlocked": "🎉 ¡Requisitos cumplidos! Plan gratis activado.",
        "menu_title": (
            "🛍️ <b>THEMOY SHOP — MENÚ PRINCIPAL</b>\n\n"
            "Elige una opción del menú:"
        ),
        "btn_claim": "🎁 Reclamar cuenta",
        "btn_cooldown": "⏳ Tiempo restante",
        "btn_history": "📂 Mis cuentas",
        "btn_vip": "💎 Planes VIP",
        "btn_sub": "📋 Mi suscripción",
        "btn_redeem": "🎟️ Canjear código",
        "no_stock": (
            "⚠️ Por el momento no hay cuentas disponibles en stock. Inténtalo"
            " más tarde."
        ),
        "cooldown_active": (
            "⏳ Aún debes esperar <b>{rem}</b> para reclamar otra cuenta."
        ),
        "cooldown_ready": "✅ ¡No tienes tiempo de espera! Ya puedes reclamar.",
        "claim_msg1": (
            "🎉 <b>¡CUENTA RECLAMADA — THEMOY SHOP!</b>\n\n"
            "👤 Usuario/Correo: <code>{user}</code>\n"
            "🔑 Contraseña: <code>{pwd}</code>"
        ),
        "claim_msg2": (
            "⚡ Tu próximo reclamo estará disponible en: <b>{cd_text}</b>."
        ),
        "history_empty": "📂 Aún no has reclamado cuentas.",
        "history_title": "📂 <b>TUS ÚLTIMAS CUENTAS RECLAMADAS</b>\n\n",
        "vip_info": (
            "💎 <b>PLANES VIP — THEMOY SHOP</b>\n\n"
            "• 1 día — 5 ⭐ (1 cuenta cada 3 min)\n"
            "• 5 días — 15 ⭐ (1 cuenta cada 1:30 min)\n"
            "• 15 días (-20%) — 35 ⭐ (1 cuenta cada 1 min)\n"
            "• 30 días (-20%) — 60 ⭐ (1 cuenta cada 30 s)\n"
            "• 3 meses — 150 ⭐ (1 cuenta cada 30 s)\n"
            "• 5 meses — 220 ⭐ (1 cuenta cada 5 s)\n"
            "• 8 meses — 300 ⭐ (1 cuenta cada 5 s)\n"
            "• 1 año — 400 ⭐ (1 cuenta cada 5 s)\n\n"
            "Canjea un código con <b>🎟️ Canjear código</b> o solicita tu plan"
            " con el administrador."
        ),
        "sub_active": (
            "📋 <b>ESTADO DE SUSCRIPCIÓN</b>\n\n"
            "Estado: <b>Activa ✅</b>\n"
            "📦 Plan: <b>{plan}</b>\n"
            "⚡ Velocidad: <b>1 cuenta cada {cd}</b>\n"
            "⏳ Tiempo restante: <b>{rem}</b>"
        ),
        "sub_free": (
            "📋 <b>ESTADO DE SUSCRIPCIÓN</b>\n\n"
            "Estado: <b>Sin suscripción activa (Plan Gratis)</b>\n"
            "⏳ Tiempo restante de plan: <b>No aplica</b>\n\n"
            "💎 Activa un plan para reclamar cuentas mucho más rápido."
        ),
        "ask_code": (
            "🎟️ <b>CANJEAR CÓDIGO</b>\n\n"
            "Escribe o pega tu código para activar tu plan:"
        ),
        "cancelled": "❌ Acción cancelada.",
    },
    "en": {
        "choose_lang": (
            "🌐 <b>Choose your language:</b>\n\n"
            "Every bot message will appear in your selected language."
        ),
        "lang_saved": "✅ Language set to <b>English</b>.",
        "join_req": (
            "🔒 <b>FREE PLAN REQUIREMENTS — THEMOY SHOP</b>\n\n"
            "To activate and claim free accounts you must:\n"
            "1. Join our channel: <a href='{ch_url}'>{ch_name}</a>\n"
            "2. Open and start our bot: <a href='{bot_url}'>@{bot_user}</a>\n\n"
            "Then tap <b>✅ I completed the requirements</b>."
        ),
        "btn_channel": "📢 Join Channel",
        "btn_bot": "🤖 Open @TheMoyShop_bot",
        "btn_check": "✅ I completed the requirements",
        "not_in_channel": (
            "⚠️ We couldn't verify your membership in <b>{ch_name}</b> yet."
        ),
        "not_started_bot": (
            "⚠️ Please open and start <b>@{bot_user}</b>, then confirm here."
        ),
        "unlocked": "🎉 Requirements completed! Free plan activated.",
        "menu_title": (
            "🛍️ <b>THEMOY SHOP — MAIN MENU</b>\n\n"
            "Choose an option from the menu:"
        ),
        "btn_claim": "🎁 Claim account",
        "btn_cooldown": "⏳ Cooldown left",
        "btn_history": "📂 My accounts",
        "btn_vip": "💎 VIP Plans",
        "btn_sub": "📋 My subscription",
        "btn_redeem": "🎟️ Redeem code",
        "no_stock": (
            "⚠️ No accounts available in stock right now. Please try again"
            " later."
        ),
        "cooldown_active": (
            "⏳ You still have to wait <b>{rem}</b> to claim another account."
        ),
        "cooldown_ready": "✅ No cooldown! You can claim an account now.",
        "claim_msg1": (
            "🎉 <b>ACCOUNT CLAIMED — THEMOY SHOP!</b>\n\n"
            "👤 User/Email: <code>{user}</code>\n"
            "🔑 Password: <code>{pwd}</code>"
        ),
        "claim_msg2": "⚡ Your next claim will be available in: <b>{cd_text}</b>.",
        "history_empty": "📂 You haven't claimed any accounts yet.",
        "history_title": "📂 <b>YOUR RECENT CLAIMED ACCOUNTS</b>\n\n",
        "vip_info": (
            "💎 <b>VIP PLANS — THEMOY SHOP</b>\n\n"
            "• 1 day — 5 ⭐ (1 account every 3 min)\n"
            "• 5 days — 15 ⭐ (1 account every 1:30 min)\n"
            "• 15 days (-20%) — 35 ⭐ (1 account every 1 min)\n"
            "• 30 days (-20%) — 60 ⭐ (1 account every 30 s)\n"
            "• 3 months — 150 ⭐ (1 account every 30 s)\n"
            "• 5 months — 220 ⭐ (1 account every 5 s)\n"
            "• 8 months — 300 ⭐ (1 account every 5 s)\n"
            "• 1 year — 400 ⭐ (1 account every 5 s)\n\n"
            "Redeem a code with <b>🎟️ Redeem code</b> or contact the admin."
        ),
        "sub_active": (
            "📋 <b>SUBSCRIPTION STATUS</b>\n\n"
            "Status: <b>Active ✅</b>\n"
            "📦 Plan: <b>{plan}</b>\n"
            "⚡ Speed: <b>1 account every {cd}</b>\n"
            "⏳ Time remaining: <b>{rem}</b>"
        ),
        "sub_free": (
            "📋 <b>SUBSCRIPTION STATUS</b>\n\n"
            "Status: <b>No active subscription (Free Plan)</b>\n"
            "⏳ Plan time remaining: <b>Not applicable</b>\n\n"
            "💎 Activate a plan to claim accounts much faster."
        ),
        "ask_code": (
            "🎟️ <b>REDEEM CODE</b>\n\n"
            "Type or paste your code to activate your plan:"
        ),
        "cancelled": "❌ Action cancelled.",
    },
    "pt": {
        "choose_lang": (
            "🌐 <b>Escolha seu idioma:</b>\n\n"
            "Todos os textos do bot aparecerão no idioma escolhido."
        ),
        "lang_saved": "✅ Idioma definido para <b>Português</b>.",
        "join_req": (
            "🔒 <b>REQUISITOS DO PLANO GRÁTIS — THEMOY SHOP</b>\n\n"
            "Para ativar e resgatar contas grátis você precisa:\n"
            "1. Entrar no canal: <a href='{ch_url}'>{ch_name}</a>\n"
            "2. Abrir e iniciar o bot: <a href='{bot_url}'>@{bot_user}</a>\n\n"
            "Depois toque em <b>✅ Já cumpri os requisitos</b>."
        ),
        "btn_channel": "📢 Entrar no canal",
        "btn_bot": "🤖 Abrir @TheMoyShop_bot",
        "btn_check": "✅ Já cumpri os requisitos",
        "not_in_channel": (
            "⚠️ Ainda não confirmamos sua entrada em <b>{ch_name}</b>."
        ),
        "not_started_bot": (
            "⚠️ Abra e inicie <b>@{bot_user}</b> e depois confirme aqui."
        ),
        "unlocked": "🎉 Requisitos concluídos! Plano grátis ativado.",
        "menu_title": (
            "🛍️ <b>THEMOY SHOP — MENU PRINCIPAL</b>\n\n"
            "Escolha uma opção no menu:"
        ),
        "btn_claim": "🎁 Resgatar conta",
        "btn_cooldown": "⏳ Tempo restante",
        "btn_history": "📂 Minhas contas",
        "btn_vip": "💎 Planos VIP",
        "btn_sub": "📋 Minha assinatura",
        "btn_redeem": "🎟️ Resgatar código",
        "no_stock": (
            "⚠️ Sem contas disponíveis no estoque no momento. Tente novamente"
            " depois."
        ),
        "cooldown_active": (
            "⏳ Ainda faltam <b>{rem}</b> para resgatar outra conta."
        ),
        "cooldown_ready": "✅ Sem tempo de espera! Já pode resgatar.",
        "claim_msg1": (
            "🎉 <b>CONTA RESGATADA — THEMOY SHOP!</b>\n\n"
            "👤 Usuário/E-mail: <code>{user}</code>\n"
            "🔑 Senha: <code>{pwd}</code>"
        ),
        "claim_msg2": (
            "⚡ Seu próximo resgate estará disponível em: <b>{cd_text}</b>."
        ),
        "history_empty": "📂 Você ainda não resgatou nenhuma conta.",
        "history_title": "📂 <b>SUAS ÚLTIMAS CONTAS RESGATADAS</b>\n\n",
        "vip_info": (
            "💎 <b>PLANOS VIP — THEMOY SHOP</b>\n\n"
            "• 1 dia — 5 ⭐ (1 conta a cada 3 min)\n"
            "• 5 dias — 15 ⭐ (1 conta a cada 1:30 min)\n"
            "• 15 dias (-20%) — 35 ⭐ (1 conta a cada 1 min)\n"
            "• 30 dias (-20%) — 60 ⭐ (1 conta a cada 30 s)\n"
            "• 3 meses — 150 ⭐ (1 conta a cada 30 s)\n"
            "• 5 meses — 220 ⭐ (1 conta a cada 5 s)\n"
            "• 8 meses — 300 ⭐ (1 conta a cada 5 s)\n"
            "• 1 ano — 400 ⭐ (1 conta a cada 5 s)\n\n"
            "Resgate um código em <b>🎟️ Resgatar código</b> ou fale com o"
            " admin."
        ),
        "sub_active": (
            "📋 <b>STATUS DA ASSINATURA</b>\n\n"
            "Status: <b>Ativa ✅</b>\n"
            "📦 Plano: <b>{plan}</b>\n"
            "⚡ Velocidade: <b>1 conta a cada {cd}</b>\n"
            "⏳ Tempo restante: <b>{rem}</b>"
        ),
        "sub_free": (
            "📋 <b>STATUS DA ASSINATURA</b>\n\n"
            "Status: <b>Sem assinatura ativa (Plano Grátis)</b>\n"
            "⏳ Tempo restante do plano: <b>Não se aplica</b>\n\n"
            "💎 Ative um plano para resgatar contas muito mais rápido."
        ),
        "ask_code": (
            "🎟️ <b>RESGATAR CÓDIGO</b>\n\n"
            "Digite ou cole seu código para ativar seu plano:"
        ),
        "cancelled": "❌ Ação cancelada.",
    },
    "fr": {
        "choose_lang": (
            "🌐 <b>Choisissez votre langue :</b>\n\n"
            "Tous les textes du bot s'afficheront dans la langue choisie."
        ),
        "lang_saved": "✅ Langue définie sur <b>Français</b>.",
        "join_req": (
            "🔒 <b>CONDITIONS POUR L'OFFRE GRATUITE — THEMOY SHOP</b>\n\n"
            "Pour activer et réclamer des comptes gratuits :\n"
            "1. Rejoindre le canal : <a href='{ch_url}'>{ch_name}</a>\n"
            "2. Ouvrir et démarrer le bot : <a href='{bot_url}'>@{bot_user}</a>\n\n"
            "Puis appuyez sur <b>✅ J'ai rempli les conditions</b>."
        ),
        "btn_channel": "📢 Rejoindre le canal",
        "btn_bot": "🤖 Ouvrir @TheMoyShop_bot",
        "btn_check": "✅ J'ai rempli les conditions",
        "not_in_channel": (
            "⚠️ Nous ne voyons pas encore votre adhésion à <b>{ch_name}</b>."
        ),
        "not_started_bot": (
            "⚠️ Ouvrez et démarrez <b>@{bot_user}</b>, puis confirmez ici."
        ),
        "unlocked": "🎉 Conditions validées ! Offre gratuite activée.",
        "menu_title": (
            "🛍️ <b>THEMOY SHOP — MENU PRINCIPAL</b>\n\n"
            "Choisissez une option dans le menu :"
        ),
        "btn_claim": "🎁 Réclamer un compte",
        "btn_cooldown": "⏳ Temps restant",
        "btn_history": "📂 Mes comptes",
        "btn_vip": "💎 Offres VIP",
        "btn_sub": "📋 Mon abonnement",
        "btn_redeem": "🎟️ Utiliser un code",
        "no_stock": (
            "⚠️ Aucun compte disponible en stock pour le moment. Réessayez plus"
            " tard."
        ),
        "cooldown_active": (
            "⏳ Vous devez encore attendre <b>{rem}</b> avant le prochain"
            " compte."
        ),
        "cooldown_ready": (
            "✅ Aucun temps d'attente ! Vous pouvez réclamer un compte."
        ),
        "claim_msg1": (
            "🎉 <b>COMPTE RÉCLAMÉ — THEMOY SHOP !</b>\n\n"
            "👤 Identifiant/E-mail : <code>{user}</code>\n"
            "🔑 Mot de passe : <code>{pwd}</code>"
        ),
        "claim_msg2": (
            "⚡ Prochaine réclamation disponible dans : <b>{cd_text}</b>."
        ),
        "history_empty": "📂 Vous n'avez pas encore réclamé de compte.",
        "history_title": "📂 <b>VOS DERNIERS COMPTES RÉCLAMÉS</b>\n\n",
        "vip_info": (
            "💎 <b>OFFRES VIP — THEMOY SHOP</b>\n\n"
            "• 1 jour — 5 ⭐ (1 compte toutes les 3 min)\n"
            "• 5 jours — 15 ⭐ (1 compte toutes les 1:30 min)\n"
            "• 15 jours (-20%) — 35 ⭐ (1 compte toutes les 1 min)\n"
            "• 30 jours (-20%) — 60 ⭐ (1 compte toutes les 30 s)\n"
            "• 3 mois — 150 ⭐ (1 compte toutes les 30 s)\n"
            "• 5 mois — 220 ⭐ (1 compte toutes les 5 s)\n"
            "• 8 mois — 300 ⭐ (1 compte toutes les 5 s)\n"
            "• 1 an — 400 ⭐ (1 compte toutes les 5 s)\n\n"
            "Utilisez un code via <b>🎟️ Utiliser un code</b> ou contactez"
            " l'admin."
        ),
        "sub_active": (
            "📋 <b>STATUT DE L'ABONNEMENT</b>\n\n"
            "Statut : <b>Actif ✅</b>\n"
            "📦 Offre : <b>{plan}</b>\n"
            "⚡ Vitesse : <b>1 compte toutes les {cd}</b>\n"
            "⏳ Temps restant : <b>{rem}</b>"
        ),
        "sub_free": (
            "📋 <b>STATUT DE L'ABONNEMENT</b>\n\n"
            "Statut : <b>Aucun abonnement actif (Offre Gratuite)</b>\n"
            "⏳ Temps restant : <b>Non applicable</b>\n\n"
            "💎 Activez une offre pour réclamer des comptes plus rapidement."
        ),
        "ask_code": (
            "🎟️ <b>UTILISER UN CODE</b>\n\n"
            "Écrivez ou collez votre code pour activer votre offre :"
        ),
        "cancelled": "❌ Action annulée.",
    },
    "ru": {
        "choose_lang": (
            "🌐 <b>Выберите язык:</b>\n\n"
            "Все сообщения бота будут отображаться на выбранном языке."
        ),
        "lang_saved": "✅ Язык установлен: <b>Русский</b>.",
        "join_req": (
            "🔒 <b>УСЛОВИЯ БЕСПЛАТНОГО ТАРИФА — THEMOY SHOP</b>\n\n"
            "Чтобы активировать бесплатный доступ:\n"
            "1. Подпишитесь на канал: <a href='{ch_url}'>{ch_name}</a>\n"
            "2. Откройте и запустите бота: <a href='{bot_url}'>@{bot_user}</a>\n\n"
            "Затем нажмите <b>✅ Я выполнил условия</b>."
        ),
        "btn_channel": "📢 Перейти в канал",
        "btn_bot": "🤖 Открыть @TheMoyShop_bot",
        "btn_check": "✅ Я выполнил условия",
        "not_in_channel": (
            "⚠️ Пока не подтверждена подписка на <b>{ch_name}</b>."
        ),
        "not_started_bot": (
            "⚠️ Откройте и запустите <b>@{bot_user}</b>, затем подтвердите здесь."
        ),
        "unlocked": "🎉 Условия выполнены! Бесплатный тариф активирован.",
        "menu_title": (
            "🛍️ <b>THEMOY SHOP — ГЛАВНОЕ МЕНЮ</b>\n\n"
            "Выберите пункт меню:"
        ),
        "btn_claim": "🎁 Получить аккаунт",
        "btn_cooldown": "⏳ Оставшееся время",
        "btn_history": "📂 Мои аккаунты",
        "btn_vip": "💎 VIP тарифы",
        "btn_sub": "📋 Моя подписка",
        "btn_redeem": "🎟️ Активировать код",
        "no_stock": (
            "⚠️ Сейчас нет доступных аккаунтов. Попробуйте позже."
        ),
        "cooldown_active": (
            "⏳ До следующего получения аккаунта осталось <b>{rem}</b>."
        ),
        "cooldown_ready": "✅ Ожидания нет! Можно получить аккаунт.",
        "claim_msg1": (
            "🎉 <b>АККАУНТ ПОЛУЧЕН — THEMOY SHOP!</b>\n\n"
            "👤 Логин/Почта: <code>{user}</code>\n"
            "🔑 Пароль: <code>{pwd}</code>"
        ),
        "claim_msg2": (
            "⚡ Следующий аккаунт будет доступен через: <b>{cd_text}</b>."
        ),
        "history_empty": "📂 Вы ещё не получали аккаунты.",
        "history_title": "📂 <b>ВАШИ ПОСЛЕДНИЕ АККАУНТЫ</b>\n\n",
        "vip_info": (
            "💎 <b>VIP ТАРИФЫ — THEMOY SHOP</b>\n\n"
            "• 1 день — 5 ⭐ (1 аккаунт каждые 3 мин)\n"
            "• 5 дней — 15 ⭐ (1 аккаунт каждые 1:30 мин)\n"
            "• 15 дней (-20%) — 35 ⭐ (1 аккаунт каждую 1 мин)\n"
            "• 30 дней (-20%) — 60 ⭐ (1 аккаунт каждые 30 сек)\n"
            "• 3 месяца — 150 ⭐ (1 аккаунт каждые 30 сек)\n"
            "• 5 месяцев — 220 ⭐ (1 аккаунт каждые 5 сек)\n"
            "• 8 месяцев — 300 ⭐ (1 аккаунт каждые 5 сек)\n"
            "• 1 год — 400 ⭐ (1 аккаунт каждые 5 сек)\n\n"
            "Активируйте код через <b>🎟️ Активировать код</b> или напишите"
            " админу."
        ),
        "sub_active": (
            "📋 <b>СТАТУС ПОДПИСКИ</b>\n\n"
            "Статус: <b>Активна ✅</b>\n"
            "📦 Тариф: <b>{plan}</b>\n"
            "⚡ Скорость: <b>1 аккаунт каждые {cd}</b>\n"
            "⏳ Осталось времени: <b>{rem}</b>"
        ),
        "sub_free": (
            "📋 <b>СТАТУС ПОДПИСКИ</b>\n\n"
            "Статус: <b>Нет активной подписки (Бесплатный тариф)</b>\n"
            "⏳ Остаток тарифа: <b>Не применимо</b>\n\n"
            "💎 Активируйте тариф, чтобы получать аккаунты быстрее."
        ),
        "ask_code": (
            "🎟️ <b>АКТИВАЦИЯ КОДА</b>\n\n"
            "Введите или вставьте код для активации тарифа:"
        ),
        "cancelled": "❌ Действие отменено.",
    },
    "ar": {
        "choose_lang": (
            "🌐 <b>اختر لغتك:</b>\n\n"
            "ستظهر جميع نصوص البوت باللغة التي تختارها."
        ),
        "lang_saved": "✅ تم ضبط اللغة على <b>العربية</b>.",
        "join_req": (
            "🔒 <b>شروط الخطة المجانية — THEMOY SHOP</b>\n\n"
            "لتفعيل الخطة المجانية والمطالبة بالحسابات:\n"
            "1. انضم إلى القناة: <a href='{ch_url}'>{ch_name}</a>\n"
            "2. افتح وابدأ البوت: <a href='{bot_url}'>@{bot_user}</a>\n\n"
            "ثم اضغط <b>✅ لقد أتممت الشروط</b>."
        ),
        "btn_channel": "📢 الانضمام إلى القناة",
        "btn_bot": "🤖 فتح @TheMoyShop_bot",
        "btn_check": "✅ لقد أتممت الشروط",
        "not_in_channel": "⚠️ لم نتحقق بعد من انضمامك إلى <b>{ch_name}</b>.",
        "not_started_bot": "⚠️ يرجى فتح <b>@{bot_user}</b> ثم التأكيد هنا.",
        "unlocked": "🎉 تم استيفاء الشروط! تم تفعيل الخطة المجانية.",
        "menu_title": (
            "🛍️ <b>THEMOY SHOP — القائمة الرئيسية</b>\n\n"
            "اختر خيارًا من القائمة:"
        ),
        "btn_claim": "🎁 طلب حساب",
        "btn_cooldown": "⏳ الوقت المتبقي",
        "btn_history": "📂 حساباتي",
        "btn_vip": "💎 باقات VIP",
        "btn_sub": "📋 اشتراكي",
        "btn_redeem": "🎟️ استرداد رمز",
        "no_stock": "⚠️ لا توجد حسابات متاحة حاليًا. حاول لاحقًا.",
        "cooldown_active": (
            "⏳ يجب الانتظار <b>{rem}</b> قبل طلب حساب آخر."
        ),
        "cooldown_ready": "✅ لا يوجد وقت انتظار! يمكنك طلب حساب الآن.",
        "claim_msg1": (
            "🎉 <b>تم استلام الحساب — THEMOY SHOP!</b>\n\n"
            "👤 المستخدم/البريد: <code>{user}</code>\n"
            "🔑 كلمة المرور: <code>{pwd}</code>"
        ),
        "claim_msg2": "⚡ سيكون الطلب التالي متاحًا بعد: <b>{cd_text}</b>.",
        "history_empty": "📂 لم تقم بطلب أي حسابات بعد.",
        "history_title": "📂 <b>آخر الحسابات التي حصلت عليها</b>\n\n",
        "vip_info": (
            "💎 <b>باقات VIP — THEMOY SHOP</b>\n\n"
            "• يوم واحد — 5 ⭐ (حساب كل 3 دقائق)\n"
            "• 5 أيام — 15 ⭐ (حساب كل 1:30 دقيقة)\n"
            "• 15 يومًا (-20%) — 35 ⭐ (حساب كل دقيقة)\n"
            "• 30 يومًا (-20%) — 60 ⭐ (حساب كل 30 ثانية)\n"
            "• 3 أشهر — 150 ⭐ (حساب كل 30 ثانية)\n"
            "• 5 أشهر — 220 ⭐ (حساب كل 5 ثوانٍ)\n"
            "• 8 أشهر — 300 ⭐ (حساب كل 5 ثوانٍ)\n"
            "• سنة كاملة — 400 ⭐ (حساب كل 5 ثوانٍ)\n\n"
            "فعّل رمزًا عبر <b>🎟️ استرداد رمز</b> أو تواصل مع المشرف."
        ),
        "sub_active": (
            "📋 <b>حالة الاشتراك</b>\n\n"
            "الحالة: <b>نشط ✅</b>\n"
            "📦 الباقة: <b>{plan}</b>\n"
            "⚡ السرعة: <b>حساب كل {cd}</b>\n"
            "⏳ الوقت المتبقي: <b>{rem}</b>"
        ),
        "sub_free": (
            "📋 <b>حالة الاشتراك</b>\n\n"
            "الحالة: <b>لا يوجد اشتراك نشط (الخطة المجانية)</b>\n"
            "⏳ الوقت المتبقي للباقة: <b>غير متاح</b>\n\n"
            "💎 فعّل باقة للحصول على الحسابات بشكل أسرع."
        ),
        "ask_code": "🎟️ <b>استرداد رمز</b>\n\nاكتب أو الصق الرمز لتفعيل باقتك:",
        "cancelled": "❌ تم إلغاء العملية.",
    },
}


# ================= BASE DE DATOS SQLITE =================
def init_db() -> None:
  with sqlite3.connect(DB_PATH) as conn:
    conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                lang TEXT DEFAULT 'es',
                opened_partner_bot INTEGER DEFAULT 0,
                free_plan_active INTEGER DEFAULT 0,
                last_claim_at INTEGER DEFAULT 0
            )
            """)
    conn.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                is_claimed INTEGER DEFAULT 0,
                claimed_by INTEGER,
                claimed_at INTEGER
            )
            """)
    conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                user_id INTEGER PRIMARY KEY,
                plan_name TEXT NOT NULL,
                cooldown_seconds INTEGER NOT NULL,
                expires_at INTEGER NOT NULL
            )
            """)
    conn.execute("""
            CREATE TABLE IF NOT EXISTS redeem_codes (
                code TEXT PRIMARY KEY,
                plan_name TEXT NOT NULL,
                cooldown_seconds INTEGER NOT NULL,
                days INTEGER NOT NULL,
                max_uses INTEGER DEFAULT 1,
                used_count INTEGER DEFAULT 0,
                expires_at INTEGER
            )
            """)
    conn.execute("""
            CREATE TABLE IF NOT EXISTS code_redemptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                redeemed_at INTEGER NOT NULL
            )
            """)
    conn.commit()


def ensure_user(user_id: int) -> None:
  with sqlite3.connect(DB_PATH) as conn:
    conn.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,)
    )
    conn.commit()


def set_user_lang(user_id: int, lang: str) -> None:
  lang_clean = lang if lang in TEXTS else "es"
  with sqlite3.connect(DB_PATH) as conn:
    conn.execute(
        """
            INSERT INTO users (user_id, lang)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET lang = excluded.lang
            """,
        (user_id, lang_clean),
    )
    conn.commit()


def get_user_lang(user_id: int) -> str:
  with sqlite3.connect(DB_PATH) as conn:
    row = conn.execute(
        "SELECT lang FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
  return row[0] if row and row[0] in TEXTS else "es"


def mark_partner_bot_opened(user_id: int) -> None:
  with sqlite3.connect(DB_PATH) as conn:
    conn.execute(
        """
            INSERT INTO users (user_id, opened_partner_bot)
            VALUES (?, 1)
            ON CONFLICT(user_id) DO UPDATE SET opened_partner_bot = 1
            """,
        (user_id,),
    )
    conn.commit()


def has_opened_partner_bot(user_id: int) -> bool:
  with sqlite3.connect(DB_PATH) as conn:
    row = conn.execute(
        "SELECT opened_partner_bot FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
  return bool(row and row[0] == 1)


def set_free_plan_active(user_id: int, active: bool = True) -> None:
  with sqlite3.connect(DB_PATH) as conn:
    conn.execute(
        """
            INSERT INTO users (user_id, free_plan_active)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET free_plan_active = excluded.free_plan_active
            """,
        (user_id, 1 if active else 0),
    )
    conn.commit()


def is_free_plan_active(user_id: int) -> bool:
  with sqlite3.connect(DB_PATH) as conn:
    row = conn.execute(
        "SELECT free_plan_active FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
  return bool(row and row[0] == 1)


def get_active_subscription(user_id: int) -> dict | None:
  now = int(time.time())
  with sqlite3.connect(DB_PATH) as conn:
    row = conn.execute(
        """
            SELECT plan_name, cooldown_seconds, expires_at
            FROM subscriptions
            WHERE user_id = ? AND expires_at > ?
            """,
        (user_id, now),
    ).fetchone()
  if not row:
    return None
  return {
      "plan_name": row[0],
      "cooldown_seconds": int(row[1]),
      "expires_at": int(row[2]),
  }


def get_user_cooldown_seconds(user_id: int) -> int:
  sub = get_active_subscription(user_id)
  if sub:
    return sub["cooldown_seconds"]
  return DEFAULT_FREE_COOLDOWN


def format_duration(seconds: int) -> str:
  seconds = max(0, int(seconds))
  days, rem = divmod(seconds, 86400)
  hours, rem = divmod(rem, 3600)
  minutes, secs = divmod(rem, 60)
  parts = []
  if days:
    parts.append(f"{days}d")
  if hours:
    parts.append(f"{hours}h")
  if minutes:
    parts.append(f"{minutes}m")
  parts.append(f"{secs}s")
  return " ".join(parts)


def get_remaining_cooldown(user_id: int) -> int:
  cd_limit = get_user_cooldown_seconds(user_id)
  now = int(time.time())
  with sqlite3.connect(DB_PATH) as conn:
    row = conn.execute(
        "SELECT last_claim_at FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
  last_claim = int(row[0]) if row and row[0] else 0
  elapsed = now - last_claim
  return max(0, cd_limit - elapsed)


def claim_account_for_user(user_id: int) -> tuple[str, dict | None, int]:
  now = int(time.time())
  cd_limit = get_user_cooldown_seconds(user_id)

  with sqlite3.connect(DB_PATH) as conn:
    row = conn.execute(
        "SELECT last_claim_at FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    last_claim = int(row[0]) if row and row[0] else 0
    rem = max(0, cd_limit - (now - last_claim))
    if rem > 0:
      return "cooldown", None, rem

    acc = conn.execute("""
            SELECT id, username, password
            FROM accounts
            WHERE is_claimed = 0
            ORDER BY id ASC
            LIMIT 1
            """).fetchone()

    if not acc:
      return "no_stock", None, 0

    acc_id, username, password = acc
    conn.execute(
        """
            UPDATE accounts
            SET is_claimed = 1, claimed_by = ?, claimed_at = ?
            WHERE id = ?
            """,
        (user_id, now, acc_id),
    )
    conn.execute(
        """
            INSERT INTO users (user_id, last_claim_at)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET last_claim_at = excluded.last_claim_at
            """,
        (user_id, now),
    )
    conn.commit()

  return "ok", {"username": username, "password": password}, cd_limit


def get_user_history(user_id: int, limit: int = 100) -> list[tuple[str, str]]:
  with sqlite3.connect(DB_PATH) as conn:
    rows = conn.execute(
        """
            SELECT username, password
            FROM accounts
            WHERE claimed_by = ? AND is_claimed = 1
            ORDER BY claimed_at DESC, id DESC
            LIMIT ?
            """,
        (user_id, limit),
    ).fetchall()
  return [(r[0], r[1]) for r in rows]


def redeem_code_for_user(code: str, user_id: int) -> tuple[bool, str, dict | None]:
  clean_code = code.strip().upper()
  now = int(time.time())

  with sqlite3.connect(DB_PATH) as conn:
    row = conn.execute(
        """
            SELECT code, plan_name, cooldown_seconds, days, max_uses, used_count, expires_at
            FROM redeem_codes
            WHERE code = ?
            """,
        (clean_code,),
    ).fetchone()

    if not row:
      return False, "❌ Ese código no existe.", None

    _, plan_name, cooldown_seconds, days, max_uses, used_count, expires_at = row

    if expires_at is not None and now > int(expires_at):
      return False, "⌛ Este código ya venció.", None

    if int(used_count) >= int(max_uses):
      return False, "⚠️ Este código ya alcanzó su límite de usos.", None

    already = conn.execute(
        "SELECT 1 FROM code_redemptions WHERE code = ? AND user_id = ?",
        (clean_code, user_id),
    ).fetchone()
    if already:
      return False, "⚠️ Ya canjeaste este código anteriormente.", None

    sub_row = conn.execute(
        "SELECT expires_at FROM subscriptions WHERE user_id = ?", (user_id,)
    ).fetchone()
    base_ts = (
        max(now, int(sub_row[0]))
        if sub_row and int(sub_row[0]) > now
        else now
    )
    new_expires_at = base_ts + (int(days) * 86400)

    conn.execute(
        """
            INSERT INTO subscriptions (user_id, plan_name, cooldown_seconds, expires_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                plan_name = excluded.plan_name,
                cooldown_seconds = excluded.cooldown_seconds,
                expires_at = excluded.expires_at
            """,
        (user_id, plan_name, int(cooldown_seconds), new_expires_at),
    )
    conn.execute(
        "UPDATE redeem_codes SET used_count = used_count + 1 WHERE code = ?",
        (clean_code,),
    )
    conn.execute(
        "INSERT INTO code_redemptions (code, user_id, redeemed_at) VALUES (?, ?, ?)",
        (clean_code, user_id, now),
    )
    conn.commit()

  return (
      True,
      "✅ ¡Código canjeado con éxito!",
      {
          "plan_name": plan_name,
          "cooldown_seconds": int(cooldown_seconds),
          "days": int(days),
      },
  )


# ================= TECLADOS =================
def language_keyboard() -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(text="🇪🇸 Español", callback_data="set_lang_es"),
              InlineKeyboardButton(text="🇺🇸 English", callback_data="set_lang_en"),
          ],
          [
              InlineKeyboardButton(
                  text="🇧🇷 Português", callback_data="set_lang_pt"
              ),
              InlineKeyboardButton(text="🇫🇷 Français", callback_data="set_lang_fr"),
          ],
          [
              InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru"),
              InlineKeyboardButton(text="🇸🇦 العربية", callback_data="set_lang_ar"),
          ],
      ]
  )


def free_plan_keyboard(lang: str) -> InlineKeyboardMarkup:
  t = TEXTS.get(lang, TEXTS["es"])
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [InlineKeyboardButton(text=t["btn_channel"], url=REQUIRED_CHANNEL_URL)],
          [
              InlineKeyboardButton(
                  text=t["btn_bot"], callback_data="open_partner_bot"
              )
          ],
          [
              InlineKeyboardButton(
                  text=t["btn_check"], callback_data="verify_free_plan"
              )
          ],
      ]
  )


def main_menu_keyboard(lang: str) -> ReplyKeyboardMarkup:
  t = TEXTS.get(lang, TEXTS["es"])
  return ReplyKeyboardMarkup(
      keyboard=[
          [
              KeyboardButton(text=t["btn_claim"]),
              KeyboardButton(text=t["btn_cooldown"]),
          ],
          [
              KeyboardButton(text=t["btn_history"]),
              KeyboardButton(text=t["btn_vip"]),
          ],
          [
              KeyboardButton(text=t["btn_sub"]),
              KeyboardButton(text=t["btn_redeem"]),
          ],
      ],
      resize_keyboard=True,
  )


def cancel_redeem_keyboard() -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="❌ CANCELAR", callback_data="cancel_redeem"
              )
          ]
      ]
  )


def admin_menu_keyboard() -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="➕ Cargar cuentas", callback_data="adm_add_acc"
              ),
              InlineKeyboardButton(
                  text="🎟️ Crear código", callback_data="adm_new_code"
              ),
          ],
          [
              InlineKeyboardButton(
                  text="👑 Dar VIP manual", callback_data="adm_grant_vip"
              ),
              InlineKeyboardButton(
                  text="📜 Ver códigos", callback_data="adm_list_codes"
              ),
          ],
          [
              InlineKeyboardButton(
                  text="📊 Estadísticas", callback_data="adm_stats"
              )
          ],
      ]
  )


def admin_cancel_keyboard() -> InlineKeyboardMarkup:
  return InlineKeyboardMarkup(
      inline_keyboard=[
          [
              InlineKeyboardButton(
                  text="❌ Cancelar", callback_data="adm_cancel"
              )
          ],
          [
              InlineKeyboardButton(
                  text="⬅️ Volver al panel", callback_data="adm_back"
              )
          ],
      ]
  )


def is_admin(user_id: int) -> bool:
  return user_id in ADMIN_IDS


async def is_user_in_channel(bot: Bot, user_id: int) -> bool:
  try:
    member = await bot.get_chat_member(
        chat_id=REQUIRED_CHANNEL, user_id=user_id
    )
    return member.status in {"member", "administrator", "creator"}
  except Exception:
    return False


async def send_banner_or_text(
    message: Message, text: str, reply_markup=None
) -> None:
  try:
    photo = FSInputFile(BANNER_PATH)
    await message.answer_photo(
        photo=photo, caption=text, reply_markup=reply_markup, parse_mode="HTML"
    )
  except Exception:
    await message.answer(text=text, reply_markup=reply_markup, parse_mode="HTML")


async def send_free_plan_requirements(message: Message, lang: str) -> None:
  t = TEXTS.get(lang, TEXTS["es"])
  text = t["join_req"].format(
      ch_url=REQUIRED_CHANNEL_URL,
      ch_name=REQUIRED_CHANNEL,
      bot_url=REQUIRED_BOT_URL,
      bot_user=REQUIRED_BOT_USERNAME,
  )
  await send_banner_or_text(message, text, reply_markup=free_plan_keyboard(lang))


async def send_main_menu(message: Message, lang: str) -> None:
  t = TEXTS.get(lang, TEXTS["es"])
  await send_banner_or_text(
      message, t["menu_title"], reply_markup=main_menu_keyboard(lang)
  )


def get_bot_stats() -> dict[str, int]:
  now = int(time.time())
  with sqlite3.connect(DB_PATH) as conn:
    free_acc = conn.execute(
        "SELECT COUNT(*) FROM accounts WHERE is_claimed = 0"
    ).fetchone()[0]
    claimed_acc = conn.execute(
        "SELECT COUNT(*) FROM accounts WHERE is_claimed = 1"
    ).fetchone()[0]
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    active_vip = conn.execute(
        "SELECT COUNT(*) FROM subscriptions WHERE expires_at > ?", (now,)
    ).fetchone()[0]
  return {
      "free_acc": int(free_acc),
      "claimed_acc": int(claimed_acc),
      "total_users": int(total_users),
      "active_vip": int(active_vip),
  }


def bulk_insert_accounts(raw_text: str) -> tuple[int, int]:
  added = 0
  skipped = 0
  with sqlite3.connect(DB_PATH) as conn:
    for line in raw_text.splitlines():
      clean = line.strip()
      if not clean:
        continue
      user, pwd = "", ""
      for sep in (":", "|", ";"):
        if sep in clean:
          parts = clean.split(sep, 1)
          user, pwd = parts[0].strip(), parts[1].strip()
          break
      if not user and not pwd:
        parts = clean.split()
        if len(parts) >= 2:
          user, pwd = parts[0].strip(), parts[1].strip()
      if not user or not pwd:
        skipped += 1
        continue
      conn.execute(
          "INSERT INTO accounts (username, password, is_claimed) VALUES (?, ?, 0)",
          (user, pwd),
      )
      added += 1
    conn.commit()
  return added, skipped


# ================= BOT PRINCIPAL =================
async def main() -> None:
  init_db()
  bot = Bot(token=TOKEN)
  dp = Dispatcher(storage=MemoryStorage())

  @dp.message(CommandStart())
  async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    ensure_user(message.from_user.id)
    await message.answer(
        text=TEXTS["es"]["choose_lang"],
        reply_markup=language_keyboard(),
        parse_mode="HTML",
    )

  @dp.callback_query(F.data.startswith("set_lang_"))
  async def on_select_lang(callback: CallbackQuery) -> None:
    lang = callback.data.removeprefix("set_lang_")
    set_user_lang(callback.from_user.id, lang)
    t = TEXTS.get(lang, TEXTS["es"])
    await callback.answer(t["lang_saved"])

    sub = get_active_subscription(callback.from_user.id)
    if sub or is_free_plan_active(callback.from_user.id):
      await send_main_menu(callback.message, lang)
    else:
      await send_free_plan_requirements(callback.message, lang)

  @dp.callback_query(F.data == "open_partner_bot")
  async def on_open_partner_bot(callback: CallbackQuery) -> None:
    lang = get_user_lang(callback.from_user.id)
    t = TEXTS.get(lang, TEXTS["es"])
    mark_partner_bot_opened(callback.from_user.id)
    await callback.answer(REQUIRED_BOT_URL)
    await callback.message.answer(
        text=(
            f"🤖 <a href='{REQUIRED_BOT_URL}'>@{REQUIRED_BOT_USERNAME}</a>\n"
            f"{t['not_started_bot'].format(bot_user=REQUIRED_BOT_USERNAME)}"
        ),
        parse_mode="HTML",
    )

  @dp.callback_query(F.data == "verify_free_plan")
  async def on_verify_free_plan(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    lang = get_user_lang(user_id)
    t = TEXTS.get(lang, TEXTS["es"])

    if not await is_user_in_channel(bot, user_id):
      await callback.answer(
          t["not_in_channel"].format(ch_name=REQUIRED_CHANNEL), show_alert=True
      )
      return

    if not has_opened_partner_bot(user_id):
      await callback.answer(
          t["not_started_bot"].format(bot_user=REQUIRED_BOT_USERNAME),
          show_alert=True,
      )
      return

    set_free_plan_active(user_id, True)
    await callback.answer(t["unlocked"], show_alert=True)
    await callback.message.answer(t["unlocked"])
    await send_main_menu(callback.message, lang)

  # ---- ADMIN CON CONTRASEÑA ----
  @dp.message(Command("admin"))
  async def cmd_admin_auth(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
      return
    await state.set_state(AdminAuthStates.waiting_password)
    await message.answer(
        "🔐 <b>ACCESO DE ADMINISTRADOR — THEMOY SHOP</b>\n\n"
        "Escribe la contraseña para abrir el panel:",
        reply_markup=admin_cancel_keyboard(),
        parse_mode="HTML",
    )

  @dp.message(AdminAuthStates.waiting_password)
  async def process_admin_password(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
      return
    entered = (message.text or "").strip()
    try:
      await message.delete()
    except Exception:
      pass

    if entered != ADMIN_PASSWORD:
      await message.answer(
          "❌ Contraseña incorrecta. Inténtalo de nuevo o cancela.",
          reply_markup=admin_cancel_keyboard(),
          parse_mode="HTML",
      )
      return

    await state.clear()
    await send_banner_or_text(
        message,
        "🛠️ <b>PANEL DE ADMINISTRACIÓN — THEMOY SHOP</b>\n\n"
        "Acceso concedido. Selecciona una opción:",
        reply_markup=admin_menu_keyboard(),
    )

  @dp.callback_query(F.data == "adm_back")
  async def adm_back(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
      await callback.answer("Sin permiso", show_alert=True)
      return
    await state.clear()
    await callback.answer()
    await callback.message.answer(
        "🛠️ <b>PANEL DE ADMINISTRACIÓN — THEMOY SHOP</b>",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML",
    )

  @dp.callback_query(F.data == "adm_cancel")
  async def adm_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
      await callback.answer("Sin permiso", show_alert=True)
      return
    await state.clear()
    await callback.answer("Cancelado")
    await callback.message.answer(
        "❌ Acción cancelada.",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML",
    )

  @dp.callback_query(F.data == "adm_stats")
  async def adm_stats(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
      await callback.answer("Sin permiso", show_alert=True)
      return
    await callback.answer()
    s = get_bot_stats()
    await callback.message.answer(
        "📊 <b>ESTADÍSTICAS DEL BOT</b>\n\n"
        f"🟢 Cuentas disponibles: <b>{s['free_acc']}</b>\n"
        f"📦 Cuentas reclamadas: <b>{s['claimed_acc']}</b>\n"
        f"👥 Usuarios registrados: <b>{s['total_users']}</b>\n"
        f"👑 Suscripciones VIP activas: <b>{s['active_vip']}</b>",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML",
    )

  @dp.callback_query(F.data == "adm_add_acc")
  async def adm_add_acc_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
      await callback.answer("Sin permiso", show_alert=True)
      return
    await state.set_state(AdminStates.waiting_bulk_accounts)
    await callback.answer()
    await callback.message.answer(
        "➕ <b>CARGAR CUENTAS EN LOTE</b>\n\n"
        "Envía una o varias cuentas, una por línea:\n"
        "<code>correo1@gmail.com:clave1</code>\n"
        "<code>correo2@gmail.com:clave2</code>",
        reply_markup=admin_cancel_keyboard(),
        parse_mode="HTML",
    )

  @dp.message(AdminStates.waiting_bulk_accounts)
  async def adm_add_acc_process(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
      return
    added, skipped = bulk_insert_accounts(message.text or "")
    await state.clear()
    await message.answer(
        "✅ <b>CARGA COMPLETADA</b>\n\n"
        f"📥 Cuentas agregadas: <b>{added}</b>\n"
        f"⚠️ Líneas omitidas: <b>{skipped}</b>",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML",
    )

  @dp.callback_query(F.data == "adm_new_code")
  async def adm_new_code_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
      await callback.answer("Sin permiso", show_alert=True)
      return
    await state.set_state(AdminStates.waiting_new_code)
    await callback.answer()
    await callback.message.answer(
        "🎟️ <b>CREAR CÓDIGO DE CANJE</b>\n\n"
        "Envía:\n"
        "<code>CODIGO | DIAS | COOLDOWN_SEG | MAX_USOS | NOMBRE_PLAN</code>\n\n"
        "Ejemplo:\n"
        "<code>THEMOY15 | 15 | 60 | 10 | 15 Días (1 cuenta / 1 min)</code>",
        reply_markup=admin_cancel_keyboard(),
        parse_mode="HTML",
    )

  @dp.message(AdminStates.waiting_new_code)
  async def adm_new_code_process(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
      return
    parts = [p.strip() for p in (message.text or "").split("|")]
    if len(parts) < 4:
      await message.answer(
          "⚠️ Formato inválido. Usa:\n"
          "<code>CODIGO | DIAS | COOLDOWN_SEG | MAX_USOS | NOMBRE_PLAN</code>",
          reply_markup=admin_cancel_keyboard(),
          parse_mode="HTML",
      )
      return
    code = parts[0].upper()
    try:
      days = int(parts[1])
      cooldown_sec = int(parts[2])
      max_uses = int(parts[3])
    except ValueError:
      await message.answer(
          "⚠️ <b>DIAS</b>, <b>COOLDOWN_SEG</b> y <b>MAX_USOS</b> deben ser"
          " números enteros.",
          reply_markup=admin_cancel_keyboard(),
          parse_mode="HTML",
      )
      return
    plan_name = (
        parts[4]
        if len(parts) >= 5 and parts[4]
        else f"{days}d ({cooldown_sec}s)"
    )

    with sqlite3.connect(DB_PATH) as conn:
      conn.execute(
          """
                INSERT OR REPLACE INTO redeem_codes
                    (code, plan_name, cooldown_seconds, days, max_uses, used_count, expires_at)
                VALUES (?, ?, ?, ?, ?, 0, NULL)
                """,
          (code, plan_name, cooldown_sec, days, max_uses),
      )
      conn.commit()

    await state.clear()
    await message.answer(
        "✅ <b>CÓDIGO CREADO</b>\n\n"
        f"🎟️ Código: <code>{code}</code>\n"
        f"📦 Plan: <b>{plan_name}</b>\n"
        f"⏳ Duración: <b>{days} días</b>\n"
        f"⚡ Cooldown: <b>{cooldown_sec} s</b>\n"
        f"🔢 Límite de usos: <b>{max_uses}</b>",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML",
    )

  @dp.callback_query(F.data == "adm_grant_vip")
  async def adm_grant_vip_start(callback: CallbackQuery, state: FSMContext) -> None:
    if not is_admin(callback.from_user.id):
      await callback.answer("Sin permiso", show_alert=True)
      return
    await state.set_state(AdminStates.waiting_grant_vip)
    await callback.answer()
    await callback.message.answer(
        "👑 <b>ASIGNAR VIP MANUAL</b>\n\n"
        "Envía:\n"
        "<code>USER_ID | DIAS | COOLDOWN_SEG | NOMBRE_PLAN</code>\n\n"
        "Ejemplo:\n"
        "<code>987654321 | 30 | 30 | Mensual (1 cuenta / 30 s)</code>",
        reply_markup=admin_cancel_keyboard(),
        parse_mode="HTML",
    )

  @dp.message(AdminStates.waiting_grant_vip)
  async def adm_grant_vip_process(message: Message, state: FSMContext) -> None:
    if not is_admin(message.from_user.id):
      return
    parts = [p.strip() for p in (message.text or "").split("|")]
    if len(parts) < 3:
      await message.answer(
          "⚠️ Formato inválido. Usa:\n"
          "<code>USER_ID | DIAS | COOLDOWN_SEG | NOMBRE_PLAN</code>",
          reply_markup=admin_cancel_keyboard(),
          parse_mode="HTML",
      )
      return
    try:
      target_user_id = int(parts[0])
      days = int(parts[1])
      cooldown_sec = int(parts[2])
    except ValueError:
      await message.answer(
          "⚠️ <b>USER_ID</b>, <b>DIAS</b> y <b>COOLDOWN_SEG</b> deben ser"
          " números enteros.",
          reply_markup=admin_cancel_keyboard(),
          parse_mode="HTML",
      )
      return
    plan_name = (
        parts[3]
        if len(parts) >= 4 and parts[3]
        else f"VIP {days}d ({cooldown_sec}s)"
    )
    expires_at = int(time.time()) + (days * 86400)

    with sqlite3.connect(DB_PATH) as conn:
      conn.execute(
          """
                INSERT INTO subscriptions (user_id, plan_name, cooldown_seconds, expires_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    plan_name = excluded.plan_name,
                    cooldown_seconds = excluded.cooldown_seconds,
                    expires_at = excluded.expires_at
                """,
          (target_user_id, plan_name, cooldown_sec, expires_at),
      )
      conn.commit()

    await state.clear()
    await message.answer(
        "👑 <b>VIP ASIGNADO</b>\n\n"
        f"👤 Usuario: <code>{target_user_id}</code>\n"
        f"📦 Plan: <b>{plan_name}</b>\n"
        f"⏳ Duración: <b>{days} días</b>\n"
        f"⚡ Cooldown: <b>{cooldown_sec} s</b>",
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML",
    )

  @dp.callback_query(F.data == "adm_list_codes")
  async def adm_list_codes(callback: CallbackQuery) -> None:
    if not is_admin(callback.from_user.id):
      await callback.answer("Sin permiso", show_alert=True)
      return
    await callback.answer()
    with sqlite3.connect(DB_PATH) as conn:
      rows = conn.execute("""
                SELECT code, days, cooldown_seconds, used_count, max_uses
                FROM redeem_codes
                ORDER BY code ASC
                LIMIT 30
                """).fetchall()
    if not rows:
      await callback.message.answer(
          "📜 No hay códigos creados todavía.",
          reply_markup=admin_menu_keyboard(),
      )
      return
    lines = ["📜 <b>CÓDIGOS DE CANJE</b>\n"]
    for code, days, cd, used, max_u in rows:
      lines.append(
          f"• <code>{code}</code> — {days}d | {cd}s | Usos: <b>{used}/{max_u}</b>"
      )
    await callback.message.answer(
        "\n".join(lines),
        reply_markup=admin_menu_keyboard(),
        parse_mode="HTML",
    )

  # ---- CANJE DE CÓDIGOS (FSM) ----
  @dp.callback_query(F.data == "cancel_redeem")
  async def cancel_redeem_cb(callback: CallbackQuery, state: FSMContext) -> None:
    lang = get_user_lang(callback.from_user.id)
    t = TEXTS.get(lang, TEXTS["es"])
    await state.clear()
    await callback.answer(t["cancelled"])
    await callback.message.answer(t["cancelled"])

  @dp.message(RedeemStates.waiting_for_code)
  async def process_redeem_code(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    lang = get_user_lang(user_id)
    code_input = (message.text or "").strip()
    ok, msg, plan_info = redeem_code_for_user(code_input, user_id)
    await state.clear()

    if not ok or not plan_info:
      await send_banner_or_text(
          message,
          f"🎟️ <b>THEMOY SHOP</b>\n\n{msg}",
          reply_markup=main_menu_keyboard(lang),
      )
      return

    await send_banner_or_text(
        message,
        f"{msg}\n\n"
        f"📦 <b>Plan:</b> {plan_info['plan_name']}\n"
        f"⏳ <b>Días sumados:</b> {plan_info['days']}",
        reply_markup=main_menu_keyboard(lang),
    )

  # ---- BOTONES DEL MENÚ PRINCIPAL ----
  @dp.message(F.text)
  async def handle_menu_buttons(message: Message, state: FSMContext) -> None:
    user_id = message.from_user.id
    ensure_user(user_id)
    lang = get_user_lang(user_id)
    t = TEXTS.get(lang, TEXTS["es"])
    txt = (message.text or "").strip()

    sub = get_active_subscription(user_id)
    if not sub and not is_free_plan_active(user_id):
      await send_free_plan_requirements(message, lang)
      return

    if txt == t["btn_claim"]:
      status, acc, val = claim_account_for_user(user_id)
      if status == "cooldown":
        await message.answer(
            t["cooldown_active"].format(rem=format_duration(val)),
            parse_mode="HTML",
        )
        return
      if status == "no_stock":
        await message.answer(t["no_stock"], parse_mode="HTML")
        return

      # Entrega en dos mensajes
      await message.answer(
          t["claim_msg1"].format(user=acc["username"], pwd=acc["password"]),
          parse_mode="HTML",
      )
      await message.answer(
          t["claim_msg2"].format(cd_text=format_duration(val)),
          parse_mode="HTML",
      )

    elif txt == t["btn_cooldown"]:
      rem = get_remaining_cooldown(user_id)
      if rem > 0:
        await message.answer(
            t["cooldown_active"].format(rem=format_duration(rem)),
            parse_mode="HTML",
        )
      else:
        await message.answer(t["cooldown_ready"], parse_mode="HTML")

    elif txt == t["btn_history"]:
      history = get_user_history(user_id, limit=100)
      if not history:
        await message.answer(t["history_empty"], parse_mode="HTML")
        return
      lines = [t["history_title"]]
      for idx, (u, p) in enumerate(history, start=1):
        lines.append(f"{idx}. <code>{u}</code> : <code>{p}</code>")
      await message.answer("\n".join(lines), parse_mode="HTML")

    elif txt == t["btn_vip"]:
      await send_banner_or_text(
          message, t["vip_info"], reply_markup=main_menu_keyboard(lang)
      )

    elif txt == t["btn_sub"]:
      now = int(time.time())
      if sub:
        rem_str = format_duration(sub["expires_at"] - now)
        cd_str = format_duration(sub["cooldown_seconds"])
        msg = t["sub_active"].format(
            plan=sub["plan_name"], cd=cd_str, rem=rem_str
        )
      else:
        msg = t["sub_free"]
      await send_banner_or_text(
          message, msg, reply_markup=main_menu_keyboard(lang)
      )

    elif txt == t["btn_redeem"]:
      await state.set_state(RedeemStates.waiting_for_code)
      await message.answer(
          t["ask_code"], reply_markup=cancel_redeem_keyboard(), parse_mode="HTML"
      )

  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())