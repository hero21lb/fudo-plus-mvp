CREATE TABLE IF NOT EXISTS customers (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name TEXT NOT NULL CHECK (length(trim(name)) > 0),
    phone TEXT NOT NULL CHECK (length(trim(phone)) > 0),
    oauth_provider TEXT,
    oauth_subject TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT customers_oauth_pair CHECK (
        (oauth_provider IS NULL AND oauth_subject IS NULL) OR
        (oauth_provider IS NOT NULL AND oauth_subject IS NOT NULL AND
         length(trim(oauth_provider)) > 0 AND length(trim(oauth_subject)) > 0)
    ),
    UNIQUE (oauth_provider, oauth_subject)
);
CREATE TABLE IF NOT EXISTS orders (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id BIGINT REFERENCES customers(id) ON DELETE RESTRICT,
    customer_name TEXT NOT NULL CHECK (length(trim(customer_name)) > 0),
    customer_phone TEXT NOT NULL CHECK (length(trim(customer_phone)) > 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'confirmed', 'preparing', 'ready', 'completed', 'cancelled')),
    fulfillment_method TEXT NOT NULL CHECK (fulfillment_method IN ('pickup', 'delivery')),
    delivery_address TEXT,
    delivery_reference TEXT,
    total_cents BIGINT NOT NULL CHECK (total_cents >= 0),
    payment_method TEXT NOT NULL DEFAULT 'cash'
        CHECK (payment_method IN ('cash', 'online', 'simulated')),
    payment_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (payment_status IN ('pending', 'approved', 'rejected', 'simulated')),
    CONSTRAINT orders_delivery_address CHECK (
        fulfillment_method <> 'delivery' OR
        (delivery_address IS NOT NULL AND length(trim(delivery_address)) > 0)
    ),
    CONSTRAINT orders_simulated_payment CHECK (
        (payment_method = 'simulated' AND payment_status = 'simulated') OR
        (payment_method <> 'simulated' AND payment_status <> 'simulated')
    )
);
CREATE TABLE IF NOT EXISTS order_items (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
    product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE RESTRICT,
    product_name TEXT NOT NULL CHECK (length(trim(product_name)) > 0),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price_cents INTEGER NOT NULL CHECK (unit_price_cents >= 0),
    line_total_cents BIGINT GENERATED ALWAYS AS (quantity::bigint * unit_price_cents) STORED
);
CREATE INDEX IF NOT EXISTS orders_customer_id_idx ON orders(customer_id);
CREATE INDEX IF NOT EXISTS orders_status_created_at_idx ON orders(status, created_at);
CREATE INDEX IF NOT EXISTS order_items_order_id_idx ON order_items(order_id);
CREATE INDEX IF NOT EXISTS order_items_product_id_idx ON order_items(product_id);
