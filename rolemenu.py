#!/usr/bin/env python3
import discord
from sqlalchemy import create_engine, String, Column, ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

rolemenu_db = create_engine("sqlite:///rolemenu.db", echo=True)

Base = declarative_base()

class Guild(Base):
    __tablename__ = "guilds"
    guild_id = Column(Integer, primary_key=True)
    mod_roles = relationship("ModRole", back_populates="guild", cascade="all, delete, delete-orphan")

class ModRole(Base):
    __tablename__ = "modroles"
    role = Column(Integer, primary_key=True)
    guild_id = Column(String, ForeignKey("guilds.guild_id"))
    guild = relationship("Guild", back_populates="mod_roles")

class Message(Base):
    __tablename__ = "messages"
    # message_id: discord snowflake of message with attached reactions
    message_id = Column(String, primary_key=True)
    # creator: discord snowflake of user that created the role menu
    creator = Column(String)
    reactions = relationship("Reaction", back_populates="message", cascade="all, delete, delete-orphan")

class Reaction(Base):
    __tablename__ = "reactions"
    # id: {message_snowflake}_{emoji_id}
    id = Column(String, primary_key=True)
    # message: discord snowflake of message linked to this reaction
    message_id = Column(String, ForeignKey("messages.message_id"))
    message = relationship("Message", back_populates="reactions")
    # emoji: either snowflake id, or unicode codepoints encoded as comma separated hex numbers
    emoji = Column(String)
    # role: role snowflake
    role = Column(Integer)

Base.metadata.create_all(rolemenu_db)

Session = sessionmaker(bind = rolemenu_db)
session = Session()

client = discord.Client(intents=discord.Intents(
    guilds=True,
    members=True,
    emojis=True,
    messages=True,
    reactions=True
))

def emoji_convert_to_id(emoji):
    if type(emoji) is discord.PartialEmoji:
        if emoji.id:
            return emoji.id
        return ",".join(f"{ord(c):x}" for c in emoji.name)
    else:
        if emoji[0] == "<" and emoji[-1] == ">":
            anim,tag,emoji_id = emoji[1:-1].split(":")
            return emoji_id
        return ",".join(f"{ord(c):x}" for c in emoji)

async def id_convert_to_emoji(id: str):
    if len(id) > 17 and "," not in id: # probably a snowflake
        for guild in client.guilds:
            for e in guild.emojis:
                if id in str(e.url).split("/")[-1]:
                    return e
    else:
        return "".join(chr(int(f'0x{c}',16)) for c in id.split(","))

@client.event
async def on_raw_reaction_add(payload):
    if payload.member == client.user:
        return
    result = session.query(Reaction).get(f"{payload.message_id}_{emoji_convert_to_id(payload.emoji)}")
    if not result:
        return
    guild_roles = await client.get_guild(payload.guild_id).fetch_roles()
    await payload.member.add_roles(discord.utils.get(guild_roles, id=result.role), reason=f"Reaction on {payload.message_id}")

@client.event
async def on_raw_reaction_remove(payload):
    if payload.user_id == client.user.id:
        return
    result = session.query(Reaction).get(f"{payload.message_id}_{emoji_convert_to_id(payload.emoji)}")
    if not result:
        return
    guild = client.get_guild(payload.guild_id)
    guild_roles = await guild.fetch_roles()
    member = guild.get_member(payload.user_id)
    await member.remove_roles(discord.utils.get(guild_roles, id=result.role), reason=f"Reaction on {payload.message_id}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    def permission_check(author, admin_only = False):
        perms = author.permissions_in(message.channel)
        if perms.administrator or perms.manage_roles:
            return True
        if admin_only:
            return False
        result = session.query(ModRole).filter(ModRole.guild_id == message.guild.id)
        if not result:
            return False
        for r in result:
            if r.role in [_.id for _ in author.roles]:
                return True
        return False

    if message.content.startswith("!rolemenu") and (len(message.content) == 9 or message.content[9] == " "):
        if not permission_check(message.author):
            await message.reply("You can't use this command.")
            return
        cmd, *args = message.content.split()
        if not args:
            await message.reply("`!rolemenu <message link (not ID)> :emoji1:=role1 :emoji2:=role2`")
            return
        if args[0] == "addmodrole":
            if not permission_check(message.author, admin_only=True):
                await message.reply("You can't use this command.")
                return
            if len(args) == 1:
                await message.reply("`!rolemenu addmodrole role1 role2`")
                return
            roles = args[2:]
            errors = []
            print("starting on " + str(roles))
            for role in roles:
                try:
                    role_id = discord.utils.get(message.guild.roles, name=role).id
                except AttributeError:
                    errors.append(f"Skipped {item}, role not found (case sensitive!)")
                    continue
                print(f"got id {role_id}")
                guild = session.query(Guild).get(message.guild.id)
                if not guild:
                    guild = Guild(guild_id=message.guild.id)
                    session.add(guild)
                    print("added new guild")
                modrole_orm = ModRole(
                        role=role_id,
                        guild=guild
                )
                session.add(modrole_orm)
            if not errors:
                session.commit()
            else:
                session.rollback()
            await message.reply("Mod role configur" + ( ("ation errored:\n" + "\n".join(errors) ) if errors else "ed") )
            return
        msg, *menu_items = args
        if msg.isdigit():
            await message.reply("`!rolemenu <message link (not ID)> :emoji1:=role1 :emoji2:=role2`")
            return
        else:
            msg_guild_id, msg_channel_id, msg_id = msg.split("/")[-3:]
        channel = await client.fetch_channel(msg_channel_id)
        msg_obj = await channel.fetch_message(msg_id)
        msg_orm = Message(message_id=msg_id, creator=message.author.id)
        session.add(msg_orm)
        errors = []
        for item in menu_items:
            emoji, role = item.split("=")
            emoji_id = emoji_convert_to_id(emoji)
            if not emoji_id:
                errors.append(f"Skipped {item}, couldn't turn {emoji} into a unique ID")
                continue
            try:
                role_id = discord.utils.get(message.guild.roles, name=role).id
            except AttributeError:
                errors.append(f"Skipped {item}, role not found (case sensitive!)")
                continue
            e = await id_convert_to_emoji(emoji_id)
            if not e:
                errors.append(f"Skipped {item}, I don't have access to {emoji}")
                continue
            await msg_obj.add_reaction(e)
            reaction_orm = Reaction(
                    id=f"{msg_id}_{emoji_id}",
                    message=msg_orm,
                    emoji=emoji_id,
                    role=role_id)
            session.add(reaction_orm)
        if not errors:
            session.commit()
        else:
            session.rollback()
        await message.reply("Role menu configur" + ( ("ation errored:\n" + "\n".join(errors) ) if errors else "ed") )
        return

    if message.content.startswith("!norolemenu") and (len(message.content) == 11 or message.content[11] == " "):
        if not permission_check(message.author):
            await message.reply("You can't use this command.")
            return
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
        for result in msg_results:
            session.delete(result)
        session.commit()

@client.event
async def on_ready():
    print(f"Logged in as {client.user.name} ({client.user.id})")
    print(discord.utils.oauth_url(client.user.id, permissions=discord.Permissions(
        add_reactions=True,
        change_nickname=True,
        external_emojis=True,
        manage_messages=True,
        manage_roles=True,
        read_messages=True,
        read_message_history=True,
        send_messages=True
    )))

if __name__ == "__main__":
    with open(".bottoken") as f:
        client.run(f.read().strip())
