#!/usr/bin/env python3
from uuid import uuid4
import requests
import json

import config

from telegram import Update, Bot, Chat, Message, User, InlineQueryResultArticle, InputTextMessageContent, \
    InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, TypeHandler, InlineQueryHandler, Job
from telegram.ext.dispatcher import run_async

from pony import orm
from models import User as dbUser, Offer as dbOffer, Shop as dbShop, db

from schemas import ShopSchema, OfferSchema

shopsschema = ShopSchema(many=True)

import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=getattr(logging, config.LOGLEVEL))

logger = logging.getLogger("cw-shops-bot")


@run_async
def start(bot: Bot, update: Update) -> None:
    logger.debug("Entering: start")

    chat = update.effective_chat  # type: Chat
    msg = update.effective_message  # type: Message
    usr = update.effective_user  # type: User

    msg.reply_text('Welcome to Chat Wars Shops Bot.\nCheck out /help for more information!')

    logger.debug("Exiting: start")
    return


@run_async
def help(bot: Bot, update: Update) -> None:
    logger.debug("Entering: help")

    chat = update.effective_chat  # type: Chat
    msg = update.effective_message  # type: Message
    usr = update.effective_user  # type: User

    msg.reply_text("This bot was created to help you with your <a href='http://t.me/chtwrsbot'>Chat Wars</a>, "
                   "<b>⚒ Blacksmith</b> and <b>⚗️ Alchemist</b> window shopping needs. Please use it in Inline Mode."
                   "\n\nClick button below and select <i>Chat Wars Bot</i>",
                   parse_mode='HTML',
                   reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Search", switch_inline_query='')]]),
                   disable_web_page_preview=True)

    logger.debug("Exiting: help")
    return


@run_async
def dbhandler(bot: Bot, update: Update) -> None:
    logger.debug("Entering: dbhandler")

    chat = update.effective_chat  # type: Chat
    msg = update.effective_message  # type: Message
    usr = update.effective_user  # type: User

    update_users = list()
    update_users.append(usr)

    if msg and msg.forward_from:
        update_users.append(msg.forward_from)
    if msg and msg.left_chat_member:
        update_users.append(msg.left_chat_member)
    if msg and msg.new_chat_members:
        update_users.extend(msg.new_chat_members)

    with orm.db_session:
        for u in update_users:
            logger.debug("create or update data for User: {} ({})".format(u.full_name, u.id))
            dbUser.update_or_create(u)

    logger.debug("Exiting: dbhandler")
    return


@run_async
def inline_shop_search(bot: Bot, update: Update) -> None:
    logger.debug("Entering: inline_shop_search")

    chat = update.effective_chat  # type: Chat
    msg = update.effective_message  # type: Message
    usr = update.effective_user  # type: User

    query = update.inline_query.query

    keywords = query.split()

    results = []

    with orm.db_session:
        offers = dbOffer.select(lambda o: o).order_by(lambda o: o.price)
        for keyword in keywords:
            offers = offers.filter(lambda o: keyword.lower() in o.item.lower())
        offers = offers.limit(50)
        # TODO: If search is empty, search by shop name as well?
        for offer in offers:
            shop = offer.shop
            results.append(InlineQueryResultArticle(
                id=uuid4(),
                title=f'{shop.kind}{shop.name} {shop.mana}💧',
                description=f'{offer.item} - {offer.mana}💧 {offer.price}💰\n'
                            f'{shop.ownerCastle}{shop.ownerName}',
                input_message_content=InputTextMessageContent(f'/ws_{shop.link}')
                )
            )

    update.inline_query.answer(results)

    logger.debug("Exiting: inline_shop_search")
    return


@run_async
def shops_updater(bot: Bot, job: Job) -> None:
    logger.debug("Entering: shops_updater")

    resp = requests.get(config.SHOP_API)

    if resp.status_code == 200:
        logger.debug('Retrieved shop data. Dropping and recreating tables.')
        dbOffer.drop_table(with_all_data=True)
        dbShop.drop_table(with_all_data=True)

        db.create_tables(True)
        shops = resp.json()
        with orm.db_session:
            # TODO: Get fucking marshmallow deserialisation working
            for shop in shops:
                logger.debug("creating shop %s", shop['name'])
                s = dbShop(link=shop['link'],
                           name=shop['name'],
                           ownerName=shop['ownerName'],
                           ownerCastle=shop['ownerCastle'],
                           kind=shop['kind'],
                           mana=shop['mana'])
                for offer in shop['offers']:
                    logger.debug("adding offer %s to shop %s", offer['item'], shop['name'])
                    s.offers.create(**offer)
    else:
        logger.debug("Exiting: shops_updater")
        return


@run_async
def list_shops(bot: Bot, update: Update) -> None:
    logger.debug("Entering: list_shops")

    chat = update.effective_chat  # type: Chat
    msg = update.effective_message  # type: Message
    usr = update.effective_user  # type: User

    response = ''

    with orm.db_session:
        shops = dbShop.select(lambda s: s).order_by(dbShop.kind)
        for shop in shops:
            response += f'<a href="https://t.me/share/url?url=/ws_{shop.link}">{shop.kind}{shop.name}</a> '
            response += f'<i>{shop.mana}💧</i> by <b>{shop.ownerCastle}{shop.ownerName}</b>'
            response += '\n\n'

    msg.reply_text(response, parse_mode='HTML')


if __name__ == '__main__':
    ud = Updater(config.TOKEN, workers=12)
    dp = ud.dispatcher
    jq = ud.job_queue

    jq.run_repeating(shops_updater, interval=5*60, first=0)  # every 5 minutes, starting now.

    dp.add_handler(TypeHandler(Update, dbhandler), group=-1)

    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))

    dp.add_handler(CommandHandler(['list', 'shops'], list_shops))

    dp.add_handler(InlineQueryHandler(inline_shop_search))

    if config.APP_ENV.startswith('PROD'):
        ud.start_webhook(listen='0.0.0.0', port=config.WEBHOOK_PORT, url_path=config.TOKEN)
        ud.bot.set_webhook(url='https://{}/{}'.format(config.WEBHOOK_URL, config.TOKEN))
    else:
        ud.start_polling(clean=True)
    ud.idle()

