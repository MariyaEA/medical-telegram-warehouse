"""FastAPI analytical API for the medical Telegram warehouse."""
from __future__ import annotations

from typing import List
from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from api.database import get_db
from api.schemas import TopProduct, ChannelActivity, MessageSearchResult, VisualContentStats

app = FastAPI(
    title="Medical Telegram Warehouse API",
    version="1.0.0",
    description="Analytical API for Telegram-based Ethiopian medical business insights.",
)


@app.get("/health", tags=["Health"])
def health_check() -> dict:
    return {"status": "ok"}


@app.get("/api/reports/top-products", response_model=List[TopProduct], tags=["Reports"])
def get_top_products(limit: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    """Return frequently mentioned medical/product terms across all channels."""
    sql = text("""
        with tokens as (
            select regexp_split_to_table(lower(message_text), '\\s+') as token
            from marts.fct_messages
            where message_text is not null
        )
        select token as product_term, count(*)::int as mention_count
        from tokens
        where length(token) > 3
          and token not in ('with', 'from', 'this', 'that', 'available', 'price')
        group by token
        order by mention_count desc
        limit :limit
    """)
    try:
        return [dict(row._mapping) for row in db.execute(sql, {"limit": limit}).fetchall()]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database query failed") from exc


@app.get("/api/channels/{channel_name}/activity", response_model=List[ChannelActivity], tags=["Channels"])
def get_channel_activity(channel_name: str, db: Session = Depends(get_db)):
    """Return daily posting activity and engagement metrics for a specific channel."""
    sql = text("""
        select
            dc.channel_name,
            dd.full_date as activity_date,
            count(fm.message_id)::int as post_count,
            coalesce(sum(fm.view_count), 0)::int as total_views,
            coalesce(sum(fm.forward_count), 0)::int as total_forwards
        from marts.fct_messages fm
        join marts.dim_channels dc on fm.channel_key = dc.channel_key
        join marts.dim_dates dd on fm.date_key = dd.date_key
        where lower(dc.channel_name) = lower(:channel_name)
        group by dc.channel_name, dd.full_date
        order by dd.full_date
    """)
    try:
        rows = [dict(row._mapping) for row in db.execute(sql, {"channel_name": channel_name}).fetchall()]
        if not rows:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found or no activity available")
        return rows
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database query failed") from exc


@app.get("/api/search/messages", response_model=List[MessageSearchResult], tags=["Search"])
def search_messages(
    query: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search Telegram messages containing a keyword."""
    sql = text("""
        select
            fm.message_id,
            dc.channel_name,
            dd.full_date as message_date,
            fm.message_text,
            fm.view_count,
            fm.forward_count,
            fm.has_image
        from marts.fct_messages fm
        join marts.dim_channels dc on fm.channel_key = dc.channel_key
        join marts.dim_dates dd on fm.date_key = dd.date_key
        where lower(fm.message_text) like '%' || lower(:query) || '%'
        order by fm.view_count desc
        limit :limit
    """)
    try:
        return [dict(row._mapping) for row in db.execute(sql, {"query": query, "limit": limit}).fetchall()]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database query failed") from exc


@app.get("/api/reports/visual-content", response_model=List[VisualContentStats], tags=["Reports"])
def get_visual_content_stats(db: Session = Depends(get_db)):
    """Return visual content usage and YOLO-derived image category statistics by channel."""
    sql = text("""
        select
            dc.channel_name,
            count(distinct fm.message_id)::int as total_messages,
            count(distinct case when fm.has_image then fm.message_id end)::int as image_messages,
            round(count(distinct case when fm.has_image then fm.message_id end)::numeric / nullif(count(distinct fm.message_id), 0), 4)::float as image_share,
            count(distinct case when fid.image_category = 'promotional' then fid.message_id end)::int as promotional_posts,
            count(distinct case when fid.image_category = 'product_display' then fid.message_id end)::int as product_display_posts,
            count(distinct case when fid.image_category = 'lifestyle' then fid.message_id end)::int as lifestyle_posts,
            count(distinct case when fid.image_category = 'other' then fid.message_id end)::int as other_posts
        from marts.fct_messages fm
        join marts.dim_channels dc on fm.channel_key = dc.channel_key
        left join marts.fct_image_detections fid on fm.message_id = fid.message_id
        group by dc.channel_name
        order by image_messages desc
    """)
    try:
        return [dict(row._mapping) for row in db.execute(sql).fetchall()]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database query failed") from exc
