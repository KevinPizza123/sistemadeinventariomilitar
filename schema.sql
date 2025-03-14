CREATE TABLE Vendedores (
    vendedor_id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) UNIQUE NOT NULL,
    contraseña VARCHAR(255) NOT NULL,
    es_admin BOOLEAN NOT NULL DEFAULT FALSE
);

-- Hashea la contraseña "herbye25" y reemplaza el valor aquí
INSERT INTO Vendedores (nombre, contraseña, es_admin) VALUES ('admin', '$2b$12$v5KcP4JbSxAxiqRqHmikqOx7.JRWZj9ohvYW8eH4/M.1cLyz9hUEi', TRUE);

CREATE TABLE Locales (
    local_id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL
);

CREATE TABLE Productos (
    producto_id SERIAL PRIMARY KEY,
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10, 2) NOT NULL
);

CREATE TABLE Inventario (
    inventario_id SERIAL PRIMARY KEY,
    producto_id INT REFERENCES Productos(producto_id),
    local_id INT REFERENCES Locales(local_id),
    cantidad INT NOT NULL
);

CREATE TABLE Vendedores_Locales (
    vendedor_id INT,
    local_id INT,
    PRIMARY KEY (vendedor_id, local_id),
    FOREIGN KEY (vendedor_id) REFERENCES Vendedores(vendedor_id),
    FOREIGN KEY (local_id) REFERENCES Locales(local_id)
);