CREATE TABLE usuarios (
    id              SERIAL PRIMARY KEY,
    nome            VARCHAR(255)  NOT NULL,
    cracha          VARCHAR(50)   NOT NULL UNIQUE,
    senha_hash      VARCHAR(255)  NOT NULL,
    email           VARCHAR(255),
    is_active       BOOLEAN NOT NULL,
    is_admin        BOOLEAN NOT NULL,
    password_changed BOOLEAN NOT NULL,
    criado_em       TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em   TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION trigger_set_atualizado_em()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em := CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_usuarios_updated
    BEFORE UPDATE ON usuarios
    FOR EACH ROW
    EXECUTE FUNCTION trigger_set_atualizado_em();
