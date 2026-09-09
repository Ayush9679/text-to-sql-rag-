import argparse
import random
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta

from dotenv import load_dotenv
from faker import Faker
from sqlalchemy import MetaData, create_engine, delete, insert, select, text
import os


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

load_dotenv()

DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "text-to-sql")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")

if not DB_PASSWORD:
    raise RuntimeError(
        "POSTGRES_PASSWORD is missing. "
        "Add it to backend/.env"
    )


DATABASE_URL = (
    f"postgresql+psycopg://"
    f"{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

fake = Faker("en_IN")

RANDOM_SEED = 42
random.seed(RANDOM_SEED)
Faker.seed(RANDOM_SEED)


# ---------------------------------------------------------
# Dataset size
# ---------------------------------------------------------

NUM_CATEGORIES = 10
NUM_SUPPLIERS = 20
NUM_CUSTOMERS = 100
NUM_PRODUCTS = 200
NUM_ORDERS = 1000
NUM_REVIEWS = 500

MIN_ITEMS_PER_ORDER = 1
MAX_ITEMS_PER_ORDER = 5


# ---------------------------------------------------------
# Business configuration
# ---------------------------------------------------------

CATEGORIES = [
    ("Electronics", "Electronic devices and accessories"),
    ("Clothing", "Fashion and apparel products"),
    ("Books", "Books and educational material"),
    ("Home & Kitchen", "Home appliances and kitchen products"),
    ("Sports", "Sports equipment and accessories"),
    ("Beauty", "Beauty and personal care products"),
    ("Toys", "Toys and entertainment products"),
    ("Grocery", "Food and household grocery products"),
    ("Furniture", "Furniture and home furnishing products"),
    ("Automotive", "Automotive accessories and products"),
]

PRODUCT_PREFIXES = {
    "Electronics": [
        "Wireless",
        "Smart",
        "Pro",
        "Ultra",
        "Digital",
        "Portable",
    ],
    "Clothing": [
        "Classic",
        "Premium",
        "Casual",
        "Comfort",
        "Urban",
        "Essential",
    ],
    "Books": [
        "Advanced",
        "Practical",
        "Complete",
        "Modern",
        "Essential",
        "Beginner",
    ],
    "Home & Kitchen": [
        "Smart",
        "Premium",
        "Classic",
        "Compact",
        "Modern",
        "Professional",
    ],
    "Sports": [
        "Pro",
        "Elite",
        "Performance",
        "Active",
        "Training",
        "Competition",
    ],
    "Beauty": [
        "Natural",
        "Premium",
        "Organic",
        "Professional",
        "Daily",
        "Luxury",
    ],
    "Toys": [
        "Creative",
        "Fun",
        "Interactive",
        "Educational",
        "Adventure",
        "Kids",
    ],
    "Grocery": [
        "Fresh",
        "Organic",
        "Premium",
        "Daily",
        "Healthy",
        "Natural",
    ],
    "Furniture": [
        "Modern",
        "Classic",
        "Premium",
        "Compact",
        "Elegant",
        "Comfort",
    ],
    "Automotive": [
        "Pro",
        "Premium",
        "Universal",
        "Performance",
        "Advanced",
        "Smart",
    ],
}

PRODUCT_TYPES = {
    "Electronics": [
        "Laptop",
        "Smartphone",
        "Headphones",
        "Keyboard",
        "Mouse",
        "Monitor",
        "Speaker",
        "Power Bank",
        "Smartwatch",
        "Tablet",
    ],
    "Clothing": [
        "T-Shirt",
        "Jeans",
        "Jacket",
        "Hoodie",
        "Shirt",
        "Dress",
        "Sneakers",
        "Track Pants",
    ],
    "Books": [
        "Programming Book",
        "Business Book",
        "Science Book",
        "Novel",
        "Mathematics Book",
        "AI Book",
        "Management Book",
    ],
    "Home & Kitchen": [
        "Mixer",
        "Cookware Set",
        "Air Fryer",
        "Coffee Maker",
        "Vacuum Cleaner",
        "Blender",
        "Dinner Set",
    ],
    "Sports": [
        "Cricket Bat",
        "Football",
        "Tennis Racket",
        "Yoga Mat",
        "Running Shoes",
        "Dumbbells",
        "Sports Bag",
    ],
    "Beauty": [
        "Face Wash",
        "Moisturizer",
        "Perfume",
        "Shampoo",
        "Hair Dryer",
        "Skin Care Kit",
    ],
    "Toys": [
        "Remote Car",
        "Building Blocks",
        "Board Game",
        "Puzzle",
        "Action Figure",
        "Educational Kit",
    ],
    "Grocery": [
        "Coffee",
        "Tea",
        "Rice",
        "Snacks",
        "Cooking Oil",
        "Cereal",
        "Dry Fruits",
    ],
    "Furniture": [
        "Office Chair",
        "Study Table",
        "Sofa",
        "Bookshelf",
        "Bedside Table",
        "Dining Chair",
    ],
    "Automotive": [
        "Car Charger",
        "Phone Holder",
        "Cleaning Kit",
        "Seat Cover",
        "LED Light",
        "Air Compressor",
    ],
}

PAYMENT_METHODS = [
    "upi",
    "credit_card",
    "debit_card",
    "net_banking",
    "cash",
    "wallet",
]


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def money(value):
    """Return a Decimal rounded to two decimal places."""
    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def random_price():
    """
    Generate realistic retail prices with a long-tail distribution.
    """
    ranges = [
        (100, 1000),
        (500, 5000),
        (1000, 15000),
        (5000, 50000),
        (10000, 100000),
    ]

    selected_range = random.choices(
        ranges,
        weights=[30, 30, 20, 15, 5],
        k=1,
    )[0]

    return money(
        random.uniform(
            selected_range[0],
            selected_range[1],
        )
    )


def random_date(start_year=2024, end_year=2026):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31, 23, 59, 59)

    total_seconds = int((end - start).total_seconds())

    random_seconds = random.randint(
        0,
        total_seconds
    )

    return start + timedelta(
        seconds=random_seconds
    )


