from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.database import get_db
from api.schemas import ChannelActivityPoint, MessageSearchResult, TopProduct, VisualContentStats


app = FastAPI(title="Medical Telegram Warehouse API", version="1.0.0")


@app.get("/api/reports/top-products", response_model=List[TopProduct])
def top_products(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    sql = text(
        """
        SELECT token, COUNT(*) AS mentions
        FROM (
            SELECT regexp_split_to_table(lower(message_text), '[^a-z0-9]+') AS token
            FROM marts.fct_messages
        ) t
        WHERE length(token) > 2
        GROUP BY token
        ORDER BY mentions DESC
        LIMIT :limit
        """
    )
    rows = db.execute(sql, {"limit": limit}).mappings().all()
    return rows


@app.get("/api/channels/{channel_name}/activity", response_model=List[ChannelActivityPoint])
def channel_activity(channel_name: str, db: Session = Depends(get_db)):
    sql = text(
        """
        SELECT d.full_date AS date,
               COUNT(*) AS message_count,
               AVG(f.view_count) AS avg_views
        FROM marts.fct_messages f
        JOIN marts.dim_channels c ON f.channel_key = c.channel_key
        JOIN marts.dim_dates d ON f.date_key = d.date_key
        WHERE c.channel_name ILIKE :channel_name
        GROUP BY d.full_date
        ORDER BY d.full_date
        """
    )
    rows = db.execute(sql, {"channel_name": channel_name}).mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="Channel not found or no data.")
    return rows


@app.get("/api/search/messages", response_model=List[MessageSearchResult])
def search_messages(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    sql = text(
        """
        SELECT f.message_id,
               c.channel_name,
               f.message_text,
               d.full_date AS message_date,
               f.view_count,
               f.forward_count
        FROM marts.fct_messages f
        JOIN marts.dim_channels c ON f.channel_key = c.channel_key
        JOIN marts.dim_dates d ON f.date_key = d.date_key
        WHERE f.message_text ILIKE '%' || :query || '%'
        ORDER BY d.full_date DESC
        LIMIT :limit
        """
    )
    rows = db.execute(sql, {"query": query, "limit": limit}).mappings().all()
    return rows


@app.get("/api/reports/visual-content", response_model=List[VisualContentStats])
def visual_content_stats(db: Session = Depends(get_db)):
    sql = text(
        """
        WITH totals AS (
            SELECT c.channel_name,
                   COUNT(*) AS total_messages,
                   SUM(CASE WHEN f.has_image THEN 1 ELSE 0 END) AS image_messages
            FROM marts.fct_messages f
            JOIN marts.dim_channels c ON f.channel_key = c.channel_key
            GROUP BY c.channel_name
        ),
        categories AS (
            SELECT c.channel_name,
                   SUM(CASE WHEN d.image_category = 'promotional' THEN 1 ELSE 0 END) AS promotional,
                   SUM(CASE WHEN d.image_category = 'product_display' THEN 1 ELSE 0 END) AS product_display,
                   SUM(CASE WHEN d.image_category = 'lifestyle' THEN 1 ELSE 0 END) AS lifestyle,
                   SUM(CASE WHEN d.image_category = 'other' THEN 1 ELSE 0 END) AS other
            FROM marts.fct_image_detections d
            JOIN marts.dim_channels c ON d.channel_key = c.channel_key
            GROUP BY c.channel_name
        )
        SELECT t.channel_name,
               t.total_messages,
               t.image_messages,
               (t.image_messages::float / NULLIF(t.total_messages, 0)) AS image_rate,
               COALESCE(c.promotional, 0) AS promotional,
               COALESCE(c.product_display, 0) AS product_display,
               COALESCE(c.lifestyle, 0) AS lifestyle,
               COALESCE(c.other, 0) AS other
        FROM totals t
        LEFT JOIN categories c ON t.channel_name = c.channel_name
        ORDER BY image_rate DESC NULLS LAST
        """
    )
    rows = db.execute(sql).mappings().all()
    return rows


