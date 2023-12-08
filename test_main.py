from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
import sqlite3
import pandas as pd
import io
from fastapi.middleware.cors import CORSMiddleware
import datetime
from typing import Annotated
from fastapi import FastAPI, Form

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_FILE = "students.db"  # Thay đổi thành tên tệp cơ sở dữ liệu của bạn
TABLE_NAME = "students"  # Thay đổi thành tên bảng của bạn
ITEMS_PER_PAGE = 10
SEARCHABLE_COLUMNS = ["MASV", "HoTenSV", "NgaySinh", "Phai", "MaLop",
                       "Nganh", 'DienThoaiGiaDinh', 'DienThoaiCaNhan',
                       'DiaChiLienHe', 'Email', 'CoViecLam', 'LoaiDonViLamViec',
                       'TenDonViLamViec', 'DiaChiDonViLamViec', 
                       'TinhThanhPho']  # Thay đổi thành các cột có thể tìm kiếm được


COLUMN_NAMES = [
    'MASV',
    'HoTenSV',
    'NgaySinh',
    'Phai',
    'MaLop',
    'Nganh',
    'DienThoaiGiaDinh',
    'DienThoaiCaNhan',
    'DiaChiLienHe',
    'Email',
    'CoViecLam',
    'LoaiDonViLamViec',
    'TenDonViLamViec',
    'DiaChiDonViLamViec',
    'TinhThanhPho'
]


def create_table():
    connection = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, check_same_thread=False)
    connection.execute('pragma encoding=utf8')
    cursor = connection.cursor()

    cursor.execute(
        f'''
        CREATE TABLE IF NOT EXISTS "{TABLE_NAME}" (
            "MASV" TEXT PRIMARY KEY,
            "HoTenSV" TEXT,
            "NgaySinh" TEXT,
            "Phai" TEXT,
            "MaLop" TEXT,
            "Nganh" TEXT,
            "DienThoaiGiaDinh" TEXT,
            "DienThoaiCaNhan" TEXT,
            "DiaChiLienHe" TEXT,
            "Email" TEXT,
            "CoViecLam" TEXT,
            "LoaiDonViLamViec" TEXT,
            "TenDonViLamViec" TEXT,
            "DiaChiDonViLamViec" TEXT,
            "TinhThanhPho" TEXT
        )
        '''
    )

    connection.commit()
    connection.close()


create_table()


def table_exists(table_name, connection):
    cursor = connection.cursor()
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?;", (table_name,))
    return cursor.fetchone() is not None

@app.delete("/delete-student/{masv}")
async def delete_student(masv: str):
    try:
        connection = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, check_same_thread=False)
        connection.execute('pragma encoding=utf8')
        cursor = connection.cursor()

        if not table_exists(TABLE_NAME, connection):
            create_table()

        # Thực hiện thao tác xóa
        query = f"DELETE FROM {TABLE_NAME} WHERE MASV = ?;"
        cursor.execute(query, (masv,))

        # Kiểm tra xem sinh viên đã được xóa hay không
        if cursor.rowcount > 0:
            connection.commit()
            connection.close()
            return {"message": "Student deleted successfully"}
        else:
            connection.close()
            raise HTTPException(status_code=404, detail="Student not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/insert-students")