def random_customer_segment():
    return random.choices(
        ["new", "regular", "premium", "vip"],
        weights=[35, 45, 15, 5],
        k=1,
    )[0]


def random_order_status():
    return random.choices(
        [
            "pending",
            "confirmed",
            "shipped",
            "delivered",
            "cancelled",
            "refunded",
        ],
        weights=[
            5,
            10,
            15,
            55,
            10,
            5,
        ],
        k=1,
    )[0]


def random_payment_status(order_status):
    if order_status == "cancelled":
        return random.choices(
            ["failed", "refunded"],
            weights=[70, 30],
            k=1,
        )[0]

    if order_status == "refunded":
        return "refunded"

    if order_status == "pending":
        return random.choices(
            ["pending", "completed"],
            weights=[60, 40],
            k=1,
        )[0]

    return random.choices(
        ["completed", "failed"],
        weights=[97, 3],
        k=1,
    )[0]


# ---------------------------------------------------------
# Database metadata
# ---------------------------------------------------------

def load_tables():
    metadata = MetaData()

    metadata.reflect(
        bind=engine,
        schema="analytics",
    )

    required_tables = {
        "categories",
        "customers",
        "suppliers",
        "products",
        "orders",
        "order_items",
        "payments",
        "reviews",
    }

    existing_tables = set(metadata.tables.keys())

    missing = []

    for table_name in required_tables:
        key = f"analytics.{table_name}"

        if key not in existing_tables:
            missing.append(table_name)

    if missing:
        raise RuntimeError(
            "Missing required tables: "
            + ", ".join(missing)
        )

    return metadata


# ---------------------------------------------------------
# Reset database data
# ---------------------------------------------------------

def reset_data(connection, tables):
    print("Resetting existing analytics data...")

    delete_order_items = delete(tables["analytics.order_items"])
    delete_payments = delete(tables["analytics.payments"])
    delete_reviews = delete(tables["analytics.reviews"])
    delete_orders = delete(tables["analytics.orders"])
    delete_products = delete(tables["analytics.products"])
    delete_customers = delete(tables["analytics.customers"])
    delete_suppliers = delete(tables["analytics.suppliers"])
    delete_categories = delete(tables["analytics.categories"])

    connection.execute(delete_order_items)
    connection.execute(delete_payments)
    connection.execute(delete_reviews)
    connection.execute(delete_orders)
    connection.execute(delete_products)
    connection.execute(delete_customers)
    connection.execute(delete_suppliers)
    connection.execute(delete_categories)

    connection.execute(
        text(
            """
            ALTER TABLE analytics.categories
            ALTER COLUMN category_id RESTART WITH 1;

            ALTER TABLE analytics.suppliers
            ALTER COLUMN supplier_id RESTART WITH 1;

            ALTER TABLE analytics.customers
            ALTER COLUMN customer_id RESTART WITH 1;

            ALTER TABLE analytics.products
            ALTER COLUMN product_id RESTART WITH 1;

            ALTER TABLE analytics.orders
            ALTER COLUMN order_id RESTART WITH 1;

            ALTER TABLE analytics.order_items
            ALTER COLUMN order_item_id RESTART WITH 1;

            ALTER TABLE analytics.payments
            ALTER COLUMN payment_id RESTART WITH 1;

            ALTER TABLE analytics.reviews
            ALTER COLUMN review_id RESTART WITH 1;
            """
        )
    )

    print("Existing data removed.")


