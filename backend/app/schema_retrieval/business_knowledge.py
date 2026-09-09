from app.schema_retrieval.knowledge import BusinessConcept


BUSINESS_CONCEPTS = [
    BusinessConcept(
        name="Revenue",
        definition=(
            "The monetary value generated from "
            "purchased order items."
        ),
        related_tables=[
            "orders",
            "order_items",
        ],
        related_columns=[
            "order_items.quantity",
            "order_items.unit_price",
        ],
        calculation=(
            "SUM(order_items.quantity * "
            "order_items.unit_price)"
        ),
    ),

    BusinessConcept(
        name="Customer",
        definition=(
            "A person or entity represented in the "
            "customer records."
        ),
        related_tables=[
            "customers",
        ],
        related_columns=[
            "customers.customer_id",
            "customers.signup_date",
            "customers.customer_segment",
        ],
    ),

    BusinessConcept(
        name="Product",
        definition=(
            "An item available for purchase and "
            "represented in the product catalog."
        ),
        related_tables=[
            "products",
        ],
        related_columns=[
            "products.product_id",
            "products.product_name",
            "products.category_id",
            "products.supplier_id",
        ],
    ),

    BusinessConcept(
        name="Order",
        definition=(
            "A customer purchase transaction "
            "recorded in the order system."
        ),
        related_tables=[
            "orders",
            "order_items",
        ],
        related_columns=[
            "orders.order_id",
            "orders.customer_id",
            "orders.order_date",
            "orders.status",
        ],
    ),

    BusinessConcept(
        name="Order Item",
        definition=(
            "An individual product line belonging "
            "to a customer order."
        ),
        related_tables=[
            "order_items",
            "orders",
            "products",
        ],
        related_columns=[
            "order_items.order_id",
            "order_items.product_id",
            "order_items.quantity",
            "order_items.unit_price",
        ],
    ),

    BusinessConcept(
        name="Product Category",
        definition=(
            "A classification used to group products."
        ),
        related_tables=[
            "categories",
            "products",
        ],
        related_columns=[
            "categories.category_id",
            "categories.category_name",
            "products.category_id",
        ],
    ),

    BusinessConcept(
        name="Customer Segment",
        definition=(
            "A classification assigned to customers "
            "based on the customer segmentation field."
        ),
        related_tables=[
            "customers",
        ],
        related_columns=[
            "customers.customer_segment",
        ],
    ),

    BusinessConcept(
        name="Average Order Value",
        definition=(
            "The average monetary value calculated "
            "across orders."
        ),
        related_tables=[
            "orders",
            "order_items",
        ],
        related_columns=[
            "orders.order_id",
            "order_items.quantity",
            "order_items.unit_price",
        ],
        calculation=(
            "Total order-item value divided by "
            "the number of orders."
        ),
    ),
]