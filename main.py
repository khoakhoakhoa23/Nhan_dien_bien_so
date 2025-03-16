from src import inputmain, outputmain

def run_parking_system():
    print("=== XE VÀO BÃI ===")
    inputmain.process_camera(camera_id=0)

    print("=== XE RA BÃI ===")
    outputmain.process_camera(camera_id=0)

if __name__ == "__main__":
    run_parking_system()