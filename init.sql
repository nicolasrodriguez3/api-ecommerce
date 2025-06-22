-- Crear base de datos de desarrollo
CREATE DATABASE ecommerce_dev;

-- Crear base de datos de testing
CREATE DATABASE ecommerce_test;

-- Crear usuario específico para la aplicación (opcional)
CREATE USER ecommerce_user WITH PASSWORD 'ecommerce_pass';

-- Dar permisos al usuario
GRANT ALL PRIVILEGES ON DATABASE ecommerce TO ecommerce_user;
GRANT ALL PRIVILEGES ON DATABASE ecommerce_dev TO ecommerce_user;
GRANT ALL PRIVILEGES ON DATABASE ecommerce_test TO ecommerce_user;