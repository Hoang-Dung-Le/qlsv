from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse
import pandas as pd
import sqlite3
import io
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE_FILE = "students.db"
TABLE_NAME = "students"
ITEMS_PER_PAGE = 10  # Số lượng sinh viên hiển thị trên mỗi trang
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


@app.get("/students/", response_model=dict)
async def get_students(page: int = Query(1, ge=1)):
    try:
        connection = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, check_same_thread=False)
        connection.execute('pragma encoding=utf8')
        cursor = connection.cursor()

        total_records_query = f"SELECT COUNT(*) FROM {TABLE_NAME};"
        total_records = cursor.execute(total_records_query).fetchone()[0]

        total_pages = (total_records + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

        offset = (page - 1) * ITEMS_PER_PAGE
        limit = ITEMS_PER_PAGE

        query = f"SELECT * FROM {TABLE_NAME} LIMIT {limit} OFFSET {offset};"
        result = cursor.execute(query).fetchall()

        students_list = []
        for row in result:
            student_dict = {
                "MASV": row[0],
                "HoTenSV": row[1],
                "NgaySinh": row[2],
                "Phai": row[3],
                "MaLop": row[4],
                "Nganh": row[5],
                "DienThoaiGiaDinh": row[6],
                "DienThoaiCaNhan": row[7],
                "DiaChiLienHe": row[8],
                "Email": row[9],
                "CoViecLam": row[10],
                "LoaiDonViLamViec": row[11],
                "TenDonViLamViec": row[12],
                "DiaChiDonViLamViec": row[13],
                "TinhThanhPho": row[14],
            }
            students_list.append(student_dict)

        connection.close()

        return {"students": students_list, "total_pages": total_pages}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Chức năng tìm kiếm và xuất Excel
@app.get("/students/search", response_model=dict)
async def search_and_export_students(
    search_query: str,
    search_property: str,  # Thêm tham số cho thuộc tính cần tìm kiếm
    page: int = Query(1, ge=1)
):
    try:
        # Kiểm tra xem search_property có trong danh sách cột không
        if search_property not in COLUMN_NAMES:
            raise HTTPException(status_code=400, detail="Invalid search property")

        connection = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, check_same_thread=False)
        connection.execute('pragma encoding=utf8')
        cursor = connection.cursor()

        # Thực hiện tìm kiếm
        search_query = search_query.strip()
        if search_query:
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
            student_dict = {
                "MASV": row[0],
                "HoTenSV": row[1],
                "NgaySinh": row[2],
                "Phai": row[3],
                "MaLop": row[4],
                "Nganh": row[5],
                "DienThoaiGiaDinh": row[6],
                "DienThoaiCaNhan": row[7],
                "DiaChiLienHe": row[8],
                "Email": row[9],
                "CoViecLam": row[10],
                "LoaiDonViLamViec": row[11],
                "TenDonViLamViec": row[12],
                "DiaChiDonViLamViec": row[13],
                "TinhThanhPho": row[14],
            }
            students_list.append(student_dict)

        connection.close()
        print(students_list)
        return {"students": students_list, "total_pages": total_pages}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Chức năng xuất Excel
@app.get("/students/export-excel")
async def export_students_to_excel(search_query: str = ''):
    try:
        connection = sqlite3.connect(DATABASE_FILE, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES, check_same_thread=False)
        connection.execute('pragma encoding=utf8')
        cursor = connection.cursor()

        # Thực hiện tìm kiếm
        search_query = search_query.strip()
        if search_query:
            search_condition = " OR ".join([f"{column} LIKE ?" for column in SEARCHABLE_COLUMNS])
            query = f"SELECT * FROM {TABLE_NAME} WHERE {search_condition};"
            result = cursor.execute(query, (f"%{search_query}%",)).fetchall()
        else:
            query = f"SELECT * FROM {TABLE_NAME};"
            result = cursor.execute(query).fetchall()

        # Tạo DataFrame từ kết quả truy vấn
        columns = [description[0] for description in cursor.description]
        df = pd.DataFrame(result, columns=columns)

        # Tạo file Excel và trả về dữ liệu như một response
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Students')
            writer.save()

        output.seek(0)
        connection.close()

        return StreamingResponse(output, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

