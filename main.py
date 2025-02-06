from interactions import (
    Client,
    Intents,
    Task,
    listen,
    slash_command,
    slash_option,
    check,
    is_owner,
    SlashContext,
    OptionType,
    ChannelType,
    models,
    SlashCommandChoice,
    Webhook,
    IntervalTrigger,
    Activity,
    ActiveVoiceState,
    BaseChannel,
    Modal,
    ShortText,
    ModalContext,
) #discord-interactions
from interactions.api.events import(
    MessageCreate,
    VoiceUserJoin,
    VoiceUserLeave,
) #discord-interactions イベントのリッスン用
from tts import tts_play, initialize_tts_dict #TTS用の分割機能群
from functions import (
    shell_cmd,
    check_game_status,
    log,
) #ログファイル生成等の分離機能群
import psutil, time, re, subprocess
import help_pagination
import Settings #トークン,IP等

#設定
bot = Client(intents=Intents.DEFAULT|Intents.GUILD_VOICE_STATES|Intents.MESSAGE_CONTENT, delete_unused_application_cmds=True)

target_guilds = Settings.TARGET_GUILDS

progression_unreached = ":white_small_square:"
progression_reached = ":green_square:"
wh : Webhook

activity_name : str = ""
activity_status : str
status_embed : models.Message
global_pid : str
now_gaming : bool
now_gaming = False
current_vc : ActiveVoiceState = None
current_tc : BaseChannel = None
tts_dict : dict = initialize_tts_dict()
debugmode : bool = False

channels_to_read = Settings.TTS_CHANNEL

#ゲームサーバーのステータスチェッカー
@Task.create(IntervalTrigger(30))
async def update_activity():
    log("@Task.create(IntervalTrigger(30))[update_activity] start")
    global global_pid
    embed = None
    if now_gaming:
        activity_name, activity_status = await check_game_status()
        activity = Activity.create(activity_name, state=activity_status[1])
        if activity_name == "not running":
            embed=models.Embed("サーバーステータス")
            embed.add_field("考えられる原因","サーバーが再起動中である\nサーバーがエラーで停止している\n中継サーバーの電源障害")
            embed.description = (":red_circle: サーバーは停止中です")
            embed.set_footer("7 Days to Die Server Observer - by Watchdog#3318", "https://i.imgur.com/zXShTa9.png")
        else:
            embed=models.Embed("サーバーステータス - " + global_pid)
            embed.add_field("Players",activity_status[1])
            embed.add_field("Ingame Time",activity_status[0])
            embed.description = (":green_circle: サーバーは起動中です")
            embed.set_footer("7 Days to Die Server Observer - by Watchdog#3318", "https://i.imgur.com/zXShTa9.png")
    else:
        activity = None
    await bot.change_presence(activity=activity)
    if embed != None:
        await status_embed.edit(embed=embed)
    log("@Task.create(IntervalTrigger(30))[update_activity] end")


#bot起動確認
@listen()
async def on_startup():
    log(f"[on_startup] start")
    # time_3.start()
    # time_4.start()
    # time_5.start()
    # update_activity.start()
    log(f"[on_startup] end")


#bot起動確認
@listen()
async def on_ready():
    global wh
    log(f"[on_ready] start")
    # wh = await Webhook.create(bot, await bot.fetch_channel(1204475272989118487), "さっさと寝ろ")
    log(f"[=====     bot information     =====]")
    log(f"| bot global name: {bot.user.global_name}")
    log(f"| bot display name: {bot.user.display_name}")
    log(f"| started at: {bot.start_time}")
    log(f"| owners: {bot.owner}")
    log(f"| latency: {bot.latency}")
    log(f"[===================================]")
    log("[on_ready] end")


#CTXCommand : ping
#botの応答速度確認
@slash_command(name="ping", description="pingpong! :)",scopes=target_guilds,)
async def ping(ctx: SlashContext):
    log(f"requested command: ping")
    late = str(round(bot.latency, 2))
    await ctx.send(content="pong! (" + late + "ms)")


# @Task.create(TimeTrigger(18))
# async def time_3():
#     await send_alarm("3時です。そろそろ寝ませんか？")
# @Task.create(TimeTrigger(19))
# async def time_4():
#     await send_alarm("4時です。寝ましょう。\n")
# @Task.create(TimeTrigger(20))
# async def time_5():
#     await send_alarm("今すぐに寝ましょう。もう5時です。\n")

