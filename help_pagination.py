from interactions.models import Embed, SlashCommandChoice
from typing import Tuple
from functions import log
import re

help_dict = {
    '/help [command]':['埋め込みヘルプを表示します',
        'command(Optional):','指定して詳細な情報を表示します (Choice, ephemeral)'],

    '/ping':['botの返答速度をチェックします'],

    '/environment':['環境の状態を表示します'],

    '/process [proc_name]':['BOTサーバーのプロセス状況を確認します',
        'proc_name:','検索対象のプロセス名 (str, min-length:2)'],

    '/ps [query]':['ゲームサーバーにプロセスの確認リクエストを送出します',
        'query:','確認対象のプロセス名 (str, min-length:2)',],

    '/tts_setting [command] [parameter]':['TTS(テキスト読み上げの設定を変更します)',
        'command:','対象の操作 (Choice)',
        'parameter:','設定するパラメータ (str)',
        '設定できる内容:','https://cloud.google.com/text-to-speech/docs/voices'],

    '/tts_dictionary [command]':['テキスト読み上げ時の辞書機能を呼びだします',
        'command','テキスト変換候補を追加、削除、または一覧出力します',
        '詳細:','コマンドを実行すると、追加、削除の場合はモーダルが開くので、そこに入力してください'],

    '/voice [command] [channel]':['特定のVCに対して一括操作リクエストを送出します',
        'command:','対象の操作 (Choice)',
        'channel:','対象のチャンネル(Choice)',
        'その他詳細:','[/help voice_commands]で詳細なコマンドを表示します'],

    '!voice_commands':["登録されているVC管理コマンドの一覧です",
        'TTSを[接続|切断]','WatchdogをVCに接続、または切断します',
        '全員切断','指定したVCに接続しているメンバーを切断します',
        '全員サーバーミュート(解除)','指定したVCに接続しているメンバーをサーバーミュート(解除)します',
        '全員サーバースピーカーミュート(解除)','指定したVCに接続しているメンバーをサーバースピーカーミュート(解除)します',],
}

def get_all_help() -> Embed:
    log(f"getting all of helps")
    embed = Embed("List of Commands")
    for (key,value) in help_dict.items():
        embed.add_field(key,value[0])
    embed.set_footer(f"commands ({len(help_dict)})")
    return embed

def get_help_choices() -> dict:
    help_choice_list = []
    for key in help_dict.keys():
        help_choice_list.append(SlashCommandChoice(key.split()[0][1:], key))
    return help_choice_list

def get_each_help(command:str) -> Embed:
    log(f"getting each help: {command}")
    descriptions = help_dict[command]
    embed = Embed(command,descriptions[0])
    for i in range(1, len(descriptions), 2):
        embed.add_field(descriptions[i],descriptions[i+1])
    return embed