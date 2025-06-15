from datetime import UTC, datetime, timedelta
from typing import Any
from fastapi import FastAPI, HTTPException
from sqlalchemy import DateTime, ForeignKey, create_engine, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker


from mailing import AssetMailer

# Assets belongs to parent and author
# at any given time, one parent can only have one active asset


class Asset(DeclarativeBase):
    __tablename__ = "asset"

    id: Mapped[int]
    title: Mapped[str]
    width: Mapped[int]
    height: Mapped[int]
    active: Mapped[bool]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    parent_id: Mapped[int] = mapped_column(ForeignKey("parent.id"))
    parent: Mapped["Parent"] = relationship(back_populates="assets")

    author_id: Mapped[int] = mapped_column(ForeignKey("author.id"))
    author: Mapped["Author"] = relationship(back_populates="assets")


class Parent(DeclarativeBase):
    __tablename__ = "parent"

    id: Mapped[int]

    assets: Mapped[list["Asset"]] = relationship(back_populates="parent")


class Author(DeclarativeBase):
    __tablename__ = "author"

    id: Mapped[int]
    name: Mapped[str]
    assets: Mapped[list["Asset"]] = relationship(back_populates="author")


engine = create_engine("some:fake:url")
session_maker = sessionmaker(
    autocommit=False,
    bind=engine,
)

app = FastAPI()


@app.get("/assets")
def index() -> list[dict[str, Any]]:
    # this endpoint is VERY slow, let's figure out why
    with session_maker() as session:
        collection: list[dict[str, Any]] = []

        two_days_ago = datetime.now(tz=UTC) - timedelta(days=2)
        res = session.execute(
            select(Asset)
            .where(Asset.created_at > two_days_ago)
            .order_by(Asset.id.asc())
        )
        for asset in res.scalars().all():
            collection.append({
                "title": asset.title,
                "full_size": asset.width + "x" + asset.height + "px",
                "parent_id": asset.parent.id,
                "author": asset.author.name,
            })

    return collection


@app.post("/assets/{asset_id}/activate")
def activate(asset_id: int) -> None:
    with session_maker() as session:
        asset = session.get(Asset, asset_id)
        if not asset:
            raise HTTPException(400, "No asset found")
        
        activate_asset(asset)

@app.post("/assets/{asset_id}/deactivate")
def deactivate(asset_id: int) -> None:
    with session_maker() as session:
        asset = session.get(Asset, asset_id)
        if not asset:
            raise HTTPException(400, "No asset found")

        asset.active = False
        AssetMailer.deactivated(asset).deliver_now()
        session.commit()


def activate_asset(session: Session, asset: Asset) -> None:
    asset.active = True
    session.commit()

    for other_asset in asset.parent.assets:
        if other_asset == asset:
            continue

        if not other_asset.active:
            continue

        other_asset.active = False
        session.commit()

    AssetMailer.activated(asset).deliver_now()