# async def send_alarm(text:str, wh:Webhook):
#     print("sending alarm at " + str(datetime.datetime.now))
#     channel = await bot.fetch_channel(1204475272989118487)
#     if len(channel.members)>0:
#         for m in channel.voice_members:
#             if not m.has_role(1240643371006169118):
#                 text+=m.mention
#                 print(f"{m.display_name}, ")
#         await wh.send(text)


#CTXCommand : help
#実装コマンドの索引
@slash_command(
    name="help",
    description="ヘルプを表示します(オプションを指定しないとすべてのコマンドを表示)",
    scopes=target_guilds,
)
@slash_option(
    name="command",
    description="詳細なヘルプを表示します",
    required=False,
    opt_type=OptionType.STRING,
    choices=help_pagination.get_help_choices(),
)
async def help(ctx:SlashContext, command:str=None):
    log(f"requested command: help, Options: {command}")
    if not command:
        result = help_pagination.get_all_help()
        await ctx.send(embed=result)
    else:
        result = help_pagination.get_each_help(command)
        await ctx.send(embed=result, ephemeral=True)


#CTXCommand : environment
#デバッグ向け
#現在環境の確認
@slash_command(
    name="environment",
    description="環境のステータスを取得します",
    scopes=target_guilds,
)
async def environment(ctx: SlashContext):
    log(f"requested command: environment")
    await ctx.defer()
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent
    embed = models.Embed(title="Status of Environment")
    embed.add_field("CPU", f"{cpu_usage}% - {psutil.cpu_count()} Core(s)")
    embed.add_field(
        "Memory [Percent/Total]",
        f"{memory_usage}% / {round(psutil.virtual_memory().total/1024/1024,2)}MB",
    )
    await ctx.send(embed=embed)


#CTXCommand : process
#デバッグ向け
#botホストコンピュータのプロセス検索
@slash_command(
    name="process",
    description="プロセスの状態を取得します",
    scopes=target_guilds,
)
@slash_option(
    name="proc_name",
    description="プロセス名を指定し、最初にヒットしたもの",
    required=True,
    opt_type=OptionType.STRING,
    min_length=2,
)
async def process(ctx: SlashContext, proc_name: str):
    log(f"requested process: help, Options: {proc_name}")
    await ctx.defer()
    target = -1
    for proc in psutil.process_iter(["pid", "name"]):
        if proc_name in proc.info["name"]:
            target = proc.info["pid"]
            break
    if target == -1:
        log(f"result: failed")
        await ctx.send(f"[{proc_name}]を含むプロセスを検出できませんでした")
        return
    embed = models.Embed(title="プロセス検索結果")
    p = psutil.Process(target)
    embed.add_field("プロセス名", p.name())
    embed.add_field("CPU使用率", p.cpu_percent())
    embed.add_field("メモリ使用率", round(p.memory_percent(), 2))
    embed.add_field("ステータス", p.status().upper())
    await ctx.send(embed=embed)
    log(f"result: found, {p.name}")


#CTXCommand : ps
#デバッグ向け
#ゲームホストコンピュータのプロセス検索
@slash_command(
    name="ps",
    description="ps | grep",
    scopes=target_guilds,
)
@slash_option(
    name="query",
    description="grepする文字列",
    required=True,
    opt_type=OptionType.STRING,
    min_length=2,
)
async def ps(ctx: SlashContext, query: str):
    log(f"requested command: ps, Options: {query}")
    await ctx.defer()
    destination = Settings.DESTINATION

    command = f"ps -aux | grep {query} | grep -v grep"
    result = shell_cmd(command, destination)
    if not result:
        result = "not found"
        log(f"result: not found")
        embeds=models.Embed(f"プロセスチェック [{command}]", result)
        embeds.set_footer(f"Resulted Pages: 1/1")
    else:
        result = result.split("\n")
        for i in range(len(result)):
            if result[i] != "":
                result[i] = result[i].split()
        i = 0
        result.remove('')
        if len(result)>10:
            await ctx.send("結果が10以上あります。条件をさらに絞ってお試しください。")
            return
        embeds = []
        for item in result:
            i += 1
            embed=models.Embed(f"プロセスチェック [{command}]")
            embed.set_footer(f"Resulted Pages: {i}/{len(result)}")
            item_name = ["USER","PID","%CPU","%MEM","VSZ","RSS","TTY","STAT","START","TIME","COMMAND"]
            for name in item_name:
                if name != "COMMAND":
                    embed.add_field(name, item.pop(0), True)
                elif name == "COMMAND":
                    embed.add_field(name, " ".join(item))
            embeds.append(embed)
    await ctx.send(embeds=embeds)
    log(f"result: found {len(result)}")


