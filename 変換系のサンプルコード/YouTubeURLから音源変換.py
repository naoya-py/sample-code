import yt_dlp
from rich.console import Console
from rich.progress import Progress, BarColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

console = Console()

format_options_default = { # デフォルトの形式オプションは削除。利用可能な形式リストから選択するように変更
    'mp3': {
        'format': 'bestaudio[ext=mp3]',
        'ext': 'mp3',
        'acodec': 'libmp3lame',
    },
    'aac': {
        'format': 'bestaudio[ext=aac]',
        'ext': 'aac',
        'acodec': 'aac',
    },
    'wav': {
        'format': 'bestaudio[ext=wav]',
        'ext': 'wav',
        'acodec': 'pcm_s16le',
    },
}

progress_bar = Progress( # Progress インスタンスをグローバルスコープで定義 (後で download_audio 内に移動しても良い)
    BarColumn(bar_width=50),
    DownloadColumn(),
    TransferSpeedColumn(),
    TimeRemainingColumn(),
    console=console,
)

def rich_progress_hook(d): # rich_progress_hook をグローバル関数として定義
    """
    richライブラリでダウンロードの進捗状況を表示するためのフック関数。
    外側の progress_bar インスタンスを再利用する。
    """
    status_bar = "[bold blue]ダウンロード中:[/bold blue]"


    if d['status'] == 'downloading':
        task_id = progress_bar.add_task("download", filename=d['filename'], start=False, total=d['total_bytes'])
        if not progress_bar._tasks[task_id].started:
            progress_bar.start_task(task_id)
            progress_bar.start()
        progress_bar.update(task_id, advance=d['downloaded_bytes'])
    elif d['status'] == 'finished':
        task_id = progress_bar.add_task("download", filename=d['filename'], start=False, total=d['total_bytes']) # finishedでもタスクIDが必要なため追加
        progress_bar.update(task_id, completed=d['total_bytes'])
        progress_bar.stop()
    elif d['status'] == 'error':
        console.print(f"[bold red]ダウンロードエラー: {d['error']}[/bold red]")
        progress_bar.stop()


def download_audio(url, selected_format_code, bitrate=None): # format_type を selected_format_code に変更
    """
    yt-dlpを使ってYouTube動画から音声をダウンロードし、richで進捗を表示する。

    Args:
        url (str): YouTube動画のURL
        selected_format_code (str): ダウンロードする音声形式の format code (例: '251')
        bitrate (str, optional): ビットレート (例: '128k', '192k', '320k'). デフォルトはNone
    """

    ydl_opts = {
        'format': selected_format_code, # ユーザーが選択した format code を直接指定
        'extractaudio': True,
        'outtmpl': '%(title)s.%(ext)s',
        'progress_hooks': [rich_progress_hook], # グローバル関数を参照
    }

    if bitrate:
        ydl_opts['audioquality'] = bitrate


    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title', None)

            # 拡張子を info_dict['format']['ext'] から取得。format_code から拡張子を特定するのは難しい場合があるため
            downloaded_format_ext = info_dict['format']['ext'] if 'format' in info_dict and 'ext' in info_dict['format'] else 'unknown'

            console.print(f"\n[bold green]ダウンロード完了:[/bold green] [bold cyan]{video_title}[/bold cyan] を [bold magenta]{downloaded_format_ext}[/bold magenta] 形式で保存しました。") # 拡張子を downloaded_format_ext で表示
    except Exception as e:
        console.print(f"[bold red]ダウンロード中にエラーが発生しました:[/bold red] {e}")
        if "Requested format is not available" in str(e): # このエラーは基本的には発生しないはずだが、念のため残しておく
            console.print("[bold yellow]指定された音声形式が動画で利用できない可能性があります。[/bold yellow]")



def list_available_formats(url):
    """
    yt-dlpで利用可能な音声形式をリスト表示する。

    Args:
        url (str): YouTube動画のURL
    """
    ydl_opts_list_formats = {
        'extractaudio': True, # 音声形式のみ取得
        'listformats': False, # listformats オプションは不要になったので False に設定。extract_info で formats 情報が取得できる
        'quiet': True, #  余計な出力を抑制
        'simulate': True, # ダウンロードせずに情報を取得
    }
    available_formats = [] # 空のリストで初期化
    try:
        with yt_dlp.YoutubeDL(ydl_opts_list_formats) as ydl:
            info_dict = ydl.extract_info(url, download=False) # download=False で情報のみ取得
            formats = info_dict.get('formats', []) # formats 情報を取得
            for f in formats:
                if f.get('vcodec') == 'none' and f.get('acodec') != 'none': # 音声形式のみをフィルタリング (vcodec='none' かつ acodec!='none')
                    format_info = {
                        'format_id': f.get('format_id'),
                        'format_note': f.get('format_note'),
                        'ext': f.get('ext'),
                        'acodec': f.get('acodec'),
                        'abr': f.get('abr'), # Audio Bitrate
                    }
                    available_formats.append(format_info) # 辞書形式で情報を追加
            return available_formats # リストを返す

    except Exception as e:
        console.print(f"[bold red]利用可能な形式のリスト取得中にエラーが発生しました:[/bold red] {e}")
        return []


if __name__ == '__main__':
    console.rule("[bold red]YouTube 音声ダウンローダー[/bold red]")

    url = console.input("[bold green]YouTube動画のURLを入力してください:[/bold green] ")

    available_formats = list_available_formats(url) # 利用可能な形式リストを取得

    if not available_formats: # リストが空の場合 (エラー or 利用可能な形式がない)
        console.print("[bold red]利用可能な音声形式を取得できませんでした。スクリプトを終了します。[/bold red]")
        exit()

    console.print("\n[bold green]利用可能な音声形式:[/bold green]")
    for i, format_info in enumerate(available_formats): # enumerate で番号付きで表示
        format_str = f"  [bold cyan]{i+1}[/bold cyan]: " # 番号表示
        format_str += f"Format ID: [magenta]{format_info['format_id']}[/magenta], "
        format_str += f"Note: [magenta]{format_info['format_note']}[/magenta], "
        format_str += f"Extension: [magenta]{format_info['ext']}[/magenta], "
        format_str += f"Audio Codec: [magenta]{format_info['acodec']}[/magenta], "
        format_str += f"Bitrate: [magenta]{format_info['abr']}[/magenta]" if format_info['abr'] else f"Bitrate: [magenta]N/A[/magenta]" # ビットレートがない場合は N/A 표시
        console.print(format_str)

    while True: # 無効な選択がされた場合に再入力を促すループ
        try:
            format_index = int(console.input("[bold green]ダウンロードする形式の番号を選択してください:[/bold green] ")) - 1 # 番号で選択させる
            if 0 <= format_index < len(available_formats):
                selected_format_code = available_formats[format_index]['format_id'] # format_id を取得
                break # 有効な選択の場合、ループを抜ける
            else:
                console.print("[bold red]無効な番号です。リストから番号を選択してください。[/bold red]")
        except ValueError:
            console.print("[bold red]無効な入力です。番号を入力してください。[/bold red]")


    bitrate = None
    selected_format_ext = available_formats[format_index]['ext'] # 選択された形式の拡張子を取得
    if selected_format_ext == 'mp3': # MP3 形式の場合のみビットレートを尋ねる
        bitrate = console.input("[bold green]MP3ビットレートを選択してください (例: 128k, 192k, 320k, デフォルトは最高音質):[/bold green] ")
        if not bitrate:
            bitrate = '0' # 最高音質

    download_audio(url, selected_format_code, bitrate) # format_type の代わりに selected_format_code を渡す