async def insert_students(file: UploadFile = File(...)):
    try:
        connection = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, check_same_thread=False)
        connection.execute('pragma encoding=utf8')
        cursor = connection.cursor()

        if not table_exists(TABLE_NAME, connection):
            create_table()

        content = await file.read()
        df = pd.read_excel(io.BytesIO(content), header=0)

        records = df.to_dict(orient='records')

        for record in records:
            columns = ', '.join(record.keys())
            placeholders = ', '.join(['?' for _ in range(len(record))])
            values = tuple(record.values())

            query = f'''
                INSERT OR REPLACE INTO "{TABLE_NAME}" (
                    "MASV", "HoTenSV", "NgaySinh", "Phai", "MaLop", "Nganh", 
                    "DienThoaiGiaDinh", "DienThoaiCaNhan", "DiaChiLienHe", "Email", 
                    "CoViecLam", "LoaiDonViLamViec", "TenDonViLamViec", 
                    "DiaChiDonViLamViec", "TinhThanhPho"
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            cursor.execute(query, values)

        connection.commit()
        connection.close()

        return {"message": "Insertion successful"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/insert-student")
async def insert_student(
    MASV: Annotated[str, Form()],
    HoTenSV: Annotated[str, Form()],
    NgaySinh: Annotated[str, Form()],
    Phai: Annotated[str, Form()],
    MaLop: Annotated[str, Form()],
    Nganh: Annotated[str, Form()],
    DienThoaiGiaDinh: Annotated[str, Form()],
    DienThoaiCaNhan: Annotated[str, Form()],
    DiaChiLienHe: Annotated[str, Form()],
    Email: Annotated[str, Form()],
    CoViecLam: Annotated[str, Form()],
    LoaiDonViLamViec: Annotated[str, Form()],
    TenDonViLamViec: Annotated[str, Form()],
    DiaChiDonViLamViec: Annotated[str, Form()],
    TinhThanhPho: Annotated[str, Form()]
):
    try:
        # Kiểm tra ngày tháng hợp lệ
        print("ok")
        datetime.datetime.strptime(NgaySinh, '%Y-%m-%d')
        
        # Kiểm tra giới tính hợp lệ
        if Phai not in ['Nam', 'Nữ']:
            raise HTTPException(status_code=422, detail="Invalid value for Phai. Expected 'Nam' or 'Nữ'.")

        connection = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, check_same_thread=False)
        connection.execute('pragma encoding=utf8')
        cursor = connection.cursor()

        if not table_exists(TABLE_NAME, connection):
            create_table()

        query = f'''
            INSERT OR REPLACE INTO "{TABLE_NAME}" (
                "MASV", "HoTenSV", "NgaySinh", "Phai", "MaLop", "Nganh", 
                "DienThoaiGiaDinh", "DienThoaiCaNhan", "DiaChiLienHe", "Email", 
                "CoViecLam", "LoaiDonViLamViec", "TenDonViLamViec", 
                "DiaChiDonViLamViec", "TinhThanhPho"
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''

        values = (
            MASV, HoTenSV, NgaySinh, Phai, MaLop, Nganh, 
            DienThoaiGiaDinh, DienThoaiCaNhan, DiaChiLienHe, Email, 
            CoViecLam, LoaiDonViLamViec, TenDonViLamViec, 
            DiaChiDonViLamViec, TinhThanhPho
        )

        cursor.execute(query, values)
        connection.commit()
        connection.close()

        return {"message": "Insertion successful"}

    except ValueError as ve:
        raise HTTPException(status_code=422, detail=f"Invalid date format: {ve}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def fetch_students(page: int, search_query: str = '', search_property: str = ''):
    try:
        connection = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, check_same_thread=False)
        connection.execute('pragma encoding=utf8')
        cursor = connection.cursor()

        # Xử lý tìm kiếm
        search_query = search_query.strip()
        print(search_query)
        if search_query and search_property in SEARCHABLE_COLUMNS:
            search_condition = f"{search_property} LIKE ?"
            query = f"SELECT * FROM {TABLE_NAME} WHERE {search_condition} LIMIT ? OFFSET ?;"
            result = cursor.execute(query, (f"%{search_query}%", ITEMS_PER_PAGE, (page - 1) * ITEMS_PER_PAGE)).fetchall()
        else:
            query = f"SELECT * FROM {TABLE_NAME} LIMIT ? OFFSET ?;"
            result = cursor.execute(query, (ITEMS_PER_PAGE, (page - 1) * ITEMS_PER_PAGE)).fetchall()

        total_records_query = f"SELECT COUNT(*) FROM {TABLE_NAME};"
        total_records = cursor.execute(total_records_query).fetchone()[0]
        total_pages = (total_records + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

        students_list = []
        for row in result:
            student_dict = dict(zip(SEARCHABLE_COLUMNS, row))
            students_list.append(student_dict)

        connection.close()
        # print(students_list)
        return {"students": students_list, "total_pages": total_pages}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/students/", response_model=dict)
async def get_students(page: int = Query(1, ge=1)):
    return fetch_students(page)


@app.get("/students/search", response_model=dict)
async def search_students(
    search_query: str,
    search_property: str,
    page: int = Query(1, ge=1)
):
    return fetch_students(page, search_query, search_property)


@app.get("/students/export-csv", response_model=dict)
async def export_students_to_csv(search_query: str = '', search_property: str = ''):
    try:
        connection = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, check_same_thread=False)
        connection.execute('pragma encoding=utf8')
        cursor = connection.cursor()
        result = ''

        # Thực hiện tìm kiếm nếu có thông tin tìm kiếm
        search_query = search_query.strip()
        if search_query and search_property:
            if search_property not in SEARCHABLE_COLUMNS:
                raise HTTPException(status_code=400, detail="Invalid search property")

            search_condition = f"{search_property} LIKE ?"
            query = f"SELECT * FROM {TABLE_NAME} WHERE {search_condition};"
            result = cursor.execute(query, (f"%{search_query}%",)).fetchall()
        else:
            query = f"SELECT * FROM {TABLE_NAME};"
            result = cursor.execute(query).fetchall()

        # Tạo DataFrame từ kết quả truy vấn
        columns = [description[0] for description in cursor.description]
        df = pd.DataFrame(result, columns=columns)
        
        # Tạo file CSV và trả về dữ liệu như một response
        output = io.StringIO()
        df.to_csv(output, index=False)
        output.seek(0)
        connection.close()
        
        return StreamingResponse(output, media_type='text/csv', headers={"Content-Disposition": f"attachment;filename=students.csv"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))