import pyshorteners

def shorten_url(long_url, service='tinyurl'):
    """
    指定されたURLを短縮する関数。

    Args:
        long_url: 短縮したいURL (str)。
        service: 使用する短縮URLサービス (str, default: 'tinyurl')。
                'tinyurl', 'bitly' (要APIトークン), 'dagd', 'isgd' などが利用可能。

    Returns:
        短縮URL (str)。エラーが発生した場合はNoneを返す。
    """
    try:
        s = pyshorteners.Shortener()

        if service == 'tinyurl':
            shortened = s.tinyurl.short(long_url)
        elif service == 'bitly':
            # Bitlyを使用する場合は、APIトークンが必要。
            # 環境変数から取得するか、直接指定する。
            # BITLY_TOKEN = os.environ.get('BITLY_TOKEN')  # 環境変数から
            BITLY_TOKEN = "YOUR_BITLY_TOKEN" # ここに直接記述(非推奨)
            shortened = s.bitly.short(long_url, bitly_token=BITLY_TOKEN)
        elif service == 'dagd':
            shortened = s.dagd.short(long_url)
        elif service == 'isgd':
            shortened = s.isgd.short(long_url)
        # 他のサービスも同様に追加可能
        else:
            print(f"エラー: {service} はサポートされていないサービスです。")
            return None

        return shortened

    except pyshorteners.exceptions.ShorteningErrorException as e:
        print(f"短縮URL生成エラー: {e}")
        return None
    except pyshorteners.exceptions.BadAPIResponseException as e:
        print(f"APIエラー: {e}")  # APIキーが無効、レート制限など
        return None
    except Exception as e:
        print(f"予期せぬエラー: {e}")
        return None



if __name__ == '__main__':
    long_url = input("短縮したいURLを入力してください: ")

    # TinyURLで短縮
    short_url_tiny = shorten_url(long_url)
    print(f"TinyURL: {short_url_tiny}")

    # Da.gdで短縮
    short_url_dagd = shorten_url(long_url, service='dagd')
    print(f"Da.gd: {short_url_dagd}")

    # Bitlyで短縮 (APIトークンが必要)
    # short_url_bitly = shorten_url(long_url, service='bitly')
    # print(f"Bitly: {short_url_bitly}")