#CTXCommand : tts_setting
#TTSで利用する設定の変更用コマンド
@slash_command(
    name="tts_setting",
    description="読み上げの設定",
    scopes=target_guilds,
)
@slash_option(
    name="command",
    description="対象の操作",
    required=True,
    opt_type=OptionType.STRING,
    choices=[
        SlashCommandChoice(name="音声モデルの変更", value="name"),
        SlashCommandChoice(name="性別の変更", value="gender"),
    ]
)
@slash_option(
    name="parameter",
    description="変更先の値",
    required=True,
    opt_type=OptionType.STRING,
)
async def tts_setting(ctx: SlashContext, command:str, parameter):
    log(f"requested command: voice, Options: {command}, {parameter}")
    s = ""
    with open("./tts/tts_settings", "r") as f:
        s = f.read()

    before = ""
    for item in s.split():
        if command in item:
            before = item
    after = f"{command}:{parameter}"
    s = s.replace(before, after)

    with open("./tts/tts_settings", "w") as f:
        f.write(s)

    log(f"settings changed: {before} => {after}")
    await ctx.send(f"{command} を変更しました\n{before} => {after}")


#CTXCommand : voice
#ボイスチャンネル操作(TTSの操作、サーバーミュート系)
@slash_command(
    name="voice",
    description="ボイスチャンネルの操作",
    scopes=target_guilds,
)
@slash_option(
    name="command",
    description="対象の操作",
    required=True,
    opt_type=OptionType.STRING,
    choices=[
        SlashCommandChoice(name="TTSを接続", value="tts_join"),
        SlashCommandChoice(name="TTSを切断", value="tts_disconnect"),
        SlashCommandChoice(name="全員切断", value="disconnect_all"),
        SlashCommandChoice(name="全員サーバーミュート", value="mute_all"),
        SlashCommandChoice(name="全員サーバースピーカーミュート", value="deaf_all"),
        SlashCommandChoice(name="全員サーバーミュート解除", value="unmute_all"),
        SlashCommandChoice(name="全員サーバースピーカーミュート解除", value="undeaf_all"),
    ]
)
@slash_option(
    name="channel",
    description="対象のチャンネル",
    required=True,
    opt_type=OptionType.CHANNEL,
    channel_types=[ChannelType.GUILD_VOICE],
)
async def voice(ctx: SlashContext, command: str, channel: int):
    log(f"requested command: voice, Options: {command}, {channel.name}")
    await ctx.defer()
    global current_vc
    if command == "disconnect_all":
        await ctx.send("現在接続しているメンバーを切断します。")
        for member in channel.members:
            if member.voice == None: continue
            await member.disconnect()
        await ctx.send("全員切断しました",ephemeral=True)
    elif command == "mute_all":
        for member in channel.members:
            if member.voice == None: continue
            await member.edit(mute=True)
        await ctx.send("全員ミュートしました",ephemeral=True)
    elif command == "deaf_all":
        for member in channel.members:
            if member.voice == None: continue
            await member.edit(mute=True)
        await ctx.send("全員スピーカーミュートしました",ephemeral=True)
    elif command == "unmute_all":
        for member in channel.members:
            if member.voice == None: continue
            await member.edit(mute=False)
        await ctx.send("全員ミュート解除しました",ephemeral=True)
    elif command == "undeaf_all":
        for member in channel.members:
            if member.voice == None: continue
            await member.edit(mute=True)
        await ctx.send("全員スピーカーミュート解除しました",ephemeral=True)
    elif command == "tts_join":
        if not ctx.voice_state:
            log(f"connecting to {channel.name}<#{channel.id}>")
            connected:ActiveVoiceState = await channel.connect(deafened=True)
            await ctx.send(f"<#{connected.channel.id}> に接続しました", silent=True, delete_after=15)
            log(f"success! connected to {connected.channel.name}<#{connected.channel.id}>")
        else:
            await ctx.send(f"既に <#{ctx.voice_state.channel.id}> に接続済みです\n移動させる場合は切断してから再接続してください", silent=True, delete_after=15)
            log(f"failed! already connected to {ctx.voice_state.channel.name}<#{ctx.voice_state.channel.id}>")
    elif command == "tts_disconnect":
        if bot.get_bot_voice_state(ctx.guild).channel.id == channel.id:
            vc:ActiveVoiceState = bot.get_bot_voice_state(ctx.guild)
            await vc.channel.disconnect()
            await ctx.send("切断しました", silent=True, delete_after=15)
            log(f"success! disconnected from {vc.channel.name}<#{vc.channel.id}>")
        else:
            vc:ActiveVoiceState = bot.get_bot_voice_state(ctx.guild)
            await ctx.send(f"切断に失敗しました\n```log\ncontext: {ctx}\ncontext voice_state: {channel}\nauthor voice_state: {ctx.author.voice}\ncurrent active_voice_state: {vc}\n```", silent=True, delete_after=15)
            log(f"failed! couldn't disconnect")
    else:
        ctx.send("実装されていません")


