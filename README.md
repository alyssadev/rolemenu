RoleMenu
========

A discord bot for providing role management for users via reactions on messages

[Invite bot to your server](https://discord.com/oauth2/authorize?client_id=873471871906095104&scope=bot&permissions=335883328)

Usage
-----

Ensure that the bot's role is above any roles you want to add:

![screenshot of role list](https://cdn.alyssadev.xyz/cdn/rolemenu3.png)

Access is automatically granted to users with Administrator or Manage Roles. You can configure a mod role with `!rolemenu addmodrole rolename`

![screenshot of rolemenu addmodrole](https://cdn.alyssadev.xyz/cdn/rolemenu5.png)

Post a message that describes what reactions will provide which roles:

![screenshot of role menu](https://cdn.alyssadev.xyz/cdn/rolemenu1.png)

Right click the role menu, and copy the message link (on mobile, you'll need to produce a URL like `https://discord.com/channels/{guild ID}/{channel ID}/{message ID}`)

![screenshot of copy message link menu option](https://cdn.alyssadev.xyz/cdn/rolemenu2.png)

Type the below message:

    !rolemenu <message link> :emoji1:=role1 :emoji2:=role2

Add more emojis and more roles as needed. Make sure there are no spaces after the emojis if using Discord's autofill, it automatically inserts spaces and this will mess up RoleMenu's parsing

If there are any errors, RoleMenu should list them (e.g if you've used a custom emoji that the bot doesn't have access to). Otherwise, it should add reactions to the specified message and report that the role menu was configured.

![screenshot of successful configuration](https://cdn.alyssadev.xyz/cdn/rolemenu4.png)

Commands
--------

* `!rolemenu <message link> :emoji1:=role1 :emoji2:=role2` : Add role menu based on message
* `!norolemenu <message link>` : Remove role menu based on message
* `!rolemenu addmodrole role1 role2` : Add mod role who can make new role menus
* `!rolemenu nomodrole role1 role2` : Remove mod role

Support
-------

https://discord.gg/gns7qTAu
