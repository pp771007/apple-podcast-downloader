# Apple Podcast 下載器

這是一個 Python 腳本，讓您可以透過提供 Apple Podcast 的網址來下載其 MP3 節目單集。它會自動嘗試使用 Apple iTunes API 尋找該 Podcast 底層的 RSS Feed，然後下載所有可用的節目。

## 功能特色

*   **自動尋找 RSS Feed**：從 Apple Podcast 網址中提取 Podcast ID，並查詢 iTunes API 以尋找對應的 RSS Feed 網址。
*   **下載節目單集**：解析 RSS Feed 並下載音訊單集（通常是 MP3 格式，透過 audio enclosures 識別）。
*   **整理下載內容**：建立一個主要的下載資料夾（預設為 `MyPodcasts`），並將每個 Podcast 的單集整理到以該 Podcast 標題命名的子資料夾中（名稱會經過清理）。
*   **下載進度條**：為每個正在下載的單集顯示下載進度條。
*   **跳過已存在檔案**：檢查目標目錄中是否已存在某個單集的檔案，如果存在則跳過下載。
*   **清理檔案名稱**：移除 Podcast 標題和單集標題中對於檔案名稱無效的字元。
*   **錯誤處理**：包含基本的錯誤處理機制，應對網路問題（超時、連線錯誤）、API 查詢失敗、Feed 解析錯誤以及下載問題。

## 環境需求

*   Python 3.x (已在 Python 3.6+ 版本上開發與測試)
*   必要的 Python 函式庫：
    *   `feedparser`：用於解析 RSS Feed。
    *   `requests`：用於發送 HTTP 請求（查詢 iTunes API 及下載單集）。

## 安裝步驟

1.  **複製或下載腳本：**
    將 `apple_podcast_downloader.py` 這個檔案儲存到您的本機電腦上。

2.  **安裝必要的函式庫：**
    開啟您的終端機或命令提示字元，然後執行：
    ```bash
    pip install feedparser requests
    ```
    或者，您可以建立一個名為 `requirements.txt` 的檔案，內容如下：
    ```
    feedparser
    requests
    ```
    然後透過以下指令安裝：
    ```bash
    pip install -r requirements.txt
    ```

## 使用方法

1.  **從終端機執行腳本：**
    ```bash
    python apple_podcast_downloader.py
    ```

2.  **輸入 Apple Podcast 網址：**
    當腳本提示時，貼上您想下載的 Apple Podcast 完整網址。網址格式應該像這樣：
    `https://podcasts.apple.com/tw/podcast/某個podcast名稱/id123456789`
    （其中 `123456789` 是該 Podcast 的唯一 ID）。

    ```
    ------------------------------------------------------------
    Apple Podcast 下載器
    請提供 Apple Podcast 的網頁連結，程式會嘗試自動尋找 RSS Feed。
    ------------------------------------------------------------
    請輸入 Apple Podcast 的網址 (例如: https://podcasts.apple.com/tw/podcast/abc/id123456789):
    > 請在此處貼上您的 APPLE PODCAST 網址
    ```

3.  **等待下載完成：**
    *   腳本會先嘗試尋找 RSS Feed 網址。
    *   如果成功，它會在執行腳本的同一個目錄下建立一個名為 `MyPodcasts` 的資料夾，並在裡面建立一個以 Podcast 標題命名的子資料夾。
    *   接著，它會遍歷所有單集並將它們下載到對應的 Podcast 子資料夾中，同時顯示每個檔案的下載進度。
    *   已存在的檔案將會被跳過。

4.  **尋找您下載的檔案：**
    下載完成後，請檢查 `MyPodcasts/<Podcast_標題>/` 目錄，裡面就會有下載好的 MP3 檔案。

## 運作原理

1.  **提取 ID**：腳本使用正規表示式 (Regular Expressions) 從使用者提供的 Apple Podcast 網址中提取數字形式的 Podcast ID。
2.  **查詢 iTunes API**：使用提取到的 ID 建構 iTunes Lookup API 的請求網址 (`https://itunes.apple.com/lookup?id=...`)。
3.  **取得 Feed 網址**：向 API 發送請求，並解析回傳的 JSON 回應，从中找到 `feedUrl`（即 RSS Feed 網址）。
4.  **解析 RSS Feed**：使用 `feedparser` 函式庫獲取並解析 RSS Feed 網址的內容。
5.  **下載單集**：
    *   遍歷解析後的 Feed 中的每個項目（entry，即單集）。
    *   尋找帶有音訊類型的 'enclosure' 標籤（例如 `audio/mpeg`）。
    *   如果找到音訊連結，使用 `requests` 函式庫（搭配 `stream=True`）以區塊 (chunk) 的方式下載檔案，並顯示進度條。
    *   檔案會儲存到結構化的目錄中 (`MyPodcasts/<Podcast_標題>/<單集_標題>.mp3`)，下載前會檢查檔案是否已存在。

## 限制與注意事項

*   **API 依賴性**：腳本的運作依賴 Apple iTunes Lookup API 的結構與可用性。如果 Apple 更改其 API，可能會導致尋找 Feed 的功能失效。
*   **網址格式**：腳本預期 Apple Podcast 網址中包含 `/id<數字>` 的部分。如果 Apple 更改其網址結構，ID 提取可能會失敗。
*   **Feed 品質**：下載成功與否取決於 Podcast 提供者是否維護了格式正確且包含有效音訊連結的 RSS Feed。某些 Podcast 可能使用非標準方式提供音訊或需要驗證，本腳本無法處理這些情況。
*   **網路問題**：下載過程可能因為網路連線問題、超時、或託管 Podcast 檔案的伺服器問題而失敗。腳本包含基本的超時處理。
*   **下載位置**：預設情況下，檔案會下載到執行腳本所在目錄下的 `MyPodcasts` 資料夾中。您可以根據需要在 `if __name__ == "__main__":` 區塊中修改 `download_directory` 變數的值。

## **免責聲明 (Disclaimer)**

*   **僅供個人使用**：本工具旨在方便使用者下載公開發布的 Podcast 節目，**僅供個人學習研究與非商業性的離線收聽**。
*   **尊重版權**：Podcast 節目的版權歸屬於其創作者或發行者。使用者應尊重版權，**切勿將下載的內容用於任何形式的重新散佈、分享或商業用途**。
*   **遵守服務條款**：使用者在使用本工具時，應自行負責確保其行為符合 Apple iTunes API 的服務條款以及各 Podcast 內容託管平台（如 Libsyn, SoundOn, Anchor 等）的服務條款，特別是關於自動化存取和頻寬使用的規定。過度使用可能導致您的 IP 被封鎖或其他後果。
*   **無擔保**：本腳本按「原樣」提供，不附帶任何明示或暗示的擔保。作者不對因使用或無法使用本腳本所造成的任何直接或間接損害負責。使用者需自行承擔使用本工具的所有風險。
