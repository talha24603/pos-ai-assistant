SCHEMA_CONTEXT = """
Database schema (POS; PostgreSQL via Prisma).

Always generate ONLY SELECT queries.
Always use double quotes for identifiers.

====================================================
TABLES
====================================================

"User"
- "id" (PK)
- "email"
- "name"
- "password"
- "isVerified"
- "otp"
- "otpExpiresAt"
- "provider"
- "createdAt"
- "stripeCustomerId"
- "isSuperAdmin"

"Tenant"
- "id" (PK)
- "name"
- "address"
- "createdAt"
- "description"
- "email"
- "logo"
- "phone"
- "status" (default INACTIVE)
- "stripeCustomerId"
- "stripeSubscriptionId"
- "subscriptionEndDate"
- "subscriptionPlan"
- "subscriptionStatus"
- "website"
- "type"

"TenantUser"
- "id" (PK)
- "role"
- "userId" (FK -> User.id)
- "tenantId" (FK -> Tenant.id)
- "status" (default ACTIVE)

"Product"
- "id" (PK)
- "name"
- "price"
- "stock"
- "imageUrl"
- "description"
- "tenantId" (FK -> Tenant.id)
- "barcode"
- "category"
- "createdAt"

"Customer"
- "id" (PK)
- "name"
- "email"
- "phone"
- "tenantId" (FK -> Tenant.id)
- "createdAt"

"Sale"
- "id" (PK)
- "total"
- "paymentType"
- "createdAt"
- "tenantId" (FK -> Tenant.id)
- "userId" (FK -> User.id; cashier/staff who recorded the sale)
- "customerId" (FK -> Customer.id, nullable)

"SaleItem"
- "id" (PK)
- "saleId" (FK -> Sale.id)
- "productId" (FK -> Product.id)
- "quantity"
- "price" (unit price at time of sale)

====================================================
RELATIONSHIPS (GROUND TRUTH)
====================================================

- TenantUser.userId -> User.id
- TenantUser.tenantId -> Tenant.id
- Product.tenantId -> Tenant.id
- Customer.tenantId -> Tenant.id
- Sale.tenantId -> Tenant.id
- Sale.userId -> User.id
- Sale.customerId -> Customer.id (optional)
- SaleItem.saleId -> Sale.id
- SaleItem.productId -> Product.id

IMPORTANT:
- "User" has NO "tenantId" and NO "role" column.
- Staff/store role lives on "TenantUser"."role", not on "User".
- "tenantId" exists on "Product", "Customer", and "Sale" only.
- "SaleItem" has no "tenantId"; scope sales via "Sale"."tenantId".
- Link users to a tenant only through "TenantUser".

====================================================
JOIN TEMPLATES (USE THESE ONLY)
====================================================

Template A: Sale with line items and products
---------------------------------------------------
FROM "Sale" s
JOIN "SaleItem" si ON si."saleId" = s."id"
JOIN "Product" p ON p."id" = si."productId"

Template B: Sale with customer (optional)
---------------------------------------------------
FROM "Sale" s
LEFT JOIN "Customer" c ON c."id" = s."customerId"

Template C: Sale with cashier (User)
---------------------------------------------------
FROM "Sale" s
JOIN "User" u ON u."id" = s."userId"

Template D: User membership in a tenant
---------------------------------------------------
FROM "User" u
JOIN "TenantUser" tu ON tu."userId" = u."id"
JOIN "Tenant" t ON t."id" = tu."tenantId"

Template E: Tenant catalog (products)
---------------------------------------------------
FROM "Tenant" t
JOIN "Product" p ON p."tenantId" = t."id"

====================================================
BUSINESS RULES
====================================================

- Multi-tenant data: filter "Product", "Customer", and "Sale" by "tenantId" for store-specific questions.
- "paymentType" on Sale is a string (e.g. CASH, CARD — use values from data; do not invent enums unless asked).
- "Sale"."total" is the sale header total; line revenue is si."quantity" * si."price".
- Walk-in sales may have NULL "customerId".
- "TenantUser"."status" is typically ACTIVE for current staff.

====================================================
ANTI-PATTERNS (FORBIDDEN)
====================================================

DO NOT:
- Reference "User"."role" or "User"."tenantId" (columns do not exist)
- Filter tenant scope on "User" alone; use "TenantUser" or tenant-scoped tables
- Join "SaleItem" directly to "Customer" (go through "Sale")
- Join "Product" directly to "Customer" without "Sale" / "SaleItem"
- Use non-existent tables (e.g. EmployeeProfile, job_post, JobApplication)
- Assume "tenantId" on "SaleItem" or "TenantUser" for product/customer/sale filters (use parent Sale or TenantUser as documented)

====================================================
FEW-SHOT EXAMPLES (CRITICAL)
====================================================

Example 1: "Total sales revenue for a tenant"
---------------------------------------------------
SELECT COALESCE(SUM(s."total"), 0) AS revenue
FROM "Sale" s
WHERE s."tenantId" = 'TENANT_ID';

---------------------------------------------------

Example 2: "Top selling products by quantity"
---------------------------------------------------
SELECT p."id", p."name", SUM(si."quantity") AS units_sold
FROM "Sale" s
JOIN "SaleItem" si ON si."saleId" = s."id"
JOIN "Product" p ON p."id" = si."productId"
WHERE s."tenantId" = 'TENANT_ID'
GROUP BY p."id", p."name"
ORDER BY units_sold DESC;

---------------------------------------------------

Example 3: "Low stock products"
---------------------------------------------------
SELECT p."id", p."name", p."stock", p."category"
FROM "Product" p
WHERE p."tenantId" = 'TENANT_ID'
  AND p."stock" < 10
ORDER BY p."stock" ASC;

---------------------------------------------------

Example 4: "Sales by payment type"
---------------------------------------------------
SELECT s."paymentType", COUNT(*) AS sale_count, SUM(s."total") AS revenue
FROM "Sale" s
WHERE s."tenantId" = 'TENANT_ID'
GROUP BY s."paymentType";

---------------------------------------------------

Example 5: "Staff role for a user in a tenant"
---------------------------------------------------
SELECT u."id", u."email", tu."role", tu."status"
FROM "User" u
JOIN "TenantUser" tu ON tu."userId" = u."id"
WHERE tu."tenantId" = 'TENANT_ID';

====================================================
QUERY RULES
====================================================

- PostgreSQL only
- SELECT only (no INSERT/UPDATE/DELETE)
- Always use explicit JOIN templates when relations exist
- Never infer relationships beyond this schema
- For tenant-specific questions, filter "Product", "Customer", and/or "Sale" with "tenantId" = the provided tenant id
"""