# ---------------------------------------------------------
# Categories
# ---------------------------------------------------------

def generate_categories(connection, tables):
    table = tables["analytics.categories"]

    rows = []

    for name, description in CATEGORIES:
        rows.append(
            {
                "category_name": name,
                "description": description,
            }
        )

    result = connection.execute(
        insert(table).returning(
            table.c.category_id,
            table.c.category_name,
        ),
        rows,
    )

    records = result.fetchall()

    category_map = {
        row.category_name: row.category_id
        for row in records
    }

    print(f"Inserted {len(records)} categories.")

    return category_map


# ---------------------------------------------------------
# Suppliers
# ---------------------------------------------------------

def generate_suppliers(connection, tables):
    table = tables["analytics.suppliers"]

    rows = []

    for index in range(NUM_SUPPLIERS):
        rows.append(
            {
                "supplier_name": (
                    f"{fake.company()} "
                    f"Supply {index + 1}"
                ),
                "city": fake.city(),
                "state": fake.state(),
                "country": "India",
                "rating": money(
                    random.uniform(3.0, 5.0)
                ),
            }
        )

    result = connection.execute(
        insert(table).returning(
            table.c.supplier_id,
            table.c.supplier_name,
        ),
        rows,
    )

    records = result.fetchall()

    supplier_ids = [
        row.supplier_id
        for row in records
    ]

    print(f"Inserted {len(records)} suppliers.")

    return supplier_ids


# ---------------------------------------------------------
# Customers
# ---------------------------------------------------------

def generate_customers(connection, tables):
    table = tables["analytics.customers"]

    rows = []

    for _ in range(NUM_CUSTOMERS):
        rows.append(
            {
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "email": fake.unique.email(),
                "phone": fake.msisdn()[:15],
                "city": fake.city(),
                "state": fake.state(),
                "country": "India",
                "signup_date": fake.date_between(
                    start_date="-3y",
                    end_date="today",
                ),
                "customer_segment": (
                    random_customer_segment()
                ),
            }
        )

    result = connection.execute(
        insert(table).returning(
            table.c.customer_id,
        ),
        rows,
    )

    customer_ids = [
        row.customer_id
        for row in result.fetchall()
    ]

    print(f"Inserted {len(customer_ids)} customers.")

    return customer_ids


# ---------------------------------------------------------
# Products
# ---------------------------------------------------------

def generate_products(
    connection,
    tables,
    category_map,
    supplier_ids,
):
    table = tables["analytics.products"]

    rows = []

    for _ in range(NUM_PRODUCTS):
        category_name = random.choice(
            list(category_map.keys())
        )

        prefix = random.choice(
            PRODUCT_PREFIXES[category_name]
        )

        product_type = random.choice(
            PRODUCT_TYPES[category_name]
        )

        product_name = (
            f"{prefix} {product_type} "
            f"{random.randint(100, 9999)}"
        )

        unit_price = random_price()

        # Cost is always below selling price.
        cost_percentage = random.uniform(
            0.45,
            0.85,
        )

        cost_price = money(
            unit_price * Decimal(str(cost_percentage))
        )

        rows.append(
            {
                "category_id": category_map[
                    category_name
                ],
                "supplier_id": random.choice(
                    supplier_ids
                ),
                "product_name": product_name,
                "description": (
                    f"{product_name} from the "
                    f"{category_name} category."
                ),
                "unit_price": unit_price,
                "cost_price": cost_price,
                "stock_quantity": random.randint(
                    0,
                    500,
                ),
                "is_active": random.random() > 0.05,
            }
        )

    result = connection.execute(
        insert(table).returning(
            table.c.product_id,
            table.c.unit_price,
            table.c.cost_price,
        ),
        rows,
    )

    products = [
        {
            "product_id": row.product_id,
            "unit_price": Decimal(row.unit_price),
            "cost_price": Decimal(row.cost_price),
        }
        for row in result.fetchall()
    ]

    print(f"Inserted {len(products)} products.")

    return products


