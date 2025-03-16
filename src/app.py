from flask import Flask, render_template, request, jsonify
import inputmain
import outputmain
from ..database import Vehicle, Session  # Sửa import
from datetime import datetime

app = Flask(__name__, template_folder="../templates", static_folder="../static")

@app.route('/')
def index():
    session = Session()
    vehicles = session.query(Vehicle).filter(Vehicle.exit_time.is_(None)).all()
    session.close()
    return render_template('index.html', vehicles=vehicles)

@app.route('/capture_entry', methods=['POST'])
def capture_entry():
    import cv2
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if ret:
        license_plate, save_path = inputmain.process_frame(frame)
        if license_plate:
            session = Session()
            vehicle = Vehicle(
                license_plate=license_plate,
                image_path=save_path,
                entry_time=datetime.now()
            )
            session.add(vehicle)
            session.commit()
            session.close()
            return jsonify({'status': 'success', 'license_plate': license_plate, 'image_path': save_path})
    return jsonify({'status': 'error', 'message': 'Không nhận diện được biển số'})

@app.route('/capture_exit', methods=['POST'])
def capture_exit():
    import cv2
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if ret:
        license_plate, save_path = outputmain.process_frame(frame)
        if license_plate:
            session = Session()
            vehicle = session.query(Vehicle).filter(
                Vehicle.license_plate == license_plate,
                Vehicle.exit_time.is_(None)
            ).first()
            if vehicle:
                vehicle.exit_time = datetime.now()
                session.commit()
                parking_duration = vehicle.exit_time - vehicle.entry_time
                hours = parking_duration.total_seconds() / 3600
                session.close()
                return jsonify({'status': 'success', 'license_plate': license_plate, 'duration': f'{hours:.2f} giờ'})
            else:
                session.close()
                return jsonify({'status': 'error', 'message': 'Xe không có trong bãi'})
    return jsonify({'status': 'error', 'message': 'Không nhận diện được biển số'})

if __name__ == '__main__':
    app.run(debug=True)