#CTXCommand : vc_raid
#ボイスチャンネル操作(メンバーのレイド)
@slash_command(
    name="raid",
    description="メンバーをソースチャンネルからターゲットチャンネルへレイドします",
    scopes=target_guilds,
)
@slash_option(
    name="source_ch",
    description="レイド元",
    required=True,
    opt_type=OptionType.CHANNEL,
    channel_types=[ChannelType.GUILD_VOICE],
)
@slash_option(
    name="target_ch",
    description="レイド先",
    required=True,
    opt_type=OptionType.CHANNEL,
    channel_types=[ChannelType.GUILD_VOICE],
)
async def vc_raid(ctx:SlashContext, source_ch:int, target_ch:int):
    log(f"requested command: raid, Options: {source_ch.name}, {target_ch.name}")
    await ctx.defer()
    refused_members = []
    for member in source_ch.voice_members:
        if member.voice:
            await member.move(target_ch) if member in target_ch.members else refused_members.append(member)
    member_names = [v.display_name for v in refused_members]
    if refused_members:
        await ctx.send(f"以下のメンバーは権限が一致していないため移動しませんでした。\n権限がないメンバーを移動させたい場合は手動で移動してください\n\n- {member_names.join("\n- ")}")
    else:
        await ctx.send(f"{source_ch.name}内の全てのメンバーを{target_ch.name}へレイドしました")

#CTXCommand : tts_dictionary
#TTSで利用する辞書内容の変更コマンド
@slash_command(
    name="tts_dictionary",
    description="読み上げ辞書機能",
    scopes=target_guilds
)
@slash_option(
    name="command",
    description="対象の操作",
    required=True,
    opt_type=OptionType.STRING,
    choices=[
        SlashCommandChoice(name="追加", value="add"),
        SlashCommandChoice(name="削除", value="delete"),
        SlashCommandChoice(name="リスト", value="list")
    ]
)
async def dictionary_modal(ctx: SlashContext, command: str):
    log(f"requested command: tts_dictionary, Options: {command}")
    global tts_dict
    if command == "add":
        modal = Modal(
            ShortText(label="この文字列を", custom_id="match", placeholder="テキストや絵文字(絵文字はコピペして)"),
            ShortText(label="この文字列として読み上げます", custom_id="replacer", placeholder="テキストだとありがたい"),
            title="辞書登録"
        )
        await ctx.send_modal(modal)
        modal_ctx: ModalContext = await ctx.bot.wait_for_modal(modal)
        key = modal_ctx.responses["match"]
        value = modal_ctx.responses["replacer"]
        tts_dict[key] = value
        text = ""
        for k, v in tts_dict.items():
            text += f"{k}\t{v}\n"
        with open("./tts/tts_dict.csv", 'w', newline='') as f:
            f.write(text)
        initialize_tts_dict()
        ctx.send(f"辞書に {key}:{value} を追加しました", silent=True, delete_after=15)

    if command == "delete":
        modal = Modal(
            ShortText(label="削除する辞書のkey\n( [/tts_dictionary list] からコピペなど )", custom_id="match", placeholder="テキストや絵文字(絵文字はコピペして)"),
            title="辞書削除"
        )
        await ctx.send_modal(modal)
        modal_ctx: ModalContext = await ctx.bot.wait_for_modal(modal)
        key = modal_ctx.responses["match"]
        value = tts_dict.pop(key)
        text = ""
        for k, v in tts_dict.items():
            text += f"{k}\t{v}\n"
        with open("./tts/tts_dict.csv", 'w', newline='') as f:
            f.write(text)
        initialize_tts_dict
        ctx.send(f"辞書から {key}:{value} を削除しました", silent=True, delete_after=15)

    if command == "list":
        embed = models.Embed(
            title="登録済み辞書",
            description="TTS読み上げの際に考慮される辞書の一覧",
        )
        embed.add_field("key: 変換元文字列", "value: 変換先文字列")
        for k,v in tts_dict.items():
            embed.add_field(k, v, True)
        await ctx.send(embed=embed)
        print(tts_dict)


