from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor
import asyncio
import json
import logging
from datetime import datetime

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 필요한 경우 도메인 추가
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PostgreSQL 연결 설정
def get_db_connection():
    try:
        connection = psycopg2.connect(
            dbname="postgre_test",
            user="ohiopostgre",
            password="ohio1234",
            host="ohiopostgre.c782uy2a401d.us-east-2.rds.amazonaws.com",
            port="5432"
        )
        logger.info("Database connection established.")
        return connection
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return None

# SSE 스트림 생성 함수
async def stream_data(table_name):
    connection = get_db_connection()
    if connection is None:
        logger.error("Database connection could not be established.")
        raise HTTPException(status_code=500, detail="Database connection failed.")

    cursor = connection.cursor(cursor_factory=RealDictCursor)
    logger.info(f"Starting data stream for table: {table_name}")

    try:
        while True:
            cursor.execute(f"""
            SELECT * FROM {table_name}
            ORDER BY timestamp DESC
            LIMIT 1;
            """)
            data = cursor.fetchone()
            if data:
                # datetime 형식을 문자열로 변환
                if isinstance(data["timestamp"], datetime):
                    data["timestamp"] = data["timestamp"].strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"Fetched data from {table_name}: {data}")
                yield f"data: {json.dumps(data)}\n\n"
            else:
                logger.warning(f"No data available in {table_name}.")
            await asyncio.sleep(0.5)  # 주기 설정
    except asyncio.CancelledError:
        logger.info(f"Client disconnected from {table_name} stream.")
    except Exception as e:
        logger.error(f"Error in stream_data for {table_name}: {e}")
    finally:
        cursor.close()
        connection.close()
        logger.info(f"Database connection closed for table: {table_name}")

# Pangyo 데이터 스트림 엔드포인트
@app.get("/streamPangyo")
async def stream_pangyo():
    logger.info("Client connected to /streamPangyo")
    return StreamingResponse(stream_data("pangyo15"), media_type="text/event-stream")

# Busan 데이터 스트림 엔드포인트
@app.get("/streamBusan")
async def stream_busan():
    logger.info("Client connected to /streamBusan")
    return StreamingResponse(stream_data("busan15"), media_type="text/event-stream")