# ---------------------------------------------------------
# Orders + Order Items
# ---------------------------------------------------------

def generate_orders(
    connection,
    tables,
    customer_ids,
    products,
):
    orders_table = tables["analytics.orders"]
    items_table = tables["analytics.order_items"]

    order_ids = []

    total_items = 0

    for order_number in range(NUM_ORDERS):
        customer_id = random.choice(customer_ids)

        order_status = random_order_status()

        order_date = random_date(
            start_year=2024,
            end_year=2026,
        )

        selected_products = random.sample(
            products,
            k=random.randint(
                MIN_ITEMS_PER_ORDER,
                MAX_ITEMS_PER_ORDER,
            ),
        )

        item_rows = []

        subtotal = Decimal("0.00")
        total_discount = Decimal("0.00")

        for product in selected_products:
            quantity = random.randint(1, 5)

            unit_price = product["unit_price"]

            gross = money(
                unit_price * quantity
            )

            discount_percentage = random.uniform(
                0.00,
                0.20,
            )

            item_discount = money(
                gross
                * Decimal(
                    str(discount_percentage)
                )
            )

            subtotal += gross
            total_discount += item_discount

            item_rows.append(
                {
                    "product_id": product["product_id"],
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "discount": item_discount,
                }
            )

        net_amount = (
            subtotal - total_discount
        )

        tax = money(
            net_amount * Decimal("0.18")
        )

        shipping_cost = (
            Decimal("0.00")
            if net_amount >= Decimal("2000")
            else Decimal("99.00")
        )

        total_amount = money(
            net_amount
            + tax
            + shipping_cost
        )

        order_result = connection.execute(
            insert(orders_table)
            .values(
                {
                    "customer_id": customer_id,
                    "order_date": order_date,
                    "status": order_status,
                    "subtotal": subtotal,
                    "discount": total_discount,
                    "tax": tax,
                    "shipping_cost": shipping_cost,
                    "total_amount": total_amount,
                }
            )
            .returning(orders_table.c.order_id)
        )

        order_id = order_result.scalar_one()

        order_ids.append(
            {
                "order_id": order_id,
                "customer_id": customer_id,
                "order_date": order_date,
                "status": order_status,
                "total_amount": total_amount,
            }
        )

        for item in item_rows:
            connection.execute(
                insert(items_table).values(
                    {
                        "order_id": order_id,
                        **item,
                    }
                )
            )

            total_items += 1

    print(
        f"Inserted {len(order_ids)} orders "
        f"and {total_items} order items."
    )

    return order_ids


# ---------------------------------------------------------
# Payments
# ---------------------------------------------------------

def generate_payments(
    connection,
    tables,
    orders,
):
    table = tables["analytics.payments"]

    rows = []

    for order in orders:
        payment_status = random_payment_status(
            order["status"]
        )

        payment_amount = order["total_amount"]

        if payment_status == "failed":
            payment_amount = Decimal("0.00")

        payment_date = order["order_date"]

        rows.append(
            {
                "order_id": order["order_id"],
                "payment_date": payment_date,
                "payment_method": random.choice(
                    PAYMENT_METHODS
                ),
                "amount": payment_amount,
                "payment_status": payment_status,
            }
        )

    connection.execute(
        insert(table),
        rows,
    )

    print(
        f"Inserted {len(rows)} payments."
    )


# ---------------------------------------------------------
# Reviews
# ---------------------------------------------------------

