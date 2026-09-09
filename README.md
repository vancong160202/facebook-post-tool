# Facebook Auto Posting Tool

## Comment ảnh vào bài đã đăng

Chạy chế độ comment thủ công sau khi bài Facebook đã xử lý xong:

```powershell
python main.py --comment
```

Chế độ `--comment` không tự đăng bài mới. Tool mở lần lượt 6 group comment đã cấu hình, tìm bài mới nhất của tài khoản đang đăng nhập trong mỗi group, rồi comment cùng một ảnh.

Đặt ảnh comment trong folder `Comment` nằm cùng cấp với folder ảnh chính. Ví dụ, nếu folder ảnh chính là `C:\Users\TEN_USER\Dropbox\FCOnline` thì dùng:

```text
C:\Users\TEN_USER\Dropbox\Comment\
```

Tool lấy ảnh đầu tiên theo tên file (`.jpg`, `.jpeg`, `.png`, `.webp`). Mỗi group thử dán ảnh bằng `Ctrl+V` trước; nếu Facebook không hiện preview, tool dùng icon camera trong popup comment để tải ảnh. Tool chờ 8 giây upload và 8 giây sau khi gửi comment. Khi chạy xong cả 6 group không lỗi, ảnh đã dùng sẽ bị xóa khỏi folder `Comment`.

Tool local trên Windows để tạo một bài Facebook gồm ảnh, caption và tối đa 10 group thông qua luồng **Thêm nhóm**.

## Tính năng

- Tự đọc ảnh từ folder Dropbox đã chọn.
- Cho phép từ 1 đến tối đa 80 ảnh cho mỗi bài.
- Tự mở Chrome và dùng profile đăng nhập riêng của tool.
- Mở group chính trước khi tạo bài.
- Chọn thêm 9 group phụ trong popup **Thêm nhóm**.
- Nhập caption mặc định: `Tặng ae ít đồ cổ sưu tầm 💥💥`.
- Chờ Facebook xử lý xong ảnh và kiểm tra caption trước khi báo hoàn tất.
- Tự bắt đầu luồng đăng sau khi chạy app, không cần bấm nút mở Facebook.

## Cấu trúc ảnh Dropbox

Folder Dropbox hiện dùng:

```text
Dropbox\\FConline\\
├── 001.jpg
├── 002.jpg
├── ...
└── 086.jpg
```

Ảnh có thể dùng `.jpg`, `.jpeg`, `.png` hoặc `.webp`. App lấy tối đa 80 ảnh đầu theo thứ tự tên file. Vì vậy nên dùng tên có số 0 ở đầu như `001.jpg`, `002.jpg` để thứ tự luôn ổn định.

Nếu muốn tự chỉ định thứ tự, tạo file `order.txt` trong folder ảnh và ghi tên file, mỗi dòng một ảnh:

```text
anh-uu-tien.jpg
anh-so-02.png
anh-so-03.jpg
```

App sẽ ưu tiên thứ tự trong `order.txt`, sau đó thêm các ảnh còn lại theo tên file.

## Cài đặt lần đầu

Mở PowerShell trong thư mục project:

```powershell
py -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium
```

Nếu PowerShell chặn script:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

## Chạy tool

```powershell
cd C:\facebook-post-tool
.\\.venv\\Scripts\\Activate.ps1
python main.py
```

App sẽ tự nạp folder Dropbox đã lưu và bắt đầu luồng đăng. Lần đầu, đăng nhập Facebook và hoàn tất 2FA/checkpoint trực tiếp trong Chrome nếu được yêu cầu.

## Chọn folder Dropbox

Nếu chưa chọn folder hoặc đổi máy:

1. Chạy `python main.py`.
2. Bấm **Chọn folder Dropbox**.
3. Chọn folder Dropbox cá nhân `FConline`.
4. Đảm bảo Dropbox đã đồng bộ ảnh về laptop trước khi chạy đăng bài.

App lưu đường dẫn folder local trong `.facebook_post_settings.json`.

## Đồng bộ sang máy khác

Đưa code lên GitHub, còn ảnh và dữ liệu đăng nhập không đưa lên GitHub.

Trên máy mới:

```powershell
git clone https://github.com/USERNAME/facebook-post-tool.git C:\facebook-post-tool
cd C:\facebook-post-tool
py -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
python -m playwright install chromium
python main.py
```

Sau đó chọn lại folder Dropbox `FConline` trên máy mới và đăng nhập Facebook trong Chrome profile của máy đó.

Không commit các thư mục/file local sau:

```text
.venv\\
chrome-profile\\
.facebook_post_settings.json
images\\
```

## Lưu ý

- Facebook có thể yêu cầu đăng nhập, 2FA, CAPTCHA hoặc checkpoint.
- Tool không vượt qua các bước xác minh của Facebook.
- Với nhiều ảnh, quá trình upload và xử lý có thể lâu; không đóng Chrome khi đang đăng.
- Tool chỉ báo hoàn tất sau khi trạng thái đăng kết thúc và caption được kiểm tra trên trang.
- Giao diện Facebook có thể thay đổi, khiến bộ chọn phần tử cần cập nhật.
