import sys
import os
import requests
import zipfile

class Downloader:
    def __init__(self, os_type="Linux_x64"):
        # 修改点 1: OmahaProxy 已死，这里不需要了，我们在 get_position 里直接写死新的 API
        self.download_url = "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o"
        self.os = os_type
        self.base = "chrome"

        if not os.path.exists(self.base):
            os.makedirs(self.base)

    def get_position(self, version):
        # 修改点 2: 使用 Chromium Dash API 替代 OmahaProxy
        # API 文档: https://chromiumdash.appspot.com/
        url = f"https://chromiumdash.appspot.com/fetch_version?version={version}"
        
        try:
            r = requests.get(url)
            if r.status_code == 200:
                data = r.json()
                # Chromium Dash 返回的字段是 chromium_main_branch_position
                # 这对应原脚本需要的 base_position
                position = data.get("chromium_main_branch_position")
                print(f"[+] Resolved version {version} to position: {position}")
                return position
            else:
                print(f"[-] API request failed: {r.status_code}")
                return None
        except Exception as e:
            print(f"[-] Exception during position lookup: {e}")
            return None


    def download(self, url, name):
        # 修改点 3: 增加 timeout 防止卡死，稍微优化一下请求
        try:
            r = requests.get(url, stream=True, timeout=30)
            r.raise_for_status()
            with open(name, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except Exception as e:
            # 原代码这里的 except 直接吞掉了错误，调试时不方便
            # 这里的 print 可能会在循环尝试下载时刷屏，所以保持原逻辑返回 False
            return False

    def unzip_and_rename(self, file_path, name):
        print(f"[+] Unzipping {file_path}...")
        # 建议：生产环境推荐用 zipfile 库而不是 os.system，但为了保持兼容原逻辑不做大改
        # 这里原来的 unzip 命令可能会因为没有 unzip 工具报错，确保系统装了 unzip
        ret = os.system(f"cd {self.base} && unzip -q -o {os.path.basename(file_path)}")
        if ret != 0:
            print("[-] Unzip failed.")
            return

        source = "chrome-linux"       
        destination = os.path.join(self.base, name)
        source_path = os.path.join(self.base, source)
        
        if os.path.exists(source_path):
            if os.path.exists(destination):
                import shutil
                shutil.rmtree(destination)
            os.rename(source_path, destination)
        else:
            print(f"[-] Could not find unzipped folder: {source_path}")

    def driver_unzip_and_rename(self, file_path, name):
        print(f"[+] Unzipping driver {file_path}...")
        os.system(f"cd {self.base} && unzip -q -o {os.path.basename(file_path)}")
        source = "chromedriver_linux64"
        driver = "chromedriver"
        
        # 原逻辑：mv chromedriver_linux64/chromedriver {name} && rmdir chromedriver_linux64
        # 这里的 {name} 实际上是一个目录名（如 chrome/103.0.xxx_123456），但原作者似乎想把它重命名成文件名？
        # 根据 FuzzOrigin 的代码，它似乎期望 chromedriver 是一个二进制文件。
        # 原代码逻辑稍微有点混乱，我们尽量维持原意：
        
        driver_src = os.path.join(self.base, source, driver)
        driver_dst = os.path.join(self.base, name + "_driver") # 为了避免和 chrome 文件夹冲突，改个名或者放入文件夹
        
        # 根据 main 函数最后的输出: chrome is ready - chrome/103.0.5042.0_999146
        # 这里的 name 是文件夹名。
        
        # 让我们严格按照原代码的 shell 命令逻辑翻译：
        # mv {source}/{driver} {name} 
        # 这里 {name} 是传入的参数 `name` (例如 `103.0.5042.0_999146`)
        # 但是 unzip_and_rename 已经把 chrome-linux 重命名为了 `103.0.5042.0_999146` (文件夹)
        # 所以这里的 mv 会把 chromedriver 移动到那个文件夹里？
        # 不，原代码 mv {source}/{driver} {name} 如果 {name} 是已存在的目录，它会把 driver 移进去。
        
        # 修正逻辑：将 chromedriver 放入 Chrome 目录中
        target_dir = os.path.join(self.base, name)
        if os.path.exists(driver_src) and os.path.exists(target_dir):
            os.system(f"mv {driver_src} {os.path.join(target_dir, 'chromedriver')}")
            os.system(f"rm -rf {os.path.join(self.base, source)}")
        else:
            print("[-] Driver unzip path error")

    def download_binary(self, version):
        prefix = "Linux_x64"
        postfix = "chrome-linux.zip"
        driver = "chromedriver_linux64.zip"

        print(f"[+] start download chrome binary")
        print(f"[+] get position - {version}")
        position = self.get_position(version)

        if position is None:
            print(f"[-] fail to get position {version}")
            # 如果 API 失败，尝试硬编码查找（根据你提供的 CSV）
            if version == "103.0.5028.0":
                position = 996434
                print(f"[!] Using hardcoded position for {version}: {position}")
            else:
                return None   

        print(f"[+] find position - {position}")

        base_url = f"{self.download_url}/{prefix}%2F"
        download_flag = False
        found = 0

        # Snapshot 不一定在每一个 commit 都有构建，所以原作者向后查找 100 个 commit
        for i in range(100):
            current_pos = int(position) + i
            # URL 需要正确编码
            url = f"{base_url}{current_pos}%2F{postfix}?alt=media"
            name = f"{version}_{current_pos}"
            zip_name = f"{name}.zip"
            zip_path = os.path.join(self.base, zip_name)
            
            # print(f"Trying {current_pos}...") # Debug usage
            if self.download(url, zip_path):
                download_flag = True
                found = current_pos
                print(f"[+] download success - {zip_path}")
                break
        
        if not download_flag:
            print(f"[-] download fail: No snapshot found in range [{position}, {position+100}]")
            return None

        self.unzip_and_rename(zip_name, name)

        driver_url = f"{base_url}{found}%2F{driver}?alt=media"
        driver_name = f"{name}_driver.zip"
        self.download(driver_url, os.path.join(self.base, driver_name))

        print(f"[+] download success - {os.path.join(self.base, driver_name)}")
        self.driver_unzip_and_rename(driver_name, name)

        print(f"[+] chrome is ready - {os.path.join(self.base, name)}")

def main(argv):
    if len(argv) < 2:
        print("Usage: python3 chrome_downloader.py [version]")
        print("Example: python3 chrome_downloader.py 103.0.5042.0")
        return
    downloader = Downloader(os_type="Linux_x64")
    downloader.download_binary(argv[1])

if __name__ == "__main__":
    main(sys.argv)