def generate_reviews(
    connection,
    tables,
    customer_ids,
    products,
):
    table = tables["analytics.reviews"]

    rows = []

    review_templates = {
        5: [
            "Excellent product. Very satisfied.",
            "Great quality and value for money.",
            "Absolutely loved the product.",
            "Highly recommended.",
        ],
        4: [
            "Very good product.",
            "Good quality and works as expected.",
            "Happy with the purchase.",
        ],
        3: [
            "Average product.",
            "It is okay for the price.",
            "Decent product but could be improved.",
        ],
        2: [
            "Not very satisfied.",
            "Quality could be better.",
            "Expected more from this product.",
        ],
        1: [
            "Very disappointing.",
            "Poor quality.",
            "Would not recommend this product.",
        ],
    }

    for _ in range(NUM_REVIEWS):
        customer_id = random.choice(
            customer_ids
        )

        product = random.choice(products)

        rating = random.choices(
            [1, 2, 3, 4, 5],
            weights=[
                3,
                7,
                15,
                35,
                40,
            ],
            k=1,
        )[0]

        review_date = fake.date_time_between(
            start_date="-2y",
            end_date="now",
        )

        rows.append(
            {
                "customer_id": customer_id,
                "product_id": product[
                    "product_id"
                ],
                "rating": rating,
                "review_text": random.choice(
                    review_templates[rating]
                ),
                "review_date": review_date,
            }
        )

    connection.execute(
        insert(table),
        rows,
    )

    print(
        f"Inserted {len(rows)} reviews."
    )


# ---------------------------------------------------------
# Verification
# ---------------------------------------------------------

def verify_database(connection):
    print("\nDatabase verification")
    print("-" * 40)

    tables = [
        "categories",
        "suppliers",
        "customers",
        "products",
        "orders",
        "order_items",
        "payments",
        "reviews",
    ]

    for table_name in tables:
        result = connection.execute(
            text(
                f"""
                SELECT COUNT(*)
                FROM analytics.{table_name}
                """
            )
        )

        count = result.scalar_one()

        print(
            f"{table_name:<15} {count:>8,} rows"
        )

    print("-" * 40)

    # Foreign-key integrity checks
    checks = {
        "orphan_orders": """
            SELECT COUNT(*)
            FROM analytics.orders o
            LEFT JOIN analytics.customers c
                ON o.customer_id = c.customer_id
            WHERE c.customer_id IS NULL
        """,
        "orphan_order_items": """
            SELECT COUNT(*)
            FROM analytics.order_items oi
            LEFT JOIN analytics.orders o
                ON oi.order_id = o.order_id
            LEFT JOIN analytics.products p
                ON oi.product_id = p.product_id
            WHERE o.order_id IS NULL
               OR p.product_id IS NULL
        """,
        "orphan_payments": """
            SELECT COUNT(*)
            FROM analytics.payments p
            LEFT JOIN analytics.orders o
                ON p.order_id = o.order_id
            WHERE o.order_id IS NULL
        """,
        "orphan_reviews": """
            SELECT COUNT(*)
            FROM analytics.reviews r
            LEFT JOIN analytics.customers c
                ON r.customer_id = c.customer_id
            LEFT JOIN analytics.products p
                ON r.product_id = p.product_id
            WHERE c.customer_id IS NULL
               OR p.product_id IS NULL
        """,
    }

    print("\nIntegrity checks")
    print("-" * 40)

    all_clean = True

    for name, query in checks.items():
        result = connection.execute(
            text(query)
        )

        count = result.scalar_one()

        status = "PASS" if count == 0 else "FAIL"

        if count != 0:
            all_clean = False

        print(
            f"{name:<22} {status}"
        )

    print("-" * 40)

    if all_clean:
        print("All foreign-key integrity checks passed.")
    else:
        print("Some integrity checks failed.")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate synthetic data for Text-to-SQL project."
    )

    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing analytics data before seeding.",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("TEXT-TO-SQL ANALYST - DATABASE SEEDER")
    print("=" * 60)

    print(f"Database: {DB_NAME}")
    print(f"Host:     {DB_HOST}")
    print(f"Port:     {DB_PORT}")
    print(f"Schema:   analytics")
    print()

    metadata = load_tables()

    with engine.begin() as connection:

        if args.reset:
            reset_data(
                connection,
                metadata.tables,
            )

        print("\nGenerating dataset...\n")

        category_map = generate_categories(
            connection,
            metadata.tables,
        )

        supplier_ids = generate_suppliers(
            connection,
            metadata.tables,
        )

        customer_ids = generate_customers(
            connection,
            metadata.tables,
        )

        products = generate_products(
            connection,
            metadata.tables,
            category_map,
            supplier_ids,
        )

        orders = generate_orders(
            connection,
            metadata.tables,
            customer_ids,
            products,
        )

        generate_payments(
            connection,
            metadata.tables,
            orders,
        )

        generate_reviews(
            connection,
            metadata.tables,
            customer_ids,
            products,
        )

        verify_database(connection)

    print("\nDataset generation completed successfully.")
    print("=" * 60)


if __name__ == "__main__":
    main()