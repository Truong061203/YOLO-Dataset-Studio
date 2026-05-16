# YOLO Dataset Studio

Ứng dụng giao diện dùng để xử lý dataset YOLO từ đầu đến cuối trong một nơi duy nhất:

1. Chuẩn hóa ID class.
2. Đổi tên đồng bộ ảnh và label.
3. Dọn label rỗng, ảnh thiếu label và label thiếu ảnh.
4. Gộp nhiều dataset vào `Master_Dataset`.
5. Chia folder ảnh-label phẳng thành `train / val / test` và tạo `data.yaml`.

Người dùng chỉ cần chạy:

```powershell
python app_remap.py
```

---

## 1. Cấu trúc project

```text
YOLO-Dataset-Studio/
  app_remap.py
  README.md
```

Toàn bộ chức năng chính đã được gom vào `app_remap.py`.

---

## 2. Yêu cầu môi trường

- Python 3.10 trở lên.
- Thư viện:
  - `pyyaml`
  - `tkinter` thường có sẵn trên Python Windows.

Nếu thiếu `pyyaml`:

```powershell
pip install pyyaml
```

---

## 3. Cấu trúc dataset YOLO hợp lệ

Mỗi dataset nguồn cần có cấu trúc:

```text
Dataset_A/
  train/
    images/
    labels/
  valid/
    images/
    labels/
  test/
    images/
    labels/
```

Một cặp ảnh-label hợp lệ:

```text
train/images/apple_001.jpg
train/labels/apple_001.txt
```

Ảnh và label phải trùng basename:

```text
apple_001.jpg
apple_001.txt
```

---

## 4. Hệ class chuẩn

Tất cả dataset cần quy về cùng một thứ tự class, ví dụ:

```text
tao
chuoi
ca_rot
cam
dua
```

Tương ứng:

```text
0 = tao
1 = chuoi
2 = ca_rot
3 = cam
4 = dua
```

Trong app, file master class hiện dùng:

```text
D:\Learn\classes.txt
```

---

## 5. Cách chạy ứng dụng

```powershell
python app_remap.py
```

Ứng dụng có 5 tab:

1. `Chuẩn hoá ID`
2. `Đổi tên dataset`
3. `Dọn dữ liệu`
4. `Gộp dataset`
5. `Chia dataset`

---

# 6. Hướng dẫn từng tab

## Tab 1: Chuẩn hoá ID

### Dùng khi nào

Dùng khi các dataset khác nhau đang có `class_id` riêng và cần đưa về cùng hệ class chung.

### Cách thao tác

1. Bấm `Thêm folder dataset`.
2. Chọn một hoặc nhiều folder dataset.
3. Nếu folder đầu tiên có `data.yaml`, app sẽ đọc danh sách class gốc.
4. Chọn class đích tương ứng trong bảng mapping.
5. Nếu cần thêm ID thủ công, bấm `Thêm ID thủ công`.
6. Bấm nút chạy.

### Kết quả

- Label được đổi `class_id`.
- Label không còn class hợp lệ sẽ bị xóa.
- Ảnh cùng tên với label bị xóa cũng bị xóa theo.
- Folder được đánh dấu bằng file:

```text
.da_remap_xong
```

### Lưu ý

Tab này sửa trực tiếp dữ liệu gốc. Nên backup trước khi chạy.

---

## Tab 2: Đổi tên dataset

### Dùng khi nào

Dùng khi muốn đổi tên file trong chính dataset hiện tại để dễ quản lý.

### Cách thao tác

1. Chọn folder dataset.
2. Nhập `Tên chính`, ví dụ:

```text
tao
```

3. Bấm `Xem trước`.
4. Kiểm tra bảng preview.
5. Nếu dữ liệu đã thay đổi bên ngoài app, bấm `Làm mới`.
6. Bấm `Đổi tên`.

### Kết quả

Ví dụ:

```text
abc.jpg  -> tao_000001.jpg
abc.txt  -> tao_000001.txt
```

App đổi tên đồng bộ trong cả:

```text
train
valid
test
```

### Lưu ý

- Chỉ những cặp ảnh-label hợp lệ mới được đổi tên.
- App đổi tên bằng file tạm trung gian để tránh ghi đè khi rename hàng loạt.
- Đây là thao tác sửa trực tiếp dataset gốc.

---

## Tab 3: Dọn dữ liệu

### Dùng khi nào

Dùng khi muốn dọn các file lỗi trước khi train:

1. Label `.txt` rỗng.
2. Ảnh có nhưng không có label cùng tên.
3. Label có nhưng không có ảnh cùng tên.

### Cách thao tác

1. Bấm `Thêm folder`.
2. Chọn một hoặc nhiều dataset cần dọn.
3. Bấm `Quét trước` để xem:
   - số label rỗng
   - số ảnh thiếu label
   - số label thiếu ảnh
4. Bấm `Dọn ngay`.

### Kết quả

Nếu có:

```text
labels/sample_001.txt
images/sample_001.jpg
```

và `sample_001.txt` rỗng, app sẽ xóa cả hai file.

Nếu có:

```text
images/sample_002.jpg
```

nhưng không có:

```text
labels/sample_002.txt
```

app sẽ xóa `sample_002.jpg`.

Nếu có:

```text
labels/sample_003.txt
```

nhưng không có ảnh cùng basename trong thư mục `images`, app sẽ xóa `sample_003.txt`.

