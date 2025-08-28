# UCC 咖啡 ERP 系統

這是一個基於 Django 開發的 ERP 系統，用於管理 UCC 咖啡的生豆入庫、原料倉儲等流程。

## 環境需求

*   Python 3.10 或更高版本
*   MySQL 資料庫

## 快速入門

1.  **克隆專案**
    ```bash
    git clone <您的專案git倉庫URL>
    cd UCC
    ```

2.  **建立並啟動虛擬環境**
    ```bash
    # Windows
    python -m venv UCC_env
    UCC_env\\Scripts\\activate.bat
    ```

3.  **安裝依賴套件**
    ```bash
    pip install -r django-template/requirements.txt
    ```

4.  **設定環境變數**
    *   進入 `django-template` 資料夾。
    *   將 `.env.example` 檔案複製一份並命名為 `.env`。
    *   編輯 `.env` 檔案，填入您的資料庫連線資訊和 Django 的 `SECRET_KEY`。
    
    ```
    # .env 範例
    SECRET_KEY="請在這裡填入一個隨機產生的密鑰"
    DATABASE_URL="mysql://您的用戶名:您的密碼@127.0.0.1:3306/您的資料庫名稱"
    DEBUG=True
    ```

5.  **執行資料庫遷移**
    *   這會根據專案中的遷移檔案建立所有需要的資料表。
    ```bash
    cd django-template
    python manage.py migrate
    ```

6.  **建立超級使用者**
    *   您需要一個管理員帳號來登入後台。
    ```bash
    python manage.py createsuperuser
    ```

7.  **設定初始權限 (可選)**
    *   如果需要設定用戶活動記錄的查看權限，請執行以下命令：
    ```bash
    python manage.py setup_activity_permissions
    ```

8.  **啟動開發伺服器**
    ```bash
    python manage.py runserver
    ```

9.  **訪問系統**
    *   在瀏覽器中開啟 `http://127.0.0.1:8000` 即可看到網站。
    *   後台管理請訪問 `http://127.0.0.1:8000/admin`。

## 其他常用命令

*   **建立遷移檔案**:
    ```bash
    python manage.py makemigrations
    ```
