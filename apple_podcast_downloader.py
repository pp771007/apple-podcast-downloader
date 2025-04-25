import feedparser
import requests
import os
import sys
import re # 用於清理檔案名稱和提取 ID
import json # 用於解析 API 回應

def sanitize_filename(filename):
    """移除檔案名稱中的無效字元，並替換空格"""
    sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
    # 可以選擇性地替換空格，如果需要的話
    # sanitized = sanitized.replace(" ", "_")
    return sanitized

def get_feed_url_from_apple_podcast_url(apple_url):
    """
    嘗試從 Apple Podcast 網址提取 ID 並透過 iTunes API 查詢 RSS Feed URL。

    Args:
        apple_url (str): 使用者輸入的 Apple Podcast 網址。

    Returns:
        str: 找到的 RSS Feed URL，如果找不到則回傳 None。
    """
    print(f"[*] 正在分析 Apple Podcast 網址: {apple_url}")
    match = re.search(r'/id(\d+)', apple_url)
    if not match:
        print("[!] 無法從提供的網址中提取 Podcast ID。請確保網址格式正確 (例如: https://podcasts.apple.com/.../id123456789)。")
        return None

    podcast_id = match.group(1)
    print(f"  [+] 提取到的 Podcast ID: {podcast_id}")

    lookup_url = f"https://itunes.apple.com/lookup?id={podcast_id}&entity=podcast"
    print(f"[*] 正在透過 Apple API 查詢 RSS Feed URL: {lookup_url}")

    try:
        response = requests.get(lookup_url, timeout=15)
        response.raise_for_status()
        data = response.json()

        if data.get('resultCount', 0) > 0 and 'results' in data:
            podcast_info = data['results'][0]
            if 'feedUrl' in podcast_info:
                feed_url = podcast_info['feedUrl']
                print(f"  [+] 成功找到 RSS Feed URL: {feed_url}")
                return feed_url
            else:
                print("[!] 在 API 回應中找到了 Podcast，但未包含 'feedUrl' 欄位。")
                return None
        else:
            print(f"[!] Apple API 未找到 ID 為 {podcast_id} 的 Podcast 資訊。請檢查 ID 是否正確。")
            return None

    except requests.exceptions.Timeout:
        print("[!] 連接 Apple API 超時。請檢查您的網路連線或稍後再試。")
        return None
    except requests.exceptions.RequestException as e:
        print(f"[!] 查詢 Apple API 時發生網路或 HTTP 錯誤: {e}")
        return None
    except json.JSONDecodeError:
        print("[!] 無法解析 Apple API 的回應 (可能不是有效的 JSON)。")
        return None
    except Exception as e:
        print(f"[!] 處理 API 回應時發生未知錯誤: {e}")
        return None


