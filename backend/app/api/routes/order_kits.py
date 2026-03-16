from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.order_kit import (
    AllocateSelectedKitsRequest,
    AllocationSummaryRead,
    AvailableKitRead,
    OrderKitCreate,
    OrderKitItemRead,
    OrderKitRead,
)
from app.services.order_kit_service import (
    allocate_kit_to_order,
    allocate_selected_kits_to_order,
    auto_allocate_kits_to_order,
    delete_order_kit,
    get_available_kits_for_order,
    get_order_kits_by_order_id,
    list_order_kits,
)

router = APIRouter(tags=["order-kits"])


@router.post("/order-kits", response_model=OrderKitRead)
def allocate_kit_to_order_endpoint(
    data: OrderKitCreate,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return allocate_kit_to_order(db, data, acting_user_id)


@router.get("/order-kits", response_model=list[OrderKitItemRead])
def list_order_kits_endpoint(db: Session = Depends(get_db)):
    items = list_order_kits(db)

    return [
        OrderKitItemRead(
            id=item.id,
            order_id=item.order_id,
            order_name=item.order.name,
            kit_id=item.kit_id,
            kit_name=item.kit.name,
            product_id=item.kit.product_id,
            product_name=item.kit.product.name,
            product_hcp_code=item.kit.product.hcp_code,
            allocated_quantity=item.allocated_quantity,
            allocated_at=item.allocated_at,
            allocated_by_user_id=item.allocated_by_user_id,
        )
        for item in items
    ]


@router.get("/orders/{order_id}/kits", response_model=list[OrderKitItemRead])
def get_order_kits_by_order_id_endpoint(
    order_id: int,
    db: Session = Depends(get_db),
):
    items = get_order_kits_by_order_id(db, order_id)

    return [
        OrderKitItemRead(
            id=item.id,
            order_id=item.order_id,
            order_name=item.order.name,
            kit_id=item.kit_id,
            kit_name=item.kit.name,
            product_id=item.kit.product_id,
            product_name=item.kit.product.name,
            product_hcp_code=item.kit.product.hcp_code,
            allocated_quantity=item.allocated_quantity,
            allocated_at=item.allocated_at,
            allocated_by_user_id=item.allocated_by_user_id,
        )
        for item in items
    ]


@router.get("/orders/{order_id}/available-kits", response_model=list[AvailableKitRead])
def get_available_kits_for_order_endpoint(
    order_id: int,
    db: Session = Depends(get_db),
):
    kits = get_available_kits_for_order(db, order_id)

    return [
        AvailableKitRead(
            kit_id=kit.id,
            kit_name=kit.name,
            product_id=kit.product_id,
            product_name=kit.product.name,
            product_hcp_code=kit.product.hcp_code,
            quantity=kit.quantity,
            remaining_quantity=kit.remaining_quantity,
            is_complete=kit.is_complete,
        )
        for kit in kits
    ]


@router.post(
    "/orders/{order_id}/allocate-selected-kits",
    response_model=AllocationSummaryRead,
)
def allocate_selected_kits_to_order_endpoint(
    order_id: int,
    data: AllocateSelectedKitsRequest,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return allocate_selected_kits_to_order(
        db,
        order_id,
        data.kit_ids,
        acting_user_id,
    )


@router.post(
    "/orders/{order_id}/auto-allocate-kits",
    response_model=AllocationSummaryRead,
)
def auto_allocate_kits_to_order_endpoint(
    order_id: int,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    return auto_allocate_kits_to_order(db, order_id, acting_user_id)


@router.delete("/order-kits/{order_kit_id}", response_model=OrderKitItemRead)
def delete_order_kit_endpoint(
    order_kit_id: int,
    acting_user_id: int = Query(...),
    db: Session = Depends(get_db),
):
    item = delete_order_kit(db, order_kit_id, acting_user_id)

    return OrderKitItemRead(
        id=item.id,
        order_id=item.order_id,
        order_name=item.order.name,
        kit_id=item.kit_id,
        kit_name=item.kit.name,
        product_id=item.kit.product_id,
        product_name=item.kit.product.name,
        product_hcp_code=item.kit.product.hcp_code,
        allocated_quantity=item.allocated_quantity,
        allocated_at=item.allocated_at,
        allocated_by_user_id=item.allocated_by_user_id,
    )