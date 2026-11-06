from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.all import ProductCategory, Product, SkuInfo, Store, StoreProduct
from app.schemas.all import (
    ProductCreate, ProductUpdate, ProductOut, CategoryOut, PageResp, SkuInfoOut,
)

router = APIRouter()


@router.get("/products/categories", response_model=List[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    rows = db.scalars(
        select(ProductCategory).where(ProductCategory.is_show == 1).order_by(
            ProductCategory.level, ProductCategory.sort_order, ProductCategory.category_id
        )
    ).all()
    # parent 组装树
    by_id = {c.category_id: CategoryOut.model_validate(c) for c in rows}
    roots: List[CategoryOut] = []
    for cat_out in by_id.values():
        if cat_out.parent_id and cat_out.parent_id in by_id:
            by_id[cat_out.parent_id].children.append(cat_out)
        else:
            roots.append(cat_out)
    return roots


@router.get("/products", response_model=PageResp[ProductOut])
def list_products(
    category_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    sort_by: str = Query("sales_count_desc"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(Product)
    if category_id:
        stmt = stmt.where(Product.category_id == category_id)
    if keyword:
        like = f"%{keyword}%"
        stmt = stmt.where(or_(Product.product_name.like(like), Product.subtitle.like(like)))

    # 默认 sales_count desc
    if sort_by == "sales_count_desc":
        stmt = stmt.order_by(Product.sales_count.desc(), Product.product_id.desc())
    else:
        stmt = stmt.order_by(Product.product_id.desc())

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    items = db.scalars(
        stmt.offset((page - 1) * size).limit(size).options(selectinload(Product.skus))
    ).all()
    return PageResp(total=total or 0, items=[ProductOut.model_validate(p) for p in items], page=page, size=size)


@router.get("/products/store-coverage")
def store_coverage(db: Session = Depends(get_db)):
    """商品在门店的覆盖情况：哪些门店在售、哪些门店没有，附带门店库存。"""
    stores = db.scalars(select(Store).order_by(Store.store_id)).all()
    rows = db.execute(
        select(StoreProduct.store_id, StoreProduct.product_id, StoreProduct.stock)
    ).all()
    name_map = {s.store_id: s.name for s in stores}
    coverage: dict[str, dict] = {}
    for store_id, product_id, stock in rows:
        item = coverage.setdefault(str(product_id), {"covered": 0, "stores": []})
        item["covered"] += 1
        item["stores"].append({"store_id": store_id, "name": name_map.get(store_id, ""), "stock": stock})
    return {
        "total_stores": len(stores),
        "stores": [{"store_id": s.store_id, "name": s.name} for s in stores],
        "coverage": coverage,
    }


@router.get("/products/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    p = db.scalar(
        select(Product).where(Product.product_id == product_id).options(selectinload(Product.skus))
    )
    if not p:
        raise HTTPException(status_code=404, detail="product not found")
    return ProductOut.model_validate(p)


@router.post("/products", response_model=ProductOut)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    skus_in = payload.skus or []
    data = payload.model_dump(exclude={"skus"})
    product = Product(**data)
    db.add(product)
    db.flush()

    for s in skus_in:
        sku = SkuInfo(product_id=product.product_id, **s.model_dump(exclude={"sku_id"}))
        db.add(sku)

    db.commit()
    db.refresh(product)
    # 手动 reload sku relationship
    db.refresh(product)
    return ProductOut.model_validate(product)


@router.put("/products/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    p = db.scalar(select(Product).where(Product.product_id == product_id))
    if not p:
        raise HTTPException(status_code=404, detail="product not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return ProductOut.model_validate(p)