### Lưu ý

Đây là thao tác xóa file thật. Cần backup trước khi chạy.

---

## Tab 4: Gộp dataset

### Dùng khi nào

Dùng khi muốn gom nhiều dataset riêng vào một dataset tổng để train YOLO.

### Cách thao tác

1. Chọn `Folder dataset`.
2. Nhập `Tên chính`, ví dụ:

```text
tao
```

3. Bấm `Thêm vào danh sách`.
4. Lặp lại cho các dataset khác.
5. Chọn `Folder output`.
6. Chọn hoặc bỏ chọn `Tạo lại folder output từ đầu`.
7. Bấm `Gộp dataset`.

### Kết quả

App tạo:

```text
Master_Dataset/
  train/
    images/
    labels/
  valid/
    images/
    labels/
  test/
    images/
    labels/
  data.yaml
```

Ví dụ file đầu ra:

```text
train/images/tao_000001.jpg
train/labels/tao_000001.txt
```

### Logic xử lý

1. Chỉ copy theo cặp ảnh-label hợp lệ.
2. Giữ nguyên split:
   - `train` sang `train`
   - `valid` sang `valid`
   - `test` sang `test`
3. Đổi tên bản copy theo mẫu:

```text
nameMain_000001
```

4. Tạo `data.yaml` từ danh sách master classes hiện tại.

### Lưu ý

Tab này chỉ copy sang output, không sửa dữ liệu nguồn.

---

## Tab 5: Chia dataset

### Dùng khi nào

Dùng khi bạn có một folder nguồn đang chứa ảnh và label lẫn chung, ví dụ:

```text
csdl/
  image_001.jpg
  image_001.txt
  image_002.jpg
  image_002.txt
```

và muốn chuyển nó sang cấu trúc YOLO để train.

### Cách thao tác

1. Chọn `Folder nguồn` đang chứa ảnh và `.txt` lẫn chung.
2. Chọn `Folder output`.
3. Nếu đã có file class `.txt`, bấm `Nhập file class` để app dùng danh sách đó khi tạo `data.yaml`.
4. Nhập tỉ lệ chia, mặc định:

```text
Train = 0.8
Val   = 0.1
Test  = 0.1
```

5. Bấm `Quét trước` để xem số cặp hợp lệ, số ảnh thiếu label và nguồn class đang dùng.
6. Bấm `Chia dataset`.

### Kết quả

App tạo:

```text
dataset_yolo/
  train/
    images/
    labels/
  valid/
    images/
    labels/
  test/
    images/
    labels/
  data.yaml
```

### Logic xử lý

1. Chỉ lấy ảnh có file `.txt` cùng basename.
2. Ảnh thiếu label sẽ được bỏ qua và ghi trong log.
3. Các cặp hợp lệ được trộn ngẫu nhiên trước khi chia.
4. Output chỉ là bản copy, không sửa dữ liệu gốc.
5. `data.yaml` được tạo tự động theo cấu trúc:

```yaml
train: train/images
val: valid/images
test: test/images
```

### Lưu ý

- Tổng tỉ lệ `Train + Val + Test` phải bằng `1.0`.
- Nếu đã `Nhập file class`, `data.yaml` output sẽ dùng đúng danh sách class từ file `.txt` đó.
- Nếu không nhập file class riêng, `data.yaml` output sẽ dùng danh sách `master classes` hiện tại của app.
- Nếu bạn cần remap class trước khi train, hãy chạy tab `Chuẩn hoá ID` trước hoặc kiểm tra kỹ file label nguồn.

---

## 7. Định dạng label YOLO

Nếu train detection bbox, mỗi dòng label cần có đúng 5 giá trị:

```text
class_id x_center y_center width height
```

Nếu một dòng có nhiều hơn 5 giá trị, đó thường là polygon segmentation.

---

## 8. Checklist trước khi upload hoặc train

- [ ] File master class đúng thứ tự.
- [ ] Tất cả dataset đã chuẩn hóa `class_id`.
- [ ] Không còn label polygon nếu train detection bbox.
- [ ] Không còn label rỗng nếu không muốn giữ ảnh background.
- [ ] Không còn ảnh thiếu label hoặc label thiếu ảnh.
- [ ] Ảnh và label cùng basename.
- [ ] `Master_Dataset` có đủ `train`, `valid`, `test`.
- [ ] Dataset sau khi chia có đủ `train/images`, `valid/images`, `test/images` và thư mục `labels` tương ứng.
- [ ] `data.yaml` đúng thứ tự class.
- [ ] Đã backup trước các thao tác sửa hoặc xóa dữ liệu gốc.

---

## 9. Ghi chú cho developer

### Nguyên tắc xử lý dữ liệu

1. Ảnh và label luôn phải đi theo cặp.
2. Nếu đổi tên ảnh, phải đổi label cùng lúc.
3. Nếu xóa label không hợp lệ, cần xóa ảnh cùng basename nếu muốn loại hoàn toàn sample đó.
4. Thứ tự class trong `data.yaml` phải khớp với ID trong label.

### Hướng phát triển tiếp theo

1. Thêm chế độ `dry-run` cho rename và delete.
2. Thêm file cấu hình ngoài thay vì hard-code path.
3. Ghi log ra file.
4. Tách logic nghiệp vụ thành module riêng nếu app tiếp tục lớn hơn.

