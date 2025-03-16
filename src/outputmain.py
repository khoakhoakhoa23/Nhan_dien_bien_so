import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cv2
import easyocr
import os
from datetime import datetime
from database import Vehicle, Session  # Trỏ đến thư mục gốc

# Khởi tạo EasyOCR
reader = easyocr.Reader(['en', 'vi'])


def process_frame(frame):
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        gray = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        gray = cv2.equalizeHist(gray)
        gray = cv2.medianBlur(gray, 3)

        results = reader.readtext(gray, paragraph=True, detail=1)
        license_plate = None
        for result in results:
            text = result[1]
            prob = result[2] if len(result) > 2 else 0.0
            if prob > 0.5 or (prob == 0.0 and text):
                cleaned_text = text.replace('(', '-').replace(')', '').strip()
                if cleaned_text.endswith(' h'):
                    cleaned_text = cleaned_text[:-2]
                license_plate = cleaned_text
                print(f"Biển số: {license_plate} (Độ tin cậy: {prob:.2f})")
                break

        if not license_plate:
            print("Không tìm thấy biển số trong khung hình.")
            return None, None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_dir = os.path.join(os.path.dirname(__file__), '../output_images')
        save_path = os.path.join(save_dir, f"{timestamp}.jpg")

        os.makedirs(save_dir, exist_ok=True)
        cv2.imwrite(save_path, frame)
        print(f"Ảnh đã được lưu tại: {save_path}")

        return license_plate, save_path

    except Exception as e:
        print(f"Lỗi khi xử lý frame: {e}")
        return None, None


def process_camera(camera_id=0):
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"Không thể mở camera {camera_id}. Vui lòng kiểm tra kết nối camera.")
        return

    print("Đang xử lý XE RA BÃI. Nhấn 'q' để thoát, 's' để chụp và nhận diện.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Không thể đọc khung hình từ camera. Kết thúc chương trình.")
            break

        cv2.imshow('Camera - Xe Ra Bãi', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            license_plate, save_path = process_frame(frame)
            if license_plate:
                session = Session()
                try:
                    vehicle = session.query(Vehicle).filter(
                        Vehicle.license_plate == license_plate,
                        Vehicle.exit_time.is_(None)
                    ).first()
                    if vehicle:
                        vehicle.exit_time = datetime.now()
                        session.commit()
                        parking_duration = vehicle.exit_time - vehicle.entry_time
                        hours = parking_duration.total_seconds() / 3600
                        print(f"Đồng ý! Xe {license_plate} được phép ra bãi.")
                        print(f"Thời gian gửi: {hours:.2f} giờ")
                    else:
                        print(f"Báo động! Xe {license_plate} không có trong bãi hoặc đã ra trước đó.")
                except Exception as e:
                    print(f"Lỗi khi xử lý database: {e}")
                    session.rollback()
                finally:
                    session.close()
                print(f"Ảnh đã được lưu tại: {save_path}")
            else:
                print("Không tìm thấy biển số trong khung hình. Vui lòng thử lại.")

        if key == ord('q'):
            print("Đã thoát chương trình.")
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    process_camera()