def download_podcast_episodes(feed_url, download_folder="podcast_downloads"):
    """
    從指定的 RSS Feed URL 下載 Podcast 節目 MP3。
    (已啟用下載進度條顯示)
    """
    print(f"[*] 正在從以下網址獲取 RSS Feed: {feed_url}")
    try:
        feed = feedparser.parse(feed_url)
    except Exception as e:
        print(f"[!] 獲取或解析 Feed 時發生錯誤: {e}")
        return

    if feed.bozo:
        print(f"[!] 警告: Feed 可能格式錯誤或不完整。原因: {feed.bozo_exception}")

    podcast_title = feed.feed.get('title', 'Unknown_Podcast')
    print(f"[*] Podcast 標題: {podcast_title}")

    podcast_folder_name = sanitize_filename(podcast_title)
    full_download_path = os.path.join(download_folder, podcast_folder_name)
    os.makedirs(full_download_path, exist_ok=True)
    print(f"[*] 檔案將儲存至: {full_download_path}")

    if not feed.entries:
        print("[!] 在 Feed 中找不到任何節目集數。")
        return

    print(f"[*] 共找到 {len(feed.entries)} 集節目。")

    for entry in feed.entries:
        episode_title = entry.get('title', 'Untitled_Episode')
        print(f"\n[*] 正在處理: {episode_title}")

        mp3_url = None
        if 'enclosures' in entry:
            for enclosure in entry.enclosures:
                if enclosure.get('type', '').startswith('audio'):
                    mp3_url = enclosure.get('href')
                    if mp3_url:
                        print(f"  [+] 找到音檔連結 (enclosure): {mp3_url}")
                        break

        if not mp3_url:
            print("  [!] 找不到此集數的 MP3 連結。跳過。")
            continue

        filename = sanitize_filename(episode_title) + ".mp3"
        filepath = os.path.join(full_download_path, filename)

        if os.path.exists(filepath):
            print(f"  [*] 檔案已存在: {filename}。跳過下載。")
            continue

        print(f"  [*] 正在下載: {filename}")
        try:
            response = requests.get(mp3_url, stream=True, timeout=60) # 使用 stream=True
            response.raise_for_status() # 檢查請求是否成功

            # 獲取檔案總大小
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            block_size = 8192 # 每次讀取的區塊大小 (8KB)

            with open(filepath, 'wb') as f:
                # 使用 iter_content 迭代下載內容
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk: # 過濾掉 keep-alive 新區塊
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        # *** 以下是啟用進度條的部分 ***
                        if total_size > 0:
                            # 計算進度百分比，並縮放到 50 個字元的寬度
                            progress = int(50 * downloaded_size / total_size)
                            # 使用 \r 回車符回到行首，end="" 阻止換行，實現原地更新
                            print(f"\r    進度: [{'#' * progress}{'.' * (50 - progress)}] {downloaded_size}/{total_size} Bytes", end="")
                        else:
                            # 如果無法獲取 total_size，只顯示已下載大小
                            print(f"\r    進度: {downloaded_size} Bytes", end="")

            # *** 下載完成後，換行，避免下一個輸出接在進度條後面 ***
            print()
            print(f"  [+] 下載完成: {filename}")

        except requests.exceptions.Timeout:
            # 在錯誤訊息前加換行，確保它不會接在進度條後面
            print(f"\n  [!] 下載超時 ({mp3_url})。")
            if os.path.exists(filepath):
                os.remove(filepath)
        except requests.exceptions.RequestException as e:
            print(f"\n  [!] 下載時發生錯誤 ({mp3_url}): {e}")
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"\n  [!] 處理下載時發生未知錯誤: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)

    total_episodes = len(feed.entries)
    downloaded_count = len([entry for entry in feed.entries if not os.path.exists(os.path.join(full_download_path, sanitize_filename(entry.get('title', 'Untitled_Episode') + ".mp3")))])
    existing_count = total_episodes - downloaded_count

    print("\n[*] 所有節目處理完成。")
    print(f"[*] 本次下載: {downloaded_count} 集")
    print(f"[*] 已存在: {existing_count} 集")
    print(f"[*] 節目總數: {total_episodes} 集")


# --- 主程式執行區塊 ---
if __name__ == "__main__":
    print("-" * 60)
    print("Apple Podcast 下載器")
    print("請提供 Apple Podcast 的網頁連結，程式會嘗試自動尋找 RSS Feed。")
    print("-" * 60)

    if len(sys.argv) > 1:
        apple_podcast_url = sys.argv[1]
    else:
        apple_podcast_url = input("請輸入 Apple Podcast 的網址 (例如: https://podcasts.apple.com/tw/podcast/abc/id123456789): \n> ")

    if not apple_podcast_url or not apple_podcast_url.strip():
        print("[!] 未輸入網址，程式結束。")
    else:
        podcast_feed_url = get_feed_url_from_apple_podcast_url(apple_podcast_url.strip())

        if podcast_feed_url:
            print("-" * 60)
            download_directory = "MyPodcasts"
            download_podcast_episodes(podcast_feed_url, download_directory)
        else:
            print("-" * 60)
            print("[!] 無法自動取得 RSS Feed URL。")
            print("    請確認您輸入的 Apple Podcast 網址是否正確，或該 Podcast 是否仍然存在。")
            print("    您也可以嘗試手動尋找該 Podcast 的 RSS Feed URL 並修改程式碼。")