#CTXCommand : kill
#キルコマンド(管理者用)
@slash_command(
    name="kill",
    description="シャットダウンします (bot管理者専用)",
    scopes=target_guilds
)
@check(is_owner())
async def kill_command(ctx: SlashContext):
    await ctx.send("シャットダウンします…", silent=True, delete_after=5)
    time.sleep(5)
    exit(0)


#CTXCommand : debug
#デバッグモード(開発中)
@slash_command(
    name="debug",
    scopes=target_guilds
)
@slash_option(
    name="param",
    description="",
    required=True,
    opt_type=OptionType.STRING,
    choices=[
        SlashCommandChoice(name="true", value="true"),
        SlashCommandChoice(name="false", value="false"),
    ]
)
@check(is_owner())
async def debug_mode(ctx: SlashContext, param: str):
    global debugmode
    if param=="true":
        debugmode = True
        await ctx.send("Debug mode state: true")
        log("Debug mode state: true")
    elif param=="false":
        debugmode = False
        await ctx.send("Debug mode state: false")
        log("Debug mode state: true")


#CTXEvent : on_voice_user_join
#VCに誰かが参加したときにTTSを接続する
@listen()
async def on_voice_user_join(event:VoiceUserJoin):
    if not event.author.bot:
        log(f"[on_voice_user_join] start")
        if not bot.get_bot_voice_state(event.channel.guild):
            log(f"connecting bot to {event.channel.name}<#{event.channel.id}> ({event.author.nick})")
            await event.channel.connect(deafened=True)
            if bot.get_bot_voice_state(event.channel.guild):
                log(f"success! connected to {event.channel.name}<#{event.channel.id}> ({event.author.nick})")
                vc:ActiveVoiceState = bot.get_bot_voice_state(event.channel.guild)
                member_count = 0
                for mem in vc.channel.voice_members:
                    if not mem.bot : member_count += 1
                log(f"connected members excluding bot: {member_count}")
            else:
                log(f"failed! couldn't connect to {event.channel.name}<#{event.channel.id}>")
        else:
            vc:ActiveVoiceState = bot.get_bot_voice_state(event.channel.guild)
            log(f"bot is already connected to {vc.channel.name}<#{vc.channel.id}>")
        log(f"[on_voice_user_join] end")


#CTXEvent : on_voice_user_leave
#VCから誰かが抜けたときにTTSを切断したりしなかったりする
@listen()
async def on_voice_user_leave(event:VoiceUserLeave):
    if not event.author.bot:
        log(f"[on_voice_user_leave] start")
        if bot.get_bot_voice_state(event.channel.guild):
            vc:ActiveVoiceState = bot.get_bot_voice_state(event.channel.guild)
            member_count = 0
            for mem in vc.channel.voice_members:
                if not mem.bot : member_count += 1
            log(f"connected members excluding bot: {member_count}")
            if member_count == 0:
                if vc.channel.id == event.channel.id:
                    log(f"disconnecting bot from {event.channel.name}<#{event.channel.id}> ({event.author.nick})")
                    await event.channel.disconnect()
                    if not bot.get_bot_voice_state(event.channel.guild):
                        log(f"success! connected to {event.channel.name}<#{event.channel.id}> ({event.author.nick})")
                    else:
                        log(f"failed! couldn't connect to {event.channel.name}<#{event.channel.id}> ({event.author.nick})")
                else:
                    log(f"bot is in different channel")
            else:
                log("there are some remaining connected members!")
        else:
            log(f"bot is not connected to vc")
        log(f"[on_voice_user_leave] end")


#CTXEvent : on_message_create (Privileged)
#メッセージが投稿されたとき、TTSを利用中であれば発声する
@listen()
async def on_message_create(event:MessageCreate):
    log("[on_message_create] start")
    if (not event.message.author.bot) and bot.get_bot_voice_state(event.message.channel.guild):
        vc:ActiveVoiceState = bot.get_bot_voice_state(event.message.channel.guild)
        text = event.message.content
        if event.message.attachments:
            text += " 添付ファイルあり"
        if event.message.sticker_items:
            text += event.message.sticker_items[0].name
        log(f"message content: {text}")
        if event.message.channel.id in channels_to_read:
            await tts_play(text, vc)
        else:
            log("the message is not in channels_to_read")
        log("[on_message_create] end")
    if debugmode:
        print("[DEBUG]")
        print(event)
        print(event.message)
        print(event.message.sticker_items)

bot.start(Settings.DISCORD_TOKEN)
