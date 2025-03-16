from sqlalchemy import create_engine, Column, Integer, String, DateTime, text
from sqlalchemy.orm import sessionmaker, declarative_base

# Chuỗi kết nối SQL Server
DATABASE_URL = "mssql+pyodbc://sa:123456@127.0.0.1,1433/parking_db?driver=ODBC+Driver+17+for+SQL+Server&TrustServerCertificate=yes"

engine = create_engine(DATABASE_URL)
Base = declarative_base()  # ⚠️ Thay thế bằng dòng dưới nếu muốn tránh cảnh báo
# Base = sqlalchemy.orm.declarative_base()  # Dòng thay thế nếu muốn dùng SQLAlchemy 2.0 chuẩn

# Định nghĩa bảng vehicles
class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    license_plate = Column(String(20))
    image_path = Column(String(255))
    entry_time = Column(DateTime)
    exit_time = Column(DateTime, nullable=True)

# Tạo bảng nếu chưa tồn tại
Base.metadata.create_all(engine)

# Tạo session để thao tác với database
Session = sessionmaker(bind=engine)
session = Session()

# Kiểm tra kết nối
try:
    session.execute(text("SELECT 1"))  # ✅ Sử dụng text() để tránh lỗi
    print("Kết nối thành công!")
except Exception as e:
    print(f"Lỗi kết nối: {e}")
finally:
    session.close()
