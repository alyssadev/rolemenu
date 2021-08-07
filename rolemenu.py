#!/usr/bin/env python3
import discord
from sqlalchemy import create_engine, String, Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

rolemenu_db = create_engine("sqlite:///rolemenu.db", echo=True)

Base = declarative_base()

class Messages(Base):
    __tablename__ = "messages"
    # message_id: discord snowflake of message with attached reactions
    message_id = Column(String, primary_key=True)
    # creator: discord snowflake of user that created the role menu
    creator = Column(String)

class Reactions(Base):
    __tablename__ = "reactions"
    # id: {message_snowflake}_{emoji_id}
    id = Column(String, primary_key=True)
    # message: discord snowflake of message linked to this reaction
    message = Column(String)
    # emoji: to be determined. custom emoji can be defined with snowflake, unicode though?
    emoji = Column(String)
    # role: role snowflake
    role = Column(String)

Base.metadata.create_all(rolemenu_db)

Session = sessionmaker(bind = rolemenu_db)
session = Session()

client = discord.Client(intents=Intents(
    guilds=True,
    members=True,
    emojis=True,
    messages=True,
    reactions=True
))

def emoji_convert_to_id(emoji: discord.PartialEmoji):
    if emoji.id:
        return emoji.id
    return ",".join(f"0x{ord(c):08x}" for c in emoji.name)

@client.event
async def on_raw_reaction_add(payload):
    result = session.query(Reactions).get(f"{payload.message_id}_{emoji_convert_to_id(payload.emoji)")
    if not result:
        return
    for reaction in result:
        await payload.member.add_roles(discord.abc.Snowflake(id=reaction.role), reason=f"Reaction on {payload.message_id}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith("!rolemenu") and (len(message.content) == 9 or message.content[9] == " "):
        cmd, *args = message.content.split()
        if not args:
            await message.reply("`!rolemenu <message ID or link> :emoji1:=role1 :emoji2:=role2`")
            return
        msg, *menu_items = args
        if msg.isdigit():
            msg_id = msg
        else:
            msg_id = msg.split("/")[-1]
        for item in menu_items:
            emoji, role = item.split("=")
            print(repr(emoji))
            print(repr(role))
        await message.reply("WIP")

    if message.content.startswith("!norolemenu") and (len(message.content) == 11 or message.content[11] == " "):
        cmd, *args = message.content.split()
        if not args:
            await message.reply("`!norolemenu <message ID or link>`")
            return
        msg = args[0]
        if msg.isdigit():
            msg_id = msg
        else:
            msg_id = msg.split("/")[-1]
        
        msg_results = session.query(Messages).filter(Messages.message_id == msg_id)
        react_results = session.query(Reactions).filter(Reactions.message == msg_id)
        for result in